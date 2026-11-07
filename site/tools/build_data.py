"""output/ 폴더의 엑셀에서 앱 데이터(site/data/*.json)를 만듭니다.
실행: python3 site/tools/build_data.py  (저장소 최상위에서)"""
import json, csv, os
from openpyxl import load_workbook

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'site', 'data')
GROUP_ORDER = ['어류', '오징어·문어류', '새우·게류', '조개류', '고둥·전복류', '해삼·성게류', '멍게류', '해조류']

wb = load_workbook(os.path.join(ROOT, 'output', '해양수산도감.xlsx'), read_only=True)
rows = list(wb['주요수산물'].iter_rows(values_only=True))
head = rows[0]
ix = {h: i for i, h in enumerate(head)}
def g(r, k):
    v = r[ix[k]]
    return '' if v is None else str(v).strip()

species = []
for r in rows[1:]:
    if not r[0]: continue
    species.append({
        'id': g(r, 'ID'), 'name': g(r, '흔한 이름'), 'kor': g(r, '국명(공식)'), 'sci': g(r, '학명'),
        'group': g(r, '그룹'), 'sub': g(r, '세부 분류'), 'fam': g(r, '과'),
        'sea': [s for s in g(r, '국내 해역').split(', ') if s], 'seaBasis': g(r, '해역 근거'),
        'intro': g(r, '한줄 소개'), 'look': g(r, '생김새'), 'life': g(r, '사는 곳·생태'),
        'breed': g(r, '산란·번식 시기'), 'use': g(r, '먹는 법·이용'), 'note': g(r, '알아두면 좋은 점'),
        'level': g(r, '정보 충실도'),
    })
species.sort(key=lambda s: (GROUP_ORDER.index(s['group']) if s['group'] in GROUP_ORDER else 99, s['name']))
ids = {s['id'] for s in species}

# 원문: 목록조회본/단건조회본
LAB = {'ABST': '개요', 'FORM': '형태', 'ECOL': '생태', 'HABI': '서식지', 'NADI': '국내 분포', 'INDI': '국외 분포',
       'UTLZ': '이용', 'ACTIVINFO': '효능·활성', 'CULTIVINF': '양식'}
wb2 = load_workbook(os.path.join(ROOT, 'output', '해양수산도감_원문.xlsx'), read_only=True)
orows = list(wb2['원문'].iter_rows(values_only=True))
oh = orows[0]
original = {}
for r in orows[1:]:
    d = dict(zip(oh, r))
    if d['ID'] not in ids: continue
    fields = [[LAB[k], str(d[k]).strip()] for k in LAB if d.get(k) and str(d[k]).strip()]
    original.setdefault(d['ID'], []).append({'ver': d['버전'], 'sciFull': d['학명'] or '', 'fields': fields})

