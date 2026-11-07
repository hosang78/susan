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

# 이미지 목록(그림 제작 요청용)
img_dir = os.path.join(ROOT, 'site', 'images')
with open(os.path.join(img_dir, 'image_list.csv'), 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['파일명', 'ID', '흔한 이름', '국명', '학명', '그룹', '생김새(그림 참고용)'])
    for s in species:
        w.writerow([s['id'] + '.webp', s['id'], s['name'], s['kor'], s['sci'], s['group'], s['look']])
man = os.path.join(OUT, 'images.json')
have = sorted(fn[:-5] for fn in os.listdir(img_dir) if fn.endswith('.webp') and fn[:-5] in ids)
json.dump({'ext': 'webp', 'ids': have}, open(man, 'w', encoding='utf8'), ensure_ascii=False)
print(len(species), 'species,', sum(len(v) for v in original.values()), 'original rows,', len(have), 'images')
