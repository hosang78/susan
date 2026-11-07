import sys, json, glob, re, datetime
base = sys.argv[1]; outdir = sys.argv[2]
sys.path.insert(0, base + '/scripts')
from common import *
from textclean import *
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

BAD = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')
def cl(v):
    if v is None: return ''
    v = BAD.sub('', str(v))
    return v[:32000]

R = load_all(base); S = load_single(base)
by = {}
for r in R:
    if r['CommKorNm']: by.setdefault(r['CommKorNm'], []).append(r)

# ---- main species
C = [l.rstrip('\n').split('\t') for l in open(base + '/cand.tsv', encoding='utf8') if l.strip()]
W = {}
for f in sorted(glob.glob(base + '/write/b*.json')):
    for d in json.load(open(f, encoding='utf8')): W[d['n']] = d
main = []
for p in C:
    rs = by[p[0]]
    if len(p) > 3 and p[3]: rs = [r for r in rs if r['SpcScitfNmShort'] == p[3]]
    main.append((p, rs[0]))
main_ids = {r['SpcTxnId'] for p, r in main}

SKIP_SENT = re.compile(r'https?://|특허|논문|한국전통지식포탈|doi\.org|KTKP|μmol|\b[A-Z][a-z]{2,} [a-z]{3,}\b|[A-Z][a-z]+ et al')
def strip_noise(texts):
    out = []
    for t in texts:
        ss = [s for s in sentences(t) if not SKIP_SENT.search(s)]
        out.append(' '.join(ss))
    return out

def seas_of(m):
    return regions(' '.join(m['NADI']))
def famname(r): return r['FamilyKR'] or r['Family']

# ---------- workbook helpers
HDR = Font(bold=True, color='FFFFFF'); FILL = PatternFill('solid', fgColor='1F4E78')
WRAP = Alignment(wrap_text=True, vertical='top')
def add_sheet(wb, title, cols, rows, widths, freeze='C2', wrap=True):
    ws = wb.create_sheet(title)
    ws.append(cols)
    for c in ws[1]:
        c.font = HDR; c.fill = FILL; c.alignment = Alignment(wrap_text=True, vertical='center')
    for row in rows: ws.append([cl(x) for x in row])
    for i, w in enumerate(widths, 1): ws.column_dimensions[get_column_letter(i)].width = w
    if wrap:
        for row in ws.iter_rows(min_row=2):
            for c in row: c.alignment = WRAP
    ws.freeze_panes = freeze
    ws.auto_filter.ref = ws.dimensions
    return ws

today = '2026-11-07'
# ---------- 주요수산물
rows_main = []
for p, r in main:
    m = merged(r, S); ful, n = fullness(m)
    seas, basis = seas_of(m)
    w = W.get(p[0])
    if w:
        s, g, h, b, u, rr, c = (w['s'], w['g'], w['h'], w['b'], w['u'], w['r'], w['c'])
    else:
        s = f"{famname(r)}에 속하는 {r['_group']}입니다. (원문에 설명이 없어 분류 정보만 제공합니다.)"
        g = h = b = u = rr = ''; c = '원문에 설명 정보 없음'
    alias = p[1] if p[1] and p[1] != p[0] else ''
    if alias and not any('흔한 이름' in x for x in [c]):
        pass
    rows_main.append([r['SpcTxnId'], alias or p[0], p[0], r['SpcScitfNmShort'], r['_group'], p[2], famname(r), ', '.join(seas), basis, s, g, h, b, u, rr, ful, c])
cols_main = ['ID', '흔한 이름', '국명(공식)', '학명', '그룹', '세부 분류', '과', '국내 해역', '해역 근거', '한줄 소개', '생김새', '사는 곳·생태', '산란·번식 시기', '먹는 법·이용', '알아두면 좋은 점', '정보 충실도', '검수 메모']
w_main = [14, 14, 14, 24, 11, 13, 12, 14, 12, 38, 55, 55, 26, 45, 36, 8, 36]

