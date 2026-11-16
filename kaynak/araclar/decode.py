"""Decode the YDS PDFs: Type0 fonts without ToUnicode -> identify each glyph by matching its outline
(contour count + y coordinates; condensing only scales x) against the system DejaVu Sans fonts."""
import io,sys,json,warnings,logging,hashlib
logging.disable(logging.WARNING);warnings.filterwarnings('ignore')
import pypdf
from fontTools.ttLib import TTFont
REF={'bold':TTFont('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),'reg':TTFont('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')}
CHARS=''.join(chr(c) for c in range(32,127))+'çğıöşüÇĞİÖŞÜâîûÂÎÛ’‘“”–—…•·→«»'
def sig(tt,gname,loose=False):
    g=tt['glyf'][gname]
    if g.isComposite():
        g=g  # expand composite to flat coordinates
        coords,ends,_=g.getCoordinates(tt['glyf'])
    else:
        if g.numberOfContours<=0:return ('empty',)
        coords,ends,_=g.getCoordinates(tt['glyf'])
    if loose:return (len(ends),tuple(sorted(y for x,y in coords)))
    xs=[x for x,y in coords];xmin=min(xs);w=(max(xs)-xmin) or 1
    # x is condensed by a constant factor, y is unchanged: order-preserving y + coarse normalized x
    return (len(ends),tuple(y for x,y in coords),tuple(round(4*(x-xmin)/w) for x,y in coords))
REFSIG={};REFLOOSE={}
for k,tt in REF.items():
    cmap=tt.getBestCmap();d={};l={}
    for ch in CHARS:
        gn=cmap.get(ord(ch))
        if gn: d.setdefault(sig(tt,gn),ch);l.setdefault(sig(tt,gn,True),ch)
    REFSIG[k]=d;REFLOOSE[k]=l
_cache={}
def _fkey(fobj):
    """stable cache key: the embedded font program itself (id() of pypdf objects gets reused)"""
    try:
        if fobj.get('/Subtype')=='/Type0':fd=fobj['/DescendantFonts'][0].get_object()['/FontDescriptor'].get_object()
        else:fd=fobj['/FontDescriptor'].get_object()
        ff=fd.get('/FontFile2') or fd.get('/FontFile3') or fd.get('/FontFile')
        return str(fobj.get('/BaseFont'))+hashlib.md5(ff.get_object().get_data()).hexdigest()
    except Exception:return 'nofile:'+str(fobj.get('/BaseFont'))+str(fobj.get('/Subtype'))
def fontmap(fobj):
    key=_fkey(fobj)
    if key in _cache:return _cache[key]
    m=None
    if fobj.get('/Subtype')=='/Type0':
        df=fobj['/DescendantFonts'][0].get_object();fd=df['/FontDescriptor'].get_object()
        ff=fd.get('/FontFile2')
        base=str(fobj.get('/BaseFont'))
        kind='bold' if 'Bold' in base else 'reg'
        if ff is not None:
            tt=TTFont(io.BytesIO(ff.get_object().get_data()));order=tt.getGlyphOrder();m={}
            miss=[]
            for gid,gn in enumerate(order):
                if gid==0:continue
                s=sig(tt,gn);ch=REFSIG[kind].get(s)
                if ch is None and s!=('empty',):ch=REFLOOSE[kind].get(sig(tt,gn,True))
                if ch is None and s==('empty',):ch=' '
                if ch is None:miss.append(gid);ch='�'
                m[gid]=ch
            m['_miss']=miss
    _cache[key]=m;return m
def page_items(page):
    """returns list of (x,y,text) with decoded text"""
    out=[];fonts=page['/Resources']['/Font']
    def vis(text,cm,tm,fdict,fsize):
        if not text or fdict is None:return
        m=fontmap(fdict)
        if m: text=''.join(m.get(ord(c),c) if c not in '\n' else c for c in text)
        x=tm[4]*cm[0]+cm[4];y=tm[5]*cm[3]+cm[5]
        out.append((round(x,1),round(y,1),text))
    page.extract_text(visitor_text=vis)
    return out
if __name__=='__main__':
    r=pypdf.PdfReader(sys.argv[1]);pg=int(sys.argv[2]) if len(sys.argv)>2 else 2
    for it in page_items(r.pages[pg])[:60]:print(it)
    for k,v in _cache.items():
        if v:print('missing glyphs:',v['_miss'])

_scache={}
def simplemap(fobj):
    """simple TrueType DejaVu font: byte -> glyph (via its own cmap) -> char (via outline match)"""
    key=_fkey(fobj)
    if key in _scache:return _scache[key]
    m=None;base=str(fobj.get('/BaseFont'))
    fd=fobj.get('/FontDescriptor')
    if 'DejaVu' in base and fd is not None:
        ff=fd.get_object().get('/FontFile2')
        if ff is not None:
            tt=TTFont(io.BytesIO(ff.get_object().get_data()));kind='bold' if 'Bold' in base else 'reg';m={}
            cm={}
            for t in tt['cmap'].tables:
                try:cm.update(t.cmap)
                except Exception:pass
            for code,gn in cm.items():
                b=code&0xFF
                s=sig(tt,gn);ch=REFSIG[kind].get(s)
                if ch is None and s!=('empty',):ch=REFLOOSE[kind].get(sig(tt,gn,True))
                if ch is None and s==('empty',):ch=' '
                if ch is not None:m[b]=ch
    _scache[key]=m;return m
