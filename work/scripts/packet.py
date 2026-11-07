import sys,json; sys.path.insert(0,sys.argv[1]+'/scripts')
from common import *; from textclean import *
base=sys.argv[1]; a=int(sys.argv[2]); b=int(sys.argv[3])
R=load_all(base); S=load_single(base); by={}
for r in R:
    if r['CommKorNm']: by.setdefault(r['CommKorNm'],[]).append(r)
C=[l.rstrip('\n').split('\t') for l in open(base+'/cand.tsv',encoding='utf8') if l.strip()]
def rec(p):
    rs=by[p[0]]
    if p[3]: rs=[r for r in rs if r['SpcScitfNmShort']==p[3]]
    return rs[0]
GROUPS=[(['ABST','FORM'],'생김새·개요',380,True),(['ECOL','HABI'],'생태·서식',300,False),(['NADI'],'분포',140,False),(['UTLZ'],'이용',320,False),(['ACTIVINFO','CULTIVINF'],'효능·양식',200,False)]
for i,p in enumerate(C[a:b],a):
    r=rec(p); m=merged(r,S); ful,n=fullness(m)
    print(f"#{i} {p[0]} (흔한이름:{p[1] or '-'} | {p[2]} | {r['SpcScitfNmShort']} | {r['_group']} | {r['FamilyKR']} | 충실도 {ful}{n} | 단건:{'Y' if r['SpcTxnId'] in S else 'N'})")
    seen=[]
    for ks,lab,cap,mer in GROUPS:
        texts=[x for k in ks for x in m[k]]
        if not texts: continue
        ss,dr=clean_sents(texts,drop_meristic=mer,seen=seen)
        t=limit(' '.join(ss),cap)
        if t: print(f"  [{lab}] {t}")
