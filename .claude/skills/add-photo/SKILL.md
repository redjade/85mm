---
name: add-photo
description: 85mm 연습장(redjade.github.io/85mm)에 사진을 올린다. 원본 사진 파일이나 폴더를 받아 웹용 사본(긴 변 2400px, 메타데이터·GPS 제거)과 기록 초안을 만들고, 사용자와 함께 메모(보았다/생략했다, 거리, 분위기, 여섯 가지 말, 연습)를 채운 뒤 빌드하고 확인을 받아 배포한다. "사진 올려줘", "기록 추가", "이 사진들 올려" 같은 요청에 쓴다.
---

# 사진 올리기

이 저장소(`85mm`)의 루트에서 작업한다. 원본은 절대 저장소에 복사하지 않는다.

## 1. 웹용 사본 만들기

```bash
uv run python tools/add_photo.py <파일 또는 폴더...> [--drill <연습 id>]
```

- 먼저 `--dry-run`으로 몇 장이 들어가는지, 날짜와 EXIF가 제대로 읽히는지 보여 준다.
- 사용자가 연습 번호를 말했으면 `--drill`로 넘긴다. 연습 id는 `src/content/drills/*.md`의 파일 이름이다(예: `07-layers`).
- 출력은 한 줄에 사진 한 장씩 JSON이다. `status`가 `skip`(이미 올린 사진)이나 `error`인 것은 사용자에게 알려 준다.
- RAW(ARW, CR3, NEF…)는 받지 않는다. 사용자에게 JPEG로 내보내 달라고 한다. HEIC는 `uv pip install pillow-heif` 뒤에 받는다.
- 파이프라인이 의심스러우면 `uv run python tools/add_photo.py --selftest`로 확인한다.

## 2. 메모 채우기 (사용자와 함께)

각 사진의 `src/content/photos/<id>/photo.jpg`를 Read로 직접 본다. 그다음 `index.md`에서 아래 항목을 채운다.

| 항목 | 누가 | 내용 |
|---|---|---|
| `title` | 제안 → 사용자 확인 | 짧은 제목. 파일 이름(DSC0…)은 그대로 두지 않는다 |
| `alt` | Claude | 화면 낭독기용 한 문장 묘사. 사실만 쓴다 |
| `distance` | 제안 → 사용자 확인 | `near`(0.8–2m) / `mid`(3–8m) / `far`(20m–∞) |
| `mood` | **사용자** | 1 고요 … 5 흥분 |
| `elements` | 제안 → 사용자 확인 | 색 빛 대비 공기 이야기 생략 중에서 1~3개 |
| `drill` | 사용자 | 연습으로 찍었으면 연습 id |
| `seen` | **사용자** | 무엇을 보았나 (한두 문장) |
| `omitted` | **사용자** | 무엇을 생략했나 (한두 문장) |

- `seen`과 `omitted`는 사용자의 말이다. Claude가 지어내지 않는다. 사용자가 비워 두고 싶다고 하면 빈 문자열로 둔다.
- 여러 장이면 한 번에 표로 제안하고 사용자가 한꺼번에 고치게 한다.
- 다 채운 사진만 `draft: false`로 바꾼다. 나중에 쓰겠다고 하면 `draft: true`로 두고, 초안 목록은 `uv run python tools/add_photo.py --drafts`로 본다.
- 인물 사진이면 공개해도 되는 사진인지(아는 사람인지, 허락받았는지) 한 번 묻는다.

## 3. 빌드하고 배포하기

```bash
npm run build
```

- 빌드가 통과하면 바뀐 파일(`git status`)과 올라갈 사진 목록을 보여 준다.
- **커밋과 푸시는 사용자가 확인한 뒤에만 한다.** 푸시하면 공개 사이트에 바로 올라간다.
- 커밋 메시지 예: `photo: 2026-09-24 창가의 오후 외 2장`
- `main`에 푸시하면 GitHub Actions가 빌드해서 https://redjade.github.io/85mm/ 에 배포한다(1~2분).

## 하지 않는 것

- 원본 파일을 옮기거나 지우거나 저장소에 넣지 않는다.
- `tools/add_photo.py`를 거치지 않은 사진을 `src/content/photos`에 직접 넣지 않는다(GPS가 남을 수 있다).
- 사용자 대신 `seen`/`omitted`를 창작하지 않는다.
