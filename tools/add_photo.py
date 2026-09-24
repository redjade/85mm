"""원본 사진 → 웹용 사본 + 기록 초안(index.md).

    uv run python tools/add_photo.py <파일 또는 폴더...> [--drill 07-layers] [--dry-run]
    uv run python tools/add_photo.py --drafts      # 메모가 비어 있는 초안 목록
    uv run python tools/add_photo.py --selftest    # 파이프라인 회귀 검증

하는 일
  1. EXIF에서 촬영 정보(날짜, 조리개, 셔터, ISO, 초점거리, 카메라, 렌즈)만 읽는다.
  2. 회전을 반영하고 긴 변 2400px JPEG로 줄인다. 색 프로파일(ICC)은 남기고
     EXIF/XMP/GPS 등 메타데이터는 모두 버린다. 저장 후 다시 열어 비어 있는지 확인한다.
  3. src/content/photos/<날짜-이름>/ 에 photo.jpg 와 index.md(draft: true)를 만든다.
  4. 원본 해시를 기록해 같은 사진을 두 번 올리지 않는다.
원본 파일은 건드리지 않고 저장소에도 넣지 않는다.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageOps

REPO = Path(__file__).resolve().parent.parent
PHOTOS = REPO / "src" / "content" / "photos"
DRILLS = REPO / "src" / "content" / "drills"
EXTS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}
LONG_EDGE = 2400
QUALITY = 88

# EXIF 태그 번호
T_MAKE, T_MODEL, T_ORIENT = 271, 272, 274
IFD_EXIF, IFD_GPS = 0x8769, 0x8825
T_EXPOSURE, T_FNUMBER, T_ISO = 33434, 33437, 34855
T_DATETIME_ORIG, T_FOCAL, T_LENS = 36867, 37386, 42036

try:  # 아이폰 HEIC도 받고 싶으면: uv pip install pillow-heif
    from pillow_heif import register_heif_opener  # type: ignore

    register_heif_opener()
    EXTS |= {".heic", ".heif"}
except ImportError:
    pass


@dataclass
class Shot:
    date: datetime
    exif: dict = field(default_factory=dict)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def _num(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def _clean(v) -> str | None:
    if v is None:
        return None
    s = str(v).replace("\x00", "").strip()
    return s or None


def fmt_shutter(t: float) -> str:
    if t >= 1:
        return f"{t:g}"
    return f"1/{round(1 / t)}"


def read_shot(img: Image.Image, src: Path) -> Shot:
    ex = img.getexif()
    sub = ex.get_ifd(IFD_EXIF) if ex else {}
    info: dict = {}

    fn = _num(sub.get(T_FNUMBER))
    if fn:
        info["fnumber"] = round(fn, 1)
    t = _num(sub.get(T_EXPOSURE))
    if t:
        info["shutter"] = fmt_shutter(t)
    iso = sub.get(T_ISO)
    if isinstance(iso, (tuple, list)):
        iso = iso[0] if iso else None
    if _num(iso):
        info["iso"] = int(_num(iso))
    fl = _num(sub.get(T_FOCAL))
    if fl:
        info["focal"] = round(fl)
    make, model = _clean(ex.get(T_MAKE)), _clean(ex.get(T_MODEL))
    if model:
        info["camera"] = model if (not make or model.lower().startswith(make.lower().split()[0])) else f"{make} {model}"
    lens = _clean(sub.get(T_LENS))
    if lens:
        info["lens"] = lens

    date = None
    raw = _clean(sub.get(T_DATETIME_ORIG))
    if raw:
        try:
            date = datetime.strptime(raw[:19], "%Y:%m:%d %H:%M:%S")
        except ValueError:
            date = None
    if date is None:
        date = datetime.fromtimestamp(src.stat().st_mtime)
    return Shot(date=date, exif=info)


def slugify(stem: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")
    return s or "photo"


def existing_hashes(root: Path) -> dict[str, str]:
    out = {}
    for md in root.glob("*/index.md"):
        m = re.search(r"^source_hash:\s*\"?([0-9a-f]+)\"?", md.read_text(encoding="utf-8"), re.M)
        if m:
            out[m.group(1)] = md.parent.name
    return out


def yq(s: str) -> str:
    """YAML 큰따옴표 문자열 (JSON 문자열은 유효한 YAML이다)."""
    return json.dumps(s, ensure_ascii=False)


def frontmatter(title: str, shot: Shot, h: str, drill: str | None) -> str:
    lines = [
        "---",
        f"title: {yq(title)}",
        f"date: {shot.date.strftime('%Y-%m-%dT%H:%M:%S')}",
        "image: ./photo.jpg",
        'alt: ""',
        "draft: true  # 메모를 채운 뒤 false로",
        "exif:",
    ]
    for k in ("fnumber", "shutter", "iso", "focal", "camera", "lens"):
        if k in shot.exif:
            v = shot.exif[k]
            lines.append(f"  {k}: {yq(v) if isinstance(v, str) else v}")
    if not shot.exif:
        lines[-1] = "exif: {}"
    lines += [
        "distance: mid  # near | mid | far",
        "mood: 3  # 1 고요 … 5 흥분",
        "elements: []  # 색 빛 대비 공기 이야기 생략 중에서",
    ]
    if drill:
        lines.append(f"drill: {drill}")
    lines += [
        'seen: ""  # 무엇을 보았나',
        'omitted: ""  # 무엇을 생략했나',
        f'source_hash: "{h}"',
        "---",
        "",
    ]
    return "\n".join(lines)


def assert_clean(path: Path) -> None:
    with Image.open(path) as im:
        ex = im.getexif()
        if len(ex) or ex.get_ifd(IFD_GPS) or "exif" in im.info or "xmp" in im.info:
            raise RuntimeError(f"메타데이터가 남아 있다: {path}")


def process(src: Path, root: Path, drill: str | None, seen: dict[str, str], dry: bool, long_edge: int) -> dict:
    h = sha(src)
    if h in seen:
        return {"status": "skip", "src": str(src), "reason": f"이미 올림 ({seen[h]})"}

    with Image.open(src) as im:
        shot = read_shot(im, src)
        icc = im.info.get("icc_profile")
        img = ImageOps.exif_transpose(im)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        img.thumbnail((long_edge, long_edge), Image.Resampling.LANCZOS)

    base = f"{shot.date:%Y-%m-%d}-{slugify(src.stem)}"
    pid, n = base, 2
    while (root / pid).exists():
        pid, n = f"{base}-{n}", n + 1
    out_dir = root / pid

    result = {
        "status": "dry-run" if dry else "added",
        "id": pid,
        "src": str(src),
        "size": list(img.size),
        "date": shot.date.isoformat(),
        "exif": shot.exif,
    }
    if dry:
        return result

    out_dir.mkdir(parents=True)
    photo = out_dir / "photo.jpg"
    save_kw = dict(quality=QUALITY, optimize=True, progressive=True)
    if icc:
        save_kw["icc_profile"] = icc
    img.save(photo, "JPEG", **save_kw)  # exif=를 넘기지 않으므로 메타데이터는 모두 빠진다
    assert_clean(photo)
    (out_dir / "index.md").write_text(frontmatter(src.stem, shot, h, drill), encoding="utf-8")
    seen[h] = pid
    result["photo"] = str(photo)
    result["md"] = str(out_dir / "index.md")
    return result


def collect(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for p in map(Path, paths):
        if p.is_dir():
            files += sorted(f for f in p.iterdir() if f.suffix.lower() in EXTS)
        elif p.suffix.lower() in EXTS:
            files.append(p)
        else:
            print(json.dumps({"status": "skip", "src": str(p), "reason": "지원하지 않는 형식 (RAW는 JPEG로 내보낸 뒤)"}, ensure_ascii=False))
    return files


def list_drafts(root: Path) -> None:
    for md in sorted(root.glob("*/index.md")):
        text = md.read_text(encoding="utf-8")
        if re.search(r"^draft:\s*true", text, re.M):
            print(json.dumps({"id": md.parent.name, "md": str(md), "photo": str(md.parent / "photo.jpg")}, ensure_ascii=False))


def selftest() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="85mm-selftest-"))
    try:
        src = tmp / "DSC01234.JPG"
        im = Image.new("RGB", (3000, 2000), (200, 120, 60))
        ex = Image.Exif()
        ex[T_MAKE], ex[T_MODEL], ex[T_ORIENT] = "SONY", "ILCE-7M4", 6
        sub = ex.get_ifd(IFD_EXIF)
        sub[T_FNUMBER], sub[T_EXPOSURE], sub[T_ISO] = 1.8, 0.004, 400
        sub[T_FOCAL], sub[T_LENS] = 85.0, "FE 85mm F1.8"
        sub[T_DATETIME_ORIG] = "2026:03:14 17:42:05"
        gps = ex.get_ifd(IFD_GPS)
        gps[1], gps[2], gps[3], gps[4] = "N", (37.0, 33.0, 12.0), "E", (126.0, 58.0, 40.0)
        im.save(src, exif=ex, quality=95)
        with Image.open(src) as check:
            assert check.getexif().get_ifd(IFD_GPS), "테스트 원본에 GPS가 없다"

        root = tmp / "photos"
        root.mkdir()
        seen: dict[str, str] = {}
        r = process(src, root, "07-layers", seen, dry=False, long_edge=LONG_EDGE)
        assert r["status"] == "added", r
        assert r["id"] == "2026-03-14-dsc01234", r["id"]
        assert r["size"] == [1600, 2400], f"회전/축소 실패: {r['size']}"
        assert r["exif"] == {"fnumber": 1.8, "shutter": "1/250", "iso": 400, "focal": 85, "camera": "SONY ILCE-7M4", "lens": "FE 85mm F1.8"}, r["exif"]
        assert_clean(Path(r["photo"]))
        md = Path(r["md"]).read_text(encoding="utf-8")
        for needle in ("draft: true", "drill: 07-layers", "fnumber: 1.8", 'shutter: "1/250"', "date: 2026-03-14T17:42:05"):
            assert needle in md, f"frontmatter에 {needle!r} 없음"

        again = process(src, root, None, existing_hashes(root), dry=False, long_edge=LONG_EDGE)
        assert again["status"] == "skip", again

        png = tmp / "noexif.png"
        Image.new("RGBA", (800, 500), (10, 20, 30, 255)).save(png)
        r2 = process(png, root, None, {}, dry=False, long_edge=LONG_EDGE)
        assert r2["size"] == [800, 500] and r2["exif"] == {}, r2
        assert "exif: {}" in Path(r2["md"]).read_text(encoding="utf-8")
        print("selftest ok")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--drill", help="연습 id (예: 07-layers)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--long-edge", type=int, default=LONG_EDGE)
    ap.add_argument("--drafts", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        return selftest()
    if a.drafts:
        return list_drafts(PHOTOS)
    if not a.paths:
        ap.error("사진 파일이나 폴더를 넘겨 주세요")
    if a.drill and not (DRILLS / f"{a.drill}.md").exists():
        ap.error(f"연습 '{a.drill}'이 없다. 가능한 값: {', '.join(p.stem for p in sorted(DRILLS.glob('*.md')))}")

    PHOTOS.mkdir(parents=True, exist_ok=True)
    seen = existing_hashes(PHOTOS)
    for f in collect(a.paths):
        try:
            print(json.dumps(process(f, PHOTOS, a.drill, seen, a.dry_run, a.long_edge), ensure_ascii=False))
        except Exception as e:  # 한 장이 실패해도 나머지는 계속
            print(json.dumps({"status": "error", "src": str(f), "reason": str(e)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
