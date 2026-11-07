import sys,json,glob,re
base=sys.argv[1]; sys.path.insert(0,base+'/scripts')
from common import *
R=load_all(base); S=load_single(base); by={}
for r in R:
    if r['CommKorNm']: by.setdefault(r['CommKorNm'],[]).append(r)
W={}
for f in sorted(glob.glob(base+'/write/b*.json')):
    for d in json.load(open(f,encoding='utf8')): W[d['n']]=d
C=[l.rstrip('\n').split('\t') for l in open(base+'/cand.tsv',encoding='utf8') if l.strip()]
num=re.compile(r'\d+(?:\.\d+)?')
def toks(t): 
    return {x.rstrip('.') for x in num.findall(t.replace(',',''))}
flag=0
for p in C:
    if p[0] not in W: continue
    rs=by[p[0]]
    if len(p)>3 and p[3]: rs=[r for r in rs if r['SpcScitfNmShort']==p[3]]
    r=rs[0]; s=S.get(r['SpcTxnId'],{})
    src=' '.join(r.get(k,'')+' '+s.get(k,'') for k in ALL_FIELDS)
    st=toks(src)
    # allow derived: m<->cm conversions: also add src numbers /100 and *100
    ext=set(st)
    for x in st:
        try:
            v=float(x); ext|={str(int(v/100)) if v/100==int(v/100) else str(v/100), str(int(v*100)) if (v*100)==int(v*100) else ''}
        except: pass
    w=W[p[0]]; txt=' '.join(w[k] for k in ('s','g','h','b','u','r'))
    miss=sorted(x for x in toks(txt) if x not in ext)
    if miss:
        flag+=1; print(p[0],miss)
print('flagged',flag)
