"""Walk the content stream: every text-showing op -> (x, y, size, fontkind, text) with correct decoding."""
import pypdf,decode
from pypdf.generic import ContentStream
def mul(a,b):
    return [a[0]*b[0]+a[1]*b[2],a[0]*b[1]+a[1]*b[3],a[2]*b[0]+a[3]*b[2],a[2]*b[1]+a[3]*b[3],a[4]*b[0]+a[5]*b[2]+b[4],a[4]*b[1]+a[5]*b[3]+b[5]]
WIN={}
def simple_decode(fobj,bs):
    sm=decode.simplemap(fobj)
    if sm:return ''.join(bytes([b]).decode('cp1252',errors='replace') if 32<=b<127 else sm.get(b,bytes([b]).decode('cp1252',errors='replace')) for b in bs)
    enc=fobj.get('/Encoding');diff={}
    if enc is not None:
        e=enc.get_object()
        if isinstance(e,dict) and '/Differences' in e:
            code=None
            for it in e['/Differences']:
                if isinstance(it,int):code=it
                else:diff[code]=str(it);code+=1
    GL={'/Idotaccent':'İ','/Scedilla':'Ş','/scedilla':'ş','/Gbreve':'Ğ','/gbreve':'ğ','/dotlessi':'ı','/space':' '}
    out=''
    for b in bs:
        if b in diff:out+=GL.get(diff[b],'�')
        else:out+=bytes([b]).decode('cp1252',errors='replace')
    return out
def page_runs(reader,page):
    fonts=page['/Resources'].get('/Font',{});cs=ContentStream(page.get_contents(),reader)
    ctm=[1,0,0,1,0,0];stack=[];tm=lm=[1,0,0,1,0,0];font=None;size=0;fkey=None;runs=[];lead=0
    for ops,op in cs.operations:
        if op==b'q':stack.append(ctm[:])
        elif op==b'Q':ctm=stack.pop() if stack else ctm
        elif op==b'cm':ctm=mul([float(x) for x in ops],ctm)
        elif op==b'BT':tm=lm=[1,0,0,1,0,0]
        elif op==b'Tf':fkey=ops[0];font=fonts[fkey].get_object();size=float(ops[1])
        elif op==b'TL':lead=float(ops[0])
        elif op==b'Tm':tm=lm=[float(x) for x in ops]
        elif op in (b'Td',b'TD'):
            lm=mul([1,0,0,1,float(ops[0]),float(ops[1])],lm);tm=lm
            if op==b'TD':lead=-float(ops[1])
        elif op==b'T*':lm=mul([1,0,0,1,0,-lead],lm);tm=lm
        elif op in (b'Tj',b'TJ',b"'",b'"'):
            if op in (b"'",b'"'):lm=mul([1,0,0,1,0,-lead],lm);tm=lm
            arr=ops[0] if op==b'TJ' else [ops[-1]]
            txt=''
            for it in arr:
                if isinstance(it,(bytes,pypdf.generic.ByteStringObject,pypdf.generic.TextStringObject)):
                    bs=it if isinstance(it,bytes) else (it.original_bytes if hasattr(it,'original_bytes') else bytes(it,'latin-1'))
                    if font.get('/Subtype')=='/Type0':
                        m=decode.fontmap(font) or {}
                        txt+=''.join(m.get((bs[i]<<8)|bs[i+1],'�') for i in range(0,len(bs)-1,2))
                    else:txt+=simple_decode(font,bs)
                else:
                    try:
                        if float(it)<-250:txt+=' '
                    except Exception:pass
            m=mul(tm,ctm);base=str(font.get('/BaseFont'))
            runs.append((round(m[4],1),round(m[5],1),round(size*abs(m[0]) if m[0] else size*abs(m[1]),1),'B' if 'Bold' in base else 'R',txt))
            # advance is not needed: each run is positioned independently
    return runs
if __name__=='__main__':
    import sys;r=pypdf.PdfReader(sys.argv[1]);p=int(sys.argv[2])
    for x in page_runs(r,r.pages[p])[:int(sys.argv[3]) if len(sys.argv)>3 else 40]:print(x)
