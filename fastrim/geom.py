from __future__ import annotations


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def parse_aspect(text: str | None) -> tuple[int, int] | None:
    if not text:
        return None
    parts = text.split(":")
    if len(parts) != 2:
        return None
    try:
        width, height = int(parts[0]), int(parts[1])
    except ValueError:
        return None
    if width <= 0 or height <= 0:
        return None
    return width, height


def selection_from_drag(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    img_w: int,
    img_h: int,
    aspect: tuple[int, int] | None = None,
    grid: int | None = None,
) -> tuple[int, int, int, int]:
    """Return an inclusive-start exclusive-end box (l, t, r, b) in image pixels."""
    if img_w <= 0 or img_h <= 0:
        return 0, 0, 0, 0

    x0 = clamp(x0, 0, img_w)
    y0 = clamp(y0, 0, img_h)
    x1 = clamp(x1, 0, img_w)
    y1 = clamp(y1, 0, img_h)

    if aspect:
        l, t, r, b = _aspect_box(x0, y0, x1, y1, aspect[0], aspect[1], img_w, img_h)
    else:
        l, r = sorted((x0, x1))
        t, b = sorted((y0, y1))
        l, t, r, b = int(round(l)), int(round(t)), int(round(r)), int(round(b))

    l = int(clamp(l, 0, img_w))
    r = int(clamp(r, 0, img_w))
    t = int(clamp(t, 0, img_h))
    b = int(clamp(b, 0, img_h))

    if grid and grid > 0 and not aspect:
        l, t, r, b = snap_box(l, t, r, b, grid, img_w, img_h)

    if r < l:
        l, r = r, l
    if b < t:
        t, b = b, t
    return l, t, r, b


def _aspect_box(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    aw: int,
    ah: int,
    img_w: int,
    img_h: int,
) -> tuple[int, int, int, int]:
    dx = x1 - x0
    dy = y1 - y0
    if dx == 0 and dy == 0:
        ix, iy = int(round(x0)), int(round(y0))
        return ix, iy, ix, iy

    if abs(dx) * ah >= abs(dy) * aw:
        width = abs(dx)
        height = width * ah / aw
    else:
        height = abs(dy)
        width = height * aw / ah

    sx = 1.0 if dx >= 0 else -1.0
    sy = 1.0 if dy >= 0 else -1.0
    max_w = (img_w - x0) if sx > 0 else x0
    max_h = (img_h - y0) if sy > 0 else y0
    scale = 1.0
    if width > max_w > 0:
        scale = min(scale, max_w / width)
    if height > max_h > 0:
        scale = min(scale, max_h / height)
    width *= scale
    height *= scale

    x2 = x0 + sx * width
    y2 = y0 + sy * height
    left, right = sorted((x0, x2))
    top, bottom = sorted((y0, y2))
    return (
        int(round(left)),
        int(round(top)),
        int(round(right)),
        int(round(bottom)),
    )


def snap_box(
    left: int,
    top: int,
    right: int,
    bottom: int,
    spacing: int,
    img_w: int,
    img_h: int,
) -> tuple[int, int, int, int]:
    def snap(value: int, maximum: int) -> int:
        snapped = int(round(value / spacing) * spacing)
        return int(clamp(snapped, 0, maximum))

    left = snap(left, img_w)
    right = snap(right, img_w)
    top = snap(top, img_h)
    bottom = snap(bottom, img_h)
    if right <= left:
        right = int(min(img_w, left + spacing))
    if bottom <= top:
        bottom = int(min(img_h, top + spacing))
    return left, top, right, bottom


def box_size(box: tuple[int, int, int, int]) -> tuple[int, int]:
    left, top, right, bottom = box
    return max(0, right - left), max(0, bottom - top)
