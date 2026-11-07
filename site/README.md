# 해양수산도감 (웹)

국립해양생물자원관 해양생물종정보 서비스(공공데이터포털) 데이터를 가공한 휴대폰용 도감입니다.
주요 수산물 235종의 쉬운 설명을 보여주고, 각 종에서 원문을 펼쳐 볼 수 있습니다.

## 구성
| 경로 | 내용 |
|---|---|
| `index.html`, `style.css`, `app.js` | 화면 (외부 라이브러리 없음) |
| `data/species.json` | 주요수산물 235종 (`output/해양수산도감.xlsx`의 주요수산물 시트에서 생성) |
| `data/original.json` | 원문 (`output/해양수산도감_원문.xlsx`에서 생성, '원문 보기'를 누를 때 불러옴) |
| `data/images.json` | 그림이 있는 종 목록 |
| `images/` | 그림 폴더와 그림 요청용 목록(`image_list.csv`), 규격 안내(`images/README.md`) |
| `tools/build_data.py` | 엑셀 → `data/*.json` 생성 |
| `tools/build_artifact.py` | 미리보기용 한 장짜리 페이지 생성 |

## 실행
데이터를 `fetch`로 불러오므로 웹 서버가 필요합니다.
```
cd site
python3 -m http.server 8000
# 브라우저에서 http://localhost:8000
```
GitHub Pages 같은 정적 호스팅에 `site/` 폴더를 그대로 올려도 됩니다.

## 내용 수정
`output/해양수산도감.xlsx`를 고친 뒤 저장소 최상위에서 `python3 site/tools/build_data.py`를 실행하세요.
