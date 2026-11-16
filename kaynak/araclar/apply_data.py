"""Writes veri-uygulama.json into kelime-duragi-yds.html (const DATA / const EXAMPLES lines). Re-runnable."""
import json,pathlib
here=pathlib.Path(__file__).resolve().parent.parent;p=here/'kelime-duragi-yds.html'
V=json.load(open(here/'veri-uygulama.json',encoding='utf8'));L=p.read_text(encoding='utf8').split('\n')
i=next(k for k,l in enumerate(L) if l.startswith('const DATA = '));L[i]='const DATA = '+json.dumps(V['DATA'],ensure_ascii=False,separators=(',',':'))+';'
j=next(k for k,l in enumerate(L) if l.startswith('const EXAMPLES='));L[j]='const EXAMPLES='+json.dumps(V['EXAMPLES'],ensure_ascii=False,separators=(',',':'))+';'
p.write_text('\n'.join(L),encoding='utf8');print('ok',len(V['EXAMPLES']),'örnek')
