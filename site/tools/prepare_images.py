"""site/images/ 의 그림을 앱 규격으로 맞추고 화면 목록(data/images.json)을 갱신합니다.
실행: python3 site/tools/prepare_images.py  (저장소 최상위에서)

- 파일 이름이 {ID}.png / .jpg / .jpeg / .webp 인 그림만 처리합니다.
- 4:3이 아니면 가운데 기준으로 자르고, 960×720으로 맞춘 뒤 WebP(품질 82, 120KB 이하)로 저장합니다.
- PNG/JPG 원본은 WebP로 바꾼 뒤 지웁니다.
"""
import os, io, json, subprocess, sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
IMG = os.path.join(ROOT, 'site', 'images')
W, H, MAX_KB = 960, 720, 120
ids = {s['id'] for s in json.load(open(os.path.join(ROOT, 'site', 'data', 'species.json'), encoding='utf8'))['species']}

def to_spec(im):
    im = im.convert('RGB')
    w, h = im.size
    if abs(w / h - 4 / 3) > 0.01:
        if w / h > 4 / 3:
            nw = round(h * 4 / 3); im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
        else:
            nh = round(w * 3 / 4); im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    return im.resize((W, H), Image.LANCZOS)

report, unknown = [], []
for fn in sorted(os.listdir(IMG)):
    stem, ext = os.path.splitext(fn)
    if ext.lower() not in ('.png', '.jpg', '.jpeg', '.webp'): continue
    if stem not in ids: unknown.append(fn); continue
    path = os.path.join(IMG, fn)
    src = Image.open(path)
    small = src.size[0] < W or src.size[1] < H
    if ext.lower() == '.webp' and src.size == (W, H) and os.path.getsize(path) <= MAX_KB * 1024:
        report.append((fn, 'OK', os.path.getsize(path) // 1024, '')); continue
    im = to_spec(src)
    q = 82
    while True:
        buf = io.BytesIO(); im.save(buf, 'WEBP', quality=q, method=6)
        if buf.tell() <= MAX_KB * 1024 or q <= 65: break
        q -= 5
    out = os.path.join(IMG, stem + '.webp')
    open(out, 'wb').write(buf.getvalue())
    if ext.lower() != '.webp': os.remove(path)
    report.append((stem + '.webp', '변환', buf.tell() // 1024, '원본이 960×720보다 작음(흐릴 수 있음)' if small else ''))

for r in report: print('{:<22} {:<4} {:>4}KB {}'.format(*r))
if unknown: print('ID와 맞지 않아 건너뛴 파일:', ', '.join(unknown))
subprocess.run([sys.executable, os.path.join(ROOT, 'site', 'tools', 'build_data.py')], check=True)
