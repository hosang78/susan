import json,sys
R=json.load(open(sys.argv[1])); by={}
for r in R:
    if r['CommKorNm']: by.setdefault(r['CommKorNm'],[]).append(r)
miss=[];dups=[]
for l in open(sys.argv[2],encoding='utf8'):
    p=l.rstrip('\n').split('\t')
    if len(p)<3: continue
    o=p[0]
    if o not in by: miss.append(o); continue
    if len(by[o])>1: dups.append((o,len(by[o])))
print('후보',sum(1 for _ in open(sys.argv[2])),'없음',miss); print('중복이름',dups)