# ---------- 그외종 + 전체목록
scope = [r for r in R if r['_group']]
rows_other = []; rows_all = []
cnt_other = 0
for r in sorted(scope, key=lambda x: (x['_group'], x['CommKorNm'] == '', x['CommKorNm'], x['SpcScitfNmShort'])):
    m = merged(r, S); ful, n = fullness(m)
    seas, basis = seas_of(m)
    has_text = bool(r['CommKorNm'] and any(m[k] for k in ('ABST', 'FORM', 'ECOL', 'UTLZ')))
    where = ''
    if r['SpcTxnId'] in main_ids: where = '주요수산물'
    elif has_text: where = '그외종_설명'
    rows_all.append([r['SpcTxnId'], r['CommKorNm'], r['SpcScitfNmShort'], r['_group'], famname(r), r['OrderKR'] or r['Order'], ', '.join(seas), basis, r['CorrNmTyp'], ful if has_text or r['SpcTxnId'] in main_ids else '', where])
    if where == '그외종_설명':
        seen = []
        ss, dropped = clean_sents(strip_noise(m['ABST'] + m['FORM']), drop_meristic=True, seen=seen)
        desc = limit(gloss(' '.join(ss)), 700)
        es, _ = clean_sents(strip_noise(m['ECOL'] + m['HABI']), drop_meristic=False, seen=seen)
        hab = limit(gloss(' '.join(es)), 400)
        us, _ = clean_sents(strip_noise(m['UTLZ']), drop_meristic=False, seen=seen)
        use = limit(gloss(' '.join(us)), 350)
        note = []
        if dropped: note.append('몸 크기·지느러미 수 등 계측 수치 문장 일부 생략(원문 파일 참고)')
        if len(' '.join(ss)) > 700: note.append('긴 설명은 앞부분만 수록')
        rows_other.append([r['SpcTxnId'], r['CommKorNm'], r['SpcScitfNmShort'], r['_group'], famname(r), ', '.join(seas), basis, desc, hab, use, ful, '; '.join(note)])
cols_other = ['ID', '국명', '학명', '그룹', '과', '국내 해역', '해역 근거', '설명(전문용어 풀이 적용)', '사는 곳·생태', '이용', '정보 충실도', '가공 메모']
w_other = [14, 14, 24, 11, 12, 14, 12, 60, 40, 36, 8, 30]
cols_all = ['ID', '국명', '학명', '그룹', '과', '목', '국내 해역', '해역 근거', '정명/이명', '정보 충실도', '설명 수록 시트']
w_all = [14, 14, 28, 12, 14, 14, 14, 12, 8, 8, 14]

# ---------- 분류기준 / 용어풀이
crit = [
 ['그룹', '어류', '조기어류, 연골어류(상어·홍어·가오리), 먹장어류'],
 ['그룹', '조개류', '이매패강(굴·바지락·꼬막·가리비·홍합 등)'],
 ['그룹', '고둥·전복류', '복족강(전복·소라·고둥·군소 등)'],
 ['그룹', '오징어·문어류', '두족강'],
 ['그룹', '새우·게류', '연갑강(게·새우·갯가재 등)'],
 ['그룹', '해삼·성게류', '해삼강, 성게강'],
 ['그룹', '멍게류', '해초강(우렁쉥이·미더덕 등)'],
 ['그룹', '해조류', '갈조·홍조·녹조류, 김류(김파래강 포함)'],
 ['그룹', '제외', '세균·곰팡이·플랑크톤·새·곤충·민물식물 등은 이 도감 범위에서 제외'],
 ['해역', '전 연안', "국내분포 글에 '전 연안·전 해역·전국·전역' 등이 있을 때"],
 ['해역', '동해·서해·남해·제주', "국내분포 글에 해당 해역 이름(동해, 서해·황해, 남해, 제주·서귀포)이 있을 때. '동, 남해안'처럼 줄여 쓴 표기도 인식"],
 ['해역', '지명으로 추정', '해역 이름이 없고 지명만 있을 때 아래 지명표로 해역을 추정. 전남은 서해·남해 둘 다로 표시, 고성은 앞에 도 이름이 있을 때만 판단'],
]
for sea, ps in PLACE.items():
    crit.append(['지명표', sea, ', '.join(ps)])
crit += [
 ['충실도', '상', '개요·형태·생태·분포·이용 5개 항목 중 4개 이상 있음'],
 ['충실도', '중', '5개 항목 중 2~3개 있음'],
 ['충실도', '하', '5개 항목 중 0~1개 있음'],
 ['가공', '주요수산물 시트', '원문에 있는 내용만 쉬운 말로 풀어 씀. 원문끼리 다르거나 의심스러운 점은 검수 메모에 표시'],
 ['가공', '그외종_설명 시트', '용어풀이 시트의 사전으로 전문용어를 괄호 설명으로 자동 변환. 몸 크기·지느러미 수 같은 계측 문장 일부는 생략(원문 파일에 그대로 있음). 사람이 문장을 다듬은 것이 아님'],
 ['가공', '흔한 이름', '국명과 시장·현장에서 쓰는 이름이 다른 종에만 수동으로 지정. 일반 지식에 기반하므로 검수 필요'],
]
cols_crit = ['구분', '값', '기준']
gl_rows = [[k, v] for k, v in sorted(GLOSS.items(), key=lambda x: x[0])]

