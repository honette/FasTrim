from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from fastrim.constants import PRESET_DATETIME, PRESET_SEQ, PRESET_SEQ_ONLY


def normalize_ext(ext: str) -> str:
    ext = ext.strip() or ".jpg"
    if not ext.startswith("."):
        ext = "." + ext
    return ext.lower()


def example_name(
    source_name: str,
    *,
    preset: str,
    digits: int,
    subfolder: str,
    ext: str,
) -> str:
    stem = Path(source_name).stem or "image"
    ext = normalize_ext(ext)
    digits = max(1, digits)
    if preset == PRESET_DATETIME:
        filename = f"{stem}_20260915_143052{ext}"
    elif preset == PRESET_SEQ_ONLY:
        filename = f"{1:0{digits}d}{ext}"
    else:
        filename = f"{stem}_{1:0{digits}d}{ext}"
    sub = subfolder.strip().replace("\\", "/").strip("/")
    if sub:
        return f"{sub}/{filename}"
    return filename


def next_dest_path(
    source: Path,
    *,
    preset: str = PRESET_SEQ,
    digits: int = 3,
    subfolder: str = "",
    ext: str | None = None,
    now: datetime | None = None,
) -> Path:
    source = Path(source)
    ext = normalize_ext(ext if ext is not None else source.suffix or ".jpg")
    digits = max(1, min(8, digits))
    dest_dir = source.parent
    sub = subfolder.strip().replace("\\", "/").strip("/")
    if sub:
        dest_dir = dest_dir / sub
    dest_dir.mkdir(parents=True, exist_ok=True)

    if preset == PRESET_DATETIME:
        stamp = (now or datetime.now()).strftime("%Y%m%d_%H%M%S")
        base = f"{source.stem}_{stamp}"
        candidate = dest_dir / f"{base}{ext}"
        n = 2
        while _taken(candidate, source):
            candidate = dest_dir / f"{base}_{n}{ext}"
            n += 1
        return candidate

    if preset == PRESET_SEQ_ONLY:
        pattern = re.compile(rf"^(\d+){re.escape(ext)}$", re.IGNORECASE)
        n = _max_number(dest_dir, pattern) + 1
        while True:
            candidate = dest_dir / f"{n:0{digits}d}{ext}"
            if not _taken(candidate, source):
                return candidate
            n += 1

    pattern = re.compile(
        rf"^{re.escape(source.stem)}_(\d+){re.escape(ext)}$",
        re.IGNORECASE,
    )
    n = _max_number(dest_dir, pattern) + 1
    while True:
        candidate = dest_dir / f"{source.stem}_{n:0{digits}d}{ext}"
        if not _taken(candidate, source):
            return candidate
        n += 1


def _max_number(folder: Path, pattern: re.Pattern[str]) -> int:
    highest = 0
    try:
        names = [p.name for p in folder.iterdir() if p.is_file()]
    except OSError:
        return 0
    for name in names:
        match = pattern.match(name)
        if match:
            highest = max(highest, int(match.group(1)))
    return highest


def _taken(candidate: Path, source: Path) -> bool:
    if candidate.exists():
        return True
    try:
        return candidate.resolve() == source.resolve()
    except OSError:
        return False
