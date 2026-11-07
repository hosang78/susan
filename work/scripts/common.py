import json,re,os,glob,xml.etree.ElementTree as ET
GROUP={'Teleostei':'어류','Elasmobranchii':'어류','Holocephali':'어류','Actinopterygii':'어류','Myxini':'어류','Petromyzonti':'어류','Bivalvia':'조개류','Gastropoda':'고둥·전복류','Cephalopoda':'오징어·문어류','Malacostraca':'새우·게류','Holothuroidea':'해삼·성게류','Echinoidea':'해삼·성게류','Ascidiacea':'멍게류','Phaeophyceae':'해조류','Florideophyceae':'해조류','Bangiophyceae':'해조류','Ulvophyceae':'해조류','Compsopogonophyceae':'해조류','Stylonematophyceae':'해조류'}
ALL_FIELDS=['ABST','FORM','ECOL','CULTIVINF','BIOCHEMICAL','ACTIVINFO','NADI','INDI','HABI','UTLZ']
ALLRE=['전 연안','전연안','전 해역','전해역','전 해안','전해안','전국','전역','우리나라 전','한국 전','국내 전','전체 해역','우리나라 연안','한국 연안','우리나라 전체','전 지역','해역 전체']
SEA_WORDS=[('동해',['동해']),('서해',['서해','황해']),('남해',['남해']),('제주',['제주','서귀포'])]
PLACE={
'동해':'속초 양양 강릉 주문진 삼척 동해시 울진 영덕 포항 구룡포 영일만 경주 월성 감포 죽변 후포 울릉 독도 울산 강원 경북 경상북도 안인 대진 묵호 장호 강원도 고성 강원 고성'.split(' '),
'서해':'인천 강화 덕적 굴업 백령 대청 소청 연평 소연평 소야 안산 대부 태안 안면 만리포 천리포 파도리 서산 보령 대천 서천 군산 부안 변산 채석강 고창 영광 무안 신안 목포 진도 흑산 홍도 가거도 소흑산 대흑산 우이도 안마 외연도 어청 격렬비 금갑 하조도 경기만 경기 충남 충청남도 전북 전라북도 아산 시화 당진 함평 서해안'.split(' '),
'남해':'부산 해운대 동백섬 거제 통영 사천 삼천포 마산 창원 진해 남해군 남해도 욕지 비진 여수 돌산 광양 순천 고흥 보성 장흥 강진 완도 청산도 소안 보길 거문도 백도 다도해 경남 경상남도 대한해협 대한 해협 여서도 한산도 사량 기장 고리 송정 가덕'.split(' '),
'제주':'제주 서귀포 우도 마라도 가파도 추자 비양도 범섬 문섬 섶섬 섭섬 차귀도 성산 종달 한림 고산 화북 신창 법환 화순 사계 강정 김녕 함덕 세화 행원 애월 대포 모슬포 무릉 귀덕 조천 지귀도 관탈도 형제섬 직구도 예초리 신양리 신양'.split(' '),
}
BOTH_JN=['전남','전라남도']
def regions(t):
    """returns (seas list, basis) ; basis in ('원문 해역 표기','지명으로 추정','전 연안','')"""
    if not t: return [],''
    s=set(); explicit=False
    for k,ws in SEA_WORDS:
        if any(w in t for w in ws): s.add(k); explicit=True
    for m in re.finditer(r'([동서남])\s*[,·、]\s*(?=[동서남]해)',t):
        s.add({'동':'동해','서':'서해','남':'남해'}[m.group(1)]); explicit=True
    if any(w in t for w in ALLRE) and not s: return ['전 연안'],'전 연안'
    if any(w in t for w in ALLRE): s.add('전 연안')
    if explicit: 
        return [x for x in ['전 연안','동해','서해','남해','제주'] if x in s],'원문 해역 표기'
    # place names
    t2=re.sub(r'(경남|경상남도)\s*고성','경남고성',t)
    for k,ps in PLACE.items():
        for p in ps:
            if p in t2.replace('경남고성','경남고성'): 
                if p=='고성': continue
                s.add(k)
    if '경남고성' in t2: s.add('남해')
    if any(b in t for b in BOTH_JN): s.update(['서해','남해'])
    if s: return [x for x in ['전 연안','동해','서해','남해','제주'] if x in s],'지명으로 추정'
    return [],''
def load_all(base):
    R=json.load(open(base+'/all.json'))
    for r in R: r['_group']=GROUP.get(r['Class'],'')
    return R
def load_single(base):
    S={}
    for f in glob.glob(base+'/single/*.xml'):
        try:
            it=next(ET.parse(f).getroot().iter('item'))
        except Exception: continue
        d={c.tag:(c.text or '').strip() for c in it}
        if d.get('SpcTxnId'): S[d['SpcTxnId']]=d
    return S
def merged(r,S):
    """field-wise: list of distinct versions (bulk first)"""
    s=S.get(r['SpcTxnId'],{}); out={}
    for k in ALL_FIELDS:
        v=[x for x in [r.get(k,''),s.get(k,'')] if x]
        if len(v)==2 and (v[0]==v[1] or v[1] in v[0]): v=[v[0]]
        elif len(v)==2 and v[0] in v[1]: v=[v[1]]
        out[k]=v
    return out
def fullness(m):
    core=['ABST','FORM','ECOL','NADI','UTLZ']
    n=sum(1 for k in core if m[k]);
    return ('상' if n>=4 else '중' if n>=2 else '하'),n
