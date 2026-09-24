# 85mm

풀프레임 · 85mm f/1.8 한 개로 연습하고 기록하는 개인 노트.
https://redjade.github.io/85mm/

- **시작하며**: 왜 이 연습장인가
- **배우기**: 85mm의 성질과 보는 법 (`src/content/learn/`)
- **연습**: 제약이 있는 과제 카드 (`src/content/drills/`)
- **기록**: 찍은 사진과 두 줄 메모 (`src/content/photos/<id>/`)
- **궤적**: 거리 × 분위기 지도, 달마다, 조리개, 여섯 개의 단어

## 사진 올리기

```bash
uv run python tools/add_photo.py ~/Pictures/export/          # 웹용 사본 + 초안
uv run python tools/add_photo.py photo.jpg --drill layers  # 연습에 연결
uv run python tools/add_photo.py --drafts                     # 메모를 아직 안 채운 초안
uv run python tools/add_photo.py --selftest                   # 파이프라인 검증
```

긴 변 2400px JPEG로 줄이고 EXIF·GPS 등 메타데이터를 모두 지운다(색 프로파일은 남긴다).
촬영 정보는 `index.md`에 옮겨 적는다. 원본은 저장소에 넣지 않는다.
Claude Code에서는 `add-photo` 스킬이 이 과정과 메모 채우기를 함께 진행한다.

## 개발

```bash
npm install
npm run dev      # http://localhost:4321/85mm/
npm run build    # dist/
```

`main`에 푸시하면 GitHub Actions(`.github/workflows/deploy.yml`)가 빌드해서 GitHub Pages로 배포한다.
