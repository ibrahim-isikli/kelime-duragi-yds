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
DATA={};EX={};stats=collections.Counter()
for c in ORDER:
    seen=collections.Counter();out=[]
    for e in P[c]:
        w=re.sub(r'\s+',' ',e['w']).strip();s=slug(w);seen[s]+=1;sid=s if seen[s]==1 else f'{s}-{seen[s]}'
        it={'id':f'{c}:{sid}','w':w,'m':e['m']}
        if e['syn']:it['s']=[[z[0],z[1],npos(z[2])] for z in e['syn']]
        if e['der']:it['d']=[[z[0],z[1],npos(z[2])] for z in e['der']]
        out.append(it);stats['kelime']+=1;stats['eş(kaynak)']+=len(e['syn']);stats['türev']+=len(e['der'])
        # reuse a reviewed YÖKDİL example only for the same word in the same word class
        for yx in YD.get(c,[]) if c in ('verb','noun','adj','adv','pv') else []:
            if yx['w'].lower()==w.lower() and (c+':'+yx['w']) in YE:
                EX[f'{c}:{w}']=YE[c+':'+yx['w']];stats['örnek']+=1;break
    DATA[c]=out
for c in ('trans','conj','phr','corr','other'):   # grammar-only data (Gramer screens), kept as in the YÖKDİL edition
    DATA['g_'+c]=[dict(x,id='g_'+x['id']) for x in YD[c]];stats['gramer']+=len(YD[c])
ids=[x['id'] for a in DATA.values() for x in a];assert len(ids)==len(set(ids))
json.dump({'DATA':DATA,'EXAMPLES':EX},open(here/'veri-uygulama.json','w',encoding='utf8'),ensure_ascii=False,separators=(',',':'))
print(dict(stats))
