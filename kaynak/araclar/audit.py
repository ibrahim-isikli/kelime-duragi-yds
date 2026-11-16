"""Content checks for example sentences: python3 araclar/audit.py conj prep phr ..."""
import json,re,sys,collections,pathlib
here=pathlib.Path(__file__).resolve().parent.parent
V=json.load(open(here/'veri-uygulama.json',encoding='utf8'));D=V['DATA'];E=V['EXAMPLES']
cats=[c for c in sys.argv[1:] if not c.startswith('--')] or [c for c in D if not c.startswith('g_')]
IRR={'go':'went gone','do':'did done','get':'got gotten','give':'gave given','grow':'grew grown','find':'found','hold':'held','bring':'brought','build':'built','buy':'bought','draw':'drew drawn','eat':'ate eaten','feel':'felt','fight':'fought','see':'saw seen','say':'said','lead':'led','leave':'left','lose':'lost','mean':'meant','pay':'paid','rise':'rose risen','show':'shown','sweep':'swept','swim':'swam swum','tell':'told','think':'thought','win':'won','strike':'struck','spend':'spent','shrink':'shrank shrunk','undertake':'undertook undertaken','foresee':'foresaw foreseen','uphold':'upheld','forego':'forewent foregone','know':'knew known','bury':'buried','deny':'denied','apply':'applied','satisfy':'satisfied','specify':'specified','justify':'justified','magnify':'magnified','modify':'modified','try':'tried','marry':'married','reply':'replied','supply':'supplied','worry':'worried','carry':'carried','study':'studied','fall':'fell fallen','overcome':'overcame','withhold':'withheld','withdraw':'withdrew withdrawn','arise':'arose arisen','bear':'bore borne','forbid':'forbade forbidden','seek':'sought','teach':'taught','catch':'caught','sell':'sold','send':'sent','stand':'stood','take':'took taken','write':'wrote written','begin':'began begun','choose':'chose chosen','drive':'drove driven','fly':'flew flown','hide':'hid hidden','shake':'shook shaken','speak':'spoke spoken','steal':'stole stolen','wear':'wore worn','tear':'tore torn','lay':'laid','lie':'lay lain','meet':'met','run':'ran','sink':'sank sunk','split':'split','spread':'spread','swear':'swore sworn','understand':'understood','withstand':'withstood'}
def lemma_ok(w,b):
    w=w.lower();b=b.lower()
    if ' ' in w:return all(t in b or t[:4] in b for t in w.split())
    if b.startswith(w) or b.startswith(w[:-1]) and len(w)>3:return True
    if w.endswith('y') and b.startswith(w[:-1]+'i'):return True
    if b in IRR.get(w,'').split():return True
    if len(w)>=6 and b.startswith(w[:len(w)-2]):return True
    return False
skipmissing='--sadece-ornekli' in sys.argv
if skipmissing:cats=[c for c in cats if c!='--sadece-ornekli']
flags=[];seen=collections.defaultdict(list);n=0
for c in cats:
    for x in D[c]:
        e=E.get(f"{c}:{x['w']}")
        if not e:
            if not skipmissing:flags.append((x['id'],'örnek yok'))
            continue
        n+=1;b=re.findall(r'\*\*(.+?)\*\*',e['en']);plain=e['en'].replace('**','')
        if len(b)!=1:flags.append((x['id'],f'{len(b)} vurgu'))
        elif c in ('verb','noun','adj','adv','pv') and not lemma_ok(x['w'],b[0]):flags.append((x['id'],f'vurgu "{b[0]}" ≠ "{x["w"]}"'))
        elif c in ('conj','prep','phr') and b[0].lower()!=re.sub(r'\s*(\.\.\.|…)\s*',' ',x['w'].lower()):flags.append((x['id'],f'vurgu "{b[0]}" ≠ "{x["w"]}"'))
        if not re.search(r'[.!?]$',plain):flags.append((x['id'],'EN noktalama'))
        if not (plain[0].isupper() or plain[0].isdigit()):flags.append((x['id'],'EN büyük harf'))
        if not re.search(r'[.!?]$',e['tr']):flags.append((x['id'],'TR noktalama'))
        r=len(e['tr'])/len(plain)
        if r<0.5 or r>2:flags.append((x['id'],f'uzunluk oranı {r:.2f}'))
        if re.search(r'[ğşıİ]',plain):flags.append((x['id'],'EN içinde Türkçe harf'))
        if re.search(r'\b(\w+) \1\b',plain,re.I):flags.append((x['id'],'tekrarlanan kelime'))
        seen[plain.lower()].append(x['id'])
        syn=[s[0].lower() for s in (x.get('s') or e.get('syn') or [])];conf=[z[0].lower() for z in e.get('conf',[])]
        if set(syn)&set(conf):flags.append((x['id'],'eş/karıştırılan çelişkisi '+str(set(syn)&set(conf))))
        if x['w'].lower() in syn:flags.append((x['id'],'eş anlamlıda kendisi'))
for k,v in seen.items():
    if len(v)>1:flags.append((v,'aynı cümle'))
print(f'{n} örnek kontrol edildi, {len(flags)} işaret');[print(' ',f) for f in flags]
