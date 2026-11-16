"""Builds DATA + EXAMPLES for the YDS edition from veri-pdf.json (+ YÖKDİL grammar data and reusable examples)."""
import json,re,pathlib,sys,collections
here=pathlib.Path(__file__).resolve().parent.parent
P=json.load(open(here/'veri-pdf.json',encoding='utf8'))
yok=pathlib.Path(sys.argv[1]).read_text(encoding='utf8').split('\n')   # YÖKDİL app html: grammar data + reusable examples
YD=json.loads(next(l for l in yok if l.startswith('const DATA = '))[len('const DATA = '):].rstrip(';'))
YE=json.loads(next(l for l in yok if l.startswith('const EXAMPLES='))[len('const EXAMPLES='):].rstrip(';'))
POS={'fiil':'Fiil','isim':'İsim','sıfat':'Sıfat','zarf':'Zarf','bağlaç':'Bağlaç','p. verb':'P. Verb','p. phrase':'P. Phrase','preposition':'Preposition','determiner':'Determiner'}
def npos(p):p=re.sub(r'\s+',' ',p.strip());return POS.get(p.lower().replace('İ','i').replace('I','ı'),POS.get(p.lower(),p))
def slug(w):return re.sub(r'[^a-z0-9]+','-',w.lower().replace('’',"'")).strip('-')
ORDER=['verb','noun','adj','adv','pv','conj','prep','phr']
# clear typos in the source lists; ids are NOT changed (saved progress stays attached)
FIX={'prep:nothward':{'w':'northward'},
     'conj:suppose-that':{'m':'varsay ki'},
     'conj:while':{'m':'-e rağmen, -iken, oysa'},
     'conj:as':{'m':'-dığı için, çünkü, -dıkça, -iken, gibi'},
     'conj:since':{'m':'-dığı için, çünkü, -den beri'},
     'prep:into':{'m':'-e, -a (içine doğru)'},
     'prep:near':{'m':'yakın, yakında'},
     'prep:regarding':{'m':'ile ilgili'},
     'phr:the-number-of':{'m':'-ın sayısı'},
     'phr:as-well':{'m':'-de, -da'},
     'phr:as-to':{'m':'-e dair, ile ilgili'},
     'phr:with-reference-to':{'m':'ile ilgili'},
     'phr:with-exception-of':{'w':'with the exception of'},
     'phr:as-of':{'m':'-den itibaren'},
     'verb:correspond':{'m':'benzemek, haberleşmek'},
     'noun:business':{'m':'iş, iş yeri'},
     'noun:government':{'m':'hükümet, yönetim'},
     'noun:title':{'m':'başlık, unvan'},
     'noun:negligence':{'m':'ihmalkârlık, ihmal'},
     'noun:discretion':{'m':'akıl, sağduyu'},
     'noun:common-sense':{'m':'sağduyu'},
     'noun:instinct':{'m':'içgüdü'},
     'noun:remain':{'w':'remains','m':'kalıntı'}}
# entries that are wrong in the source and are left out (decided by the owner)
DROP={'prep:wayward'}   # source: "yola doğru"; wayward is an adjective meaning "dik başlı, asi", not a preposition
def load_tsv():
    out={}
    for f in sorted((here/'icerik').glob('*.tsv')):
        for n,l in enumerate(open(f,encoding='utf8'),1):
            l=l.rstrip('\n')
            if not l.strip():continue
            c=l.split('\t')+['']*5;iid,en,tr,syn,conf=c[:5]
            assert '**' in en and tr.strip(),(f.name,n,l[:60])
            e={'en':en.strip(),'tr':tr.strip()}
            if syn.strip():e['syn']=[[q.strip() for q in z.split('=',1)] for z in syn.split(';') if z.strip()]
            if conf.strip():e['conf']=[[q.strip() for q in (z.split('=',2)+['',''])[:3]] for z in conf.split(';') if z.strip()]
            assert iid not in out,iid;out[iid]=e
    return out
TSV=load_tsv()
DATA={};EX={};stats=collections.Counter()
for c in ORDER:
    seen=collections.Counter();out=[]
    for e in P[c]:
        w=re.sub(r'\s+',' ',e['w']).strip();s=slug(w);seen[s]+=1;sid=s if seen[s]==1 else f'{s}-{seen[s]}'
        it={'id':f'{c}:{sid}','w':w,'m':e['m']}
        it.update(FIX.get(it['id'],{}));w=it['w']
        if it['id'] in DROP:stats['çıkarıldı']+=1;continue
        if e['syn']:it['s']=[[z[0],z[1],npos(z[2])] for z in e['syn']]
        if e['der']:it['d']=[[z[0],z[1],npos(z[2])] for z in e['der']]
        out.append(it);stats['kelime']+=1;stats['eş(kaynak)']+=len(e['syn']);stats['türev']+=len(e['der'])
        # reuse a reviewed YÖKDİL example only for the same word in the same word class
        for yx in YD.get(c,[]) if c in ('verb','noun','adj','adv','pv') else []:
            if yx['w'].lower()==w.lower() and (c+':'+yx['w']) in YE:
                EX[f'{c}:{w}']=YE[c+':'+yx['w']];stats['örnek']+=1;break
        if it['id'] in TSV:EX[f"{c}:{w}"]=TSV[it['id']];stats['yeni örnek']+=1
        ex=EX.get(f"{c}:{w}")
        if ex and it.get('s') and ex.get('conf'):   # a source synonym is never also listed as confusable
            sw={z[0].lower() for z in it['s']};kept=[z for z in ex['conf'] if z[0].lower() not in sw]
            if len(kept)!=len(ex['conf']):
                ex=dict(ex);stats['çelişki ayıklandı']+=1
                if kept:ex['conf']=kept
                else:ex.pop('conf')
                EX[f"{c}:{w}"]=ex
    DATA[c]=out
for c in ('trans','conj','phr','corr','other'):   # grammar-only data (Gramer screens), kept as in the YÖKDİL edition
    DATA['g_'+c]=[dict(x,id='g_'+x['id']) for x in YD[c]];stats['gramer']+=len(YD[c])
ids=[x['id'] for a in DATA.values() for x in a];assert len(ids)==len(set(ids))
unknown=set(TSV)-set(ids);assert not unknown,unknown
json.dump({'DATA':DATA,'EXAMPLES':EX},open(here/'veri-uygulama.json','w',encoding='utf8'),ensure_ascii=False,separators=(',',':'))
print(dict(stats))