os.makedirs(OUT, exist_ok=True)
json.dump({'date': '2026-11-07', 'groups': GROUP_ORDER, 'species': species},
          open(os.path.join(OUT, 'species.json'), 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
json.dump(original, open(os.path.join(OUT, 'original.json'), 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))

# 이미지 목록과 ChatGPT 묶음 프롬프트(그림 제작 요청용)
img_dir = os.path.join(ROOT, 'site', 'images')
def pose(s):
    g, sub, n = s['group'], s['sub'], s['name'] + s['kor']
    if g == '어류':
        if sub in ('가자미·넙치류', '서대·박대류'): return '눈이 있는 쪽 몸통 전체가 보이게, 위에서 내려다본 모습(머리 왼쪽)'
        if sub == '가오리·상어류' and ('상어' not in n and '상아리' not in n): return '등 쪽에서 내려다본 모습(머리 위쪽, 꼬리 아래쪽)'
        return '왼쪽을 바라보는 옆모습, 지느러미를 펼친 상태'
    if g == '오징어·문어류': return '등 쪽에서 본 모습, 머리(몸통)는 위쪽, 다리는 아래로 자연스럽게 펼침'
    if g == '새우·게류':
        if sub == '게류': return '등딱지가 보이게 위에서 내려다본 모습, 집게다리와 걷는다리를 좌우로 펼침'
        return '왼쪽을 바라보는 옆모습, 더듬이와 다리가 다 보이게'
    if g == '조개류': return '닫힌 상태로 바깥 껍데기 한쪽이 보이게 비스듬히 위에서 본 모습'
    if g == '고둥·전복류':
        if sub == '전복류': return '껍데기 등 쪽을 위에서 본 모습(숨구멍 줄이 보이게)'
        if '군소' in n: return '왼쪽을 바라보는 옆모습'
        return '껍데기 입구가 보이는 정면 모습, 꼭대기가 위쪽'
    if g == '해삼·성게류':
        return '왼쪽을 향한 옆모습(돌기가 보이게)' if '해삼' in n else '가시를 포함해 비스듬히 위에서 본 모습'
    if g == '멍게류': return '옆모습, 바위에 붙는 아래쪽까지 보이게'
    if g == '해조류': return '한 개체 전체를 세워 펼친 모습(바위에 붙는 부착기부터 끝까지)'
    return '몸 전체가 보이는 모습'

with open(os.path.join(img_dir, 'image_list.csv'), 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['파일명', 'ID', '흔한 이름', '국명', '학명', '그룹', '세부 분류', '과', '그리는 방향', '생김새(그림 참고용)'])
    for s in species:
        w.writerow([s['id'] + '.webp', s['id'], s['name'], s['kor'], s['sci'], s['group'], s['sub'], s['fam'], pose(s), s['look']])

guide = open(os.path.join(img_dir, 'CHATGPT_가이드.md'), encoding='utf8').read()
rules = guide.split('<!-- RULES START -->')[1].split('<!-- RULES END -->')[0].strip()
pdir = os.path.join(img_dir, 'prompts'); os.makedirs(pdir, exist_ok=True)
drawn = {fn[:-5] for fn in os.listdir(img_dir) if fn.endswith('.webp')}
todo = [s for s in species if s['id'] not in drawn]
for fn in os.listdir(pdir):
    if fn.startswith(('batch_', 'set_')): os.remove(os.path.join(pdir, fn))
BATCH = 1000  # 남은 종 전체를 한 파일로
nb = (len(todo) + BATCH - 1) // BATCH
for b in range(nb):
    chunk = todo[b * BATCH:(b + 1) * BATCH]
    lines = [f'# 해양수산도감 그림 묶음 set_{b + 1:02d} / {nb:02d} ({len(chunk)}종)', '',
             '아래 전체를 복사해 ChatGPT에 붙여 넣으세요.', '', '---', '', rules.replace('{BATCH}', f'{b + 1:02d}'), '',
             f'## 이번 묶음 목록 (set_{b + 1:02d}, {len(chunk)}종)', '']
    for i, s in enumerate(chunk, 1):
        nm = s['name'] if s['name'] == s['kor'] else f"{s['name']} (국명 {s['kor']})"
        look = s['look'] or '원문에 생김새 설명 없음. 학명 기준으로 일반적인 모습을 그리고 확인 필요 사항에 반드시 표시.'
        lines += [f'{i}. 파일명: `{s["id"]}.webp`', f'   - 이름: {nm}', f'   - 학명: {s["sci"]}',
                  f'   - 분류: {s["group"]} › {s["sub"]} › {s["fam"]}', f'   - 그리는 방향: {pose(s)}', f'   - 생김새: {look}', '']
    open(os.path.join(pdir, f'set_{b + 1:02d}.md'), 'w', encoding='utf8').write('\n'.join(lines))
man = os.path.join(OUT, 'images.json')
have = sorted(fn[:-5] for fn in os.listdir(img_dir) if fn.endswith('.webp') and fn[:-5] in ids)
print('prompt batches:', nb)
json.dump({'ext': 'webp', 'ids': have}, open(man, 'w', encoding='utf8'), ensure_ascii=False)
print(len(species), 'species,', sum(len(v) for v in original.values()), 'original rows,', len(have), 'images')
