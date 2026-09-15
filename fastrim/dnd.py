from __future__ import annotations

from pathlib import Path

from fastrim.imageops import first_openable_path


def first_dropped_image(mime) -> Path | None:  # noqa: ANN001
    if mime is None or not mime.hasUrls():
        return None
    paths: list[Path] = []
    for url in mime.urls():
        local = url.toLocalFile()
        if local:
            paths.append(Path(local))
    return first_openable_path(paths)