# ---------- 안내
wb = Workbook(); ws = wb.active; ws.title = '안내'
info = [
 ['해양수산 도감 데이터'],
 [''],
 ['출처', '국립해양생물자원관 해양생물종정보 서비스(공공데이터포털 data.go.kr)'],
 ['데이터 기준일', today],
 ['범위', f'전체 22,703종 중 수산 관련 8개 그룹 {len(scope):,}종'],
 ['가공', '쉬운 설명·흔한 이름·그룹·해역·충실도는 원문을 바탕으로 가공한 것입니다. 원문은 별도 파일(해양수산도감_원문.xlsx)에 고치지 않고 보관합니다.'],
 ['주의', '효능·약용 정보는 원문에 기재된 내용이며 의학적 효능을 보장하지 않습니다. 금어기·법령 정보는 최신 법령을 확인하세요. 복어류는 독이 있는 부위가 있어 주의가 필요합니다.'],
 [''],
 ['시트', '설명'],
 ['주요수산물', f'시연용 주요 수산물 {len(rows_main)}종. 쉬운 설명을 새로 풀어 쓴 시트(검수 메모에 의심스러운 점 표시)'],
 ['그외종_설명', f'설명이 있는 그 밖의 종 {len(rows_other):,}종. 전문용어를 자동으로 풀어 쓴 시트'],
 ['전체목록', f'수산 관련 전체 {len(rows_all):,}종의 이름·분류·해역·충실도'],
 ['분류기준', '그룹·해역·충실도·가공 규칙, 지명→해역 표'],
 ['용어풀이', f'자동 변환에 쓴 전문용어 사전 {len(gl_rows)}개'],
]
for line in info: ws.append(line)
ws['A1'].font = Font(bold=True, size=14); ws.column_dimensions['A'].width = 16; ws.column_dimensions['B'].width = 110
for row in ws.iter_rows():
    for c in row: c.alignment = WRAP
add_sheet(wb, '주요수산물', cols_main, rows_main, w_main)
add_sheet(wb, '그외종_설명', cols_other, rows_other, w_other)
add_sheet(wb, '전체목록', cols_all, rows_all, w_all, wrap=False)
add_sheet(wb, '분류기준', cols_crit, crit, [12, 24, 110], freeze='A2')
add_sheet(wb, '용어풀이', ['전문용어', '쉬운 설명'], gl_rows, [16, 50], freeze='A2')
out1 = outdir + '/해양수산도감.xlsx'
wb.save(out1)

# ---------- 원문 workbook (write-only for size)
wb2 = Workbook(write_only=True)
ws2 = wb2.create_sheet('안내')
for line in [['해양수산 도감 원문 (수정 없음)'], ['출처', '국립해양생물자원관 해양생물종정보 서비스(공공데이터포털)'], ['기준일', today],
             ['내용', "'목록조회본'은 전체 목록 조회 결과, '단건조회본'은 종별 개별 조회 결과입니다. 같은 종이라도 두 조회본의 내용이 다를 수 있어 다른 경우에만 단건조회본을 함께 싣습니다."],
             ['주의', '엑셀 한 칸의 글자 수 한도(약 32,000자)를 넘는 내용은 잘라서 수록했습니다.']]:
    ws2.append(line)
ws2 = wb2.create_sheet('원문')
keys = ['ABST', 'FORM', 'ECOL', 'HABI', 'NADI', 'INDI', 'UTLZ', 'ACTIVINFO', 'CULTIVINF']
ws2.append(['버전', 'ID', '국명', '학명'] + keys)
n_orig = 0
ids_in = [r for r in scope if r['SpcTxnId'] in main_ids or (r['CommKorNm'] and any(r[k] for k in ('ABST', 'FORM', 'ECOL', 'UTLZ')))]
for r in ids_in:
    ws2.append(['목록조회본', r['SpcTxnId'], r['CommKorNm'], r['SpcScitfNm']] + [cl(r.get(k, '')) for k in keys]); n_orig += 1
    s = S.get(r['SpcTxnId'])
    if s and any(s.get(k, '') != r.get(k, '') for k in keys):
        ws2.append(['단건조회본', r['SpcTxnId'], r['CommKorNm'], r['SpcScitfNm']] + [cl(s.get(k, '')) for k in keys]); n_orig += 1
out2 = outdir + '/해양수산도감_원문.xlsx'
wb2.save(out2)
print(json.dumps({'main': len(rows_main), 'other': len(rows_other), 'all': len(rows_all), 'gloss': len(gl_rows), 'orig_rows': n_orig, 'single_loaded': len(S)}, ensure_ascii=False))
