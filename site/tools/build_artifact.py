"""미리보기용 한 장짜리 페이지를 만듭니다(CSS·JS를 본문에 넣음).
실행: python3 site/tools/build_artifact.py <출력 폴더>"""
import os, re, sys, shutil
SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[1]
os.makedirs(os.path.join(out, 'data'), exist_ok=True)
html = open(os.path.join(SITE, 'index.html'), encoding='utf8').read()
css = open(os.path.join(SITE, 'style.css'), encoding='utf8').read()
js = open(os.path.join(SITE, 'app.js'), encoding='utf8').read()
body = re.search(r'<!-- BODY START -->(.*)<!-- BODY END -->', html, re.S).group(1)
fonts = re.search(r'<link rel="stylesheet" href="(https://fonts\.googleapis\.com[^"]+)">', html).group(1)
page = ('<title>해양수산도감</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n'
        '<link rel="stylesheet" href="' + fonts + '">\n<style>\n' + css + '\n</style>\n' + body + '\n<script>\n' + js + '\n</script>\n')
open(os.path.join(out, 'index.html'), 'w', encoding='utf8').write(page)
for f in ('species.json', 'original.json', 'images.json'):
    shutil.copy(os.path.join(SITE, 'data', f), os.path.join(out, 'data', f))
print('ok', len(page))
