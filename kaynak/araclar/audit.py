"""Content checks for example sentences: python3 araclar/audit.py conj prep phr ..."""
import json,re,sys,collections,pathlib
here=pathlib.Path(__file__).resolve().parent.parent
V=json.load(open(here/'veri-uygulama.json',encoding='utf8'));D=V['DATA'];E=V['EXAMPLES']
cats=sys.argv[1:] or [c for c in D if not c.startswith('g_')]
flags=[];seen=collections.defaultdict(list);n=0
for c in cats:
    for x in D[c]:
        e=E.get(f"{c}:{x['w']}")
        if not e:flags.append((x['id'],'örnek yok'));continue
        n+=1;b=re.findall(r'\*\*(.+?)\*\*',e['en']);plain=e['en'].replace('**','')
        if len(b)!=1:flags.append((x['id'],f'{len(b)} vurgu'))
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
        if x['w'].lower() in conf:flags.append((x['id'],'karıştırılanda kendisi'))
        if x['w'].lower() in syn:flags.append((x['id'],'eş anlamlıda kendisi'))
for k,v in seen.items():
    if len(v)>1:flags.append((v,'aynı cümle'))
print(f'{n} örnek kontrol edildi, {len(flags)} işaret');[print(' ',f) for f in flags]
