import glob,json,re,pypdf,runs,collections
FILES={'004':'verb','005':'pv','006':'conj','007':'noun','008':'prep','009':'phr','010':'adj','011':'adv'}
SUB={'Diğer Yapıları':'der','Eş Anlamlılar':'syn','Zıt Anlamlılar':'ant'}
def parse(path):
    r=pypdf.PdfReader(path);entries=[];issues=[]
    for pi,pg in enumerate(r.pages):
        rr=runs.page_runs(r,pg)
        hy=max([y for x,y,s,k,t in rr if t.strip()=='İngilizce'],default=None)
        hs=max([s for x,y,s,k,t in rr if t.strip()=='İngilizce'],default=7.5);BIG=hs*1.05  # main rows are a bit larger than the header
        hx=sorted({x for x,y,s,k,t in rr if t.strip()=='İngilizce'})
        if not hx:continue
        tables=[]
        for h in hx:
            tr=[x for x,y,s,k,t in rr if t.strip()=='Türkçe' and x>h][0];tu=[x for x,y,s,k,t in rr if t.strip()=='Tür' and x>tr][0]
            tables.append((h,tr,tu))
        def which(x):
            ti=0
            for i,(h,tr,tu) in enumerate(tables):
                if x>=h-30:ti=i
            h,tr,tu=tables[ti]
            col='num' if x<h-2 else 'en' if x<tr-2 else 'tr' if x<tu-2 else 'pos'
            return ti,col
        rows=collections.OrderedDict()
        for x,y,s,k,t in rr:
            if y>=hy-1 or y<52 or not t.strip() or re.search(r'www\.|\.com\b',t):continue
            ti,col=which(x);key=(ti,round(y))
            rows.setdefault(key,{'size':s,'cells':collections.defaultdict(str)})
            rows[key]['cells'][col]+=t
        order=sorted(rows,key=lambda k:(k[0],-k[1]))
        # a cell that wraps puts its first line ABOVE the row's other cells: merge tr/en-only rows into the
        # nearest row of the same size within 12pt (prefer the row below when it is a numbered main row)
        merged=[]
        for key in order:
            row=rows[key];c={k:v.strip() for k,v in row['cells'].items() if v.strip()}
            merged.append([key,row['size'],c])
        i=0
        while i<len(merged):
            (ti,y),sz,c=merged[i]
            if c and not c.get('num') and not c.get('pos') and set(c)<= {'tr','en'} and c.get('en','') not in SUB:
                nxt=merged[i+1] if i+1<len(merged) else None;prv=merged[i-1] if i>0 else None
                def ok(o):return o and o[0][0]==ti and abs(o[0][1]-y)<=12 and abs(o[1]-sz)<0.6 and (o[2].get('pos') or o[2].get('num'))
                if ok(nxt) and (not ok(prv) or abs(nxt[0][1]-y)<=abs(prv[0][1]-y) or nxt[2].get('num')) and y>nxt[0][1]:
                    for k,v in c.items():nxt[2][k]=(v+' '+nxt[2].get(k,'')).strip()
                    merged.pop(i);continue
                if ok(prv):
                    for k,v in c.items():prv[2][k]=(prv[2].get(k,'')+' '+v).strip()
                    merged.pop(i);continue
            i+=1
        for (ti,y),size,c in merged:
            big=size>=BIG
            if big and re.fullmatch(r'\d+\.',c.get('num','')):
                entries.append({'n':int(c['num'][:-1]),'w':c.get('en',''),'m':c.get('tr',''),'pos':c.get('pos',''),'page':pi+1,'der':[],'syn':[],'ant':[]});mode=None;continue
            if not entries:continue
            e=entries[-1]
            if c.get('en','') in SUB and not c.get('tr'):mode=SUB[c['en']];continue
            if big:  # wrapped main row
                for k in ('en','tr','pos'):
                    if c.get(k):e[{'en':'w','tr':'m','pos':'pos'}[k]]+=' '+c[k]
                continue
            if mode and c.get('en'):e[mode].append([c['en'],c.get('tr',''),c.get('pos','')])
            elif mode and c.get('tr') and e[mode]:e[mode][-1][1]+=' '+c['tr']
            elif c:issues.append((pi+1,c))
    for e in entries:
        e['pos']=re.sub(r'\s*\d+(\s+\d+)*$','',e['pos']).strip()
        for k in ('w','m'):e[k]=re.sub(r'\s+',' ',e[k]).strip()
        for lst in (e['der'],e['syn'],e['ant']):
            for z in lst:z[1]=re.sub(r'\s+',' ',z[1]).strip();z[2]=re.sub(r'\s*\d+$','',z[2]).strip()
    return entries,issues
out={}
for f in sorted(glob.glob('/root/.claude/uploads/ff6127c4-78c4-5a60-896e-74611f7582b5/*YDS*.pdf')):
    code=f.split('/')[-1].split('-',1)[1][:3];cat=FILES[code];es,iss=parse(f)
    nums=[e['n'] for e in es];gaps=[n for n in range(1,max(nums)+1) if n not in set(nums)];dup=[n for n,c in collections.Counter(nums).items() if c>1]
    bad=[e for e in es if '�' in json.dumps(e,ensure_ascii=False) or not e['w'] or not e['m']]
    print(f"{cat:5} {len(es):4} kelime  numara 1..{max(nums)} eksik={gaps[:8]} tekrar={dup[:5]}  sorunlu={len(bad)} türler={dict(collections.Counter(e['pos'] for e in es))} ek={sum(len(e['der']) for e in es)} türev, {sum(len(e['syn']) for e in es)} eş, {sum(len(e['ant']) for e in es)} zıt; sınıflanmamış satır={len(iss)}")
    for b in bad[:3]:print('   SORUN',b)
    for i in iss[:3]:print('   SATIR',i)
    out[cat]=es
json.dump(out,open('../yds/parsed.json','w'),ensure_ascii=False,indent=0)
