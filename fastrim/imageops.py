from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, ImageOps

from fastrim.constants import IMAGE_EXTS

try:
    from pillow_heif import register_heif_opener

    register_heif_opener()
except ImportError:
    pass


_NATURAL_SPLIT = re.compile(r"(\d+)")


def natural_key(name: str) -> list:
    return [
        int(part) if part.isdigit() else part.casefold()
        for part in _NATURAL_SPLIT.split(name)
    ]


def is_image_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in IMAGE_EXTS


def first_openable_path(paths: list[Path]) -> Path | None:
    for path in paths:
        path = Path(path)
        if is_image_file(path):
            return path
        if path.is_dir():
            images = list_images(path)
            if images:
                return images[0]
    return None


def list_images(folder: Path) -> list[Path]:
    try:
        files = [p.resolve() for p in folder.iterdir() if is_image_file(p)]
    except OSError:
        return []
    files.sort(key=lambda p: natural_key(p.name))
    return files


def load_image(path: Path) -> Image.Image:
    with Image.open(path) as opened:
        image = ImageOps.exif_transpose(opened)
        return _normalize_mode(image)


def _normalize_mode(image: Image.Image) -> Image.Image:
    if image.mode in ("RGB", "RGBA"):
        return image.copy()
    if image.mode == "P":
        return image.convert("RGBA" if "transparency" in image.info else "RGB")
    if image.mode in ("LA", "PA"):
        return image.convert("RGBA")
    if image.mode in ("L", "CMYK", "I", "F", "1"):
        return image.convert("RGB")
    return image.convert("RGBA")


def resize_long_side(
    image: Image.Image,
    long_side: int,
    dont_upscale: bool = True,
) -> Image.Image:
    if long_side <= 0:
        return image
    width, height = image.size
    current = max(width, height)
    if current <= 0:
        return image
    if dont_upscale and current <= long_side:
        return image
    scale = long_side / current
    new_size = (max(1, round(width * scale)), max(1, round(height * scale)))
    if new_size == image.size:
        return image
    return image.resize(new_size, Image.Resampling.LANCZOS)


def rotate_image(image: Image.Image, degrees_clockwise: int) -> Image.Image:
    angle = degrees_clockwise % 360
    if angle == 0:
        return image
    if angle == 90:
        return image.transpose(Image.Transpose.ROTATE_270)
    if angle == 180:
        return image.transpose(Image.Transpose.ROTATE_180)
    if angle == 270:
        return image.transpose(Image.Transpose.ROTATE_90)
    return image.rotate(-angle, expand=True, resample=Image.Resampling.BICUBIC)


def render_working(
    source: Image.Image,
    rotation: int = 0,
    long_side: int | None = None,
    dont_upscale: bool = True,
) -> Image.Image:
    image = rotate_image(source, rotation)
    if long_side:
        image = resize_long_side(image, long_side, dont_upscale=dont_upscale)
    return image


def crop_image(image: Image.Image, box: tuple[int, int, int, int]) -> Image.Image:
    left, top, right, bottom = box
    left = max(0, left)
    top = max(0, top)
    right = min(image.width, right)
    bottom = min(image.height, bottom)
    if right <= left or bottom <= top:
        raise ValueError("empty crop")
    return image.crop((left, top, right, bottom))


def effective_ext(source: Path, output_format: str) -> str:
    if output_format and output_format != "original":
        mapping = {
            "jpeg": ".jpg",
            "jpg": ".jpg",
            "png": ".png",
            "webp": ".webp",
        }
        return mapping.get(output_format.lower(), ".jpg")
    ext = source.suffix.lower() or ".jpg"
    if ext in {".heic", ".heif"}:
        return ".jpg"
    if ext not in IMAGE_EXTS:
        return ".jpg"
    return ext


def save_image(
    image: Image.Image,
    path: Path,
    jpeg_quality: int = 92,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    ext = path.suffix.lower()
    quality = max(1, min(100, jpeg_quality))
    if ext in {".jpg", ".jpeg", ".jfif"}:
        to_save = image.convert("RGB") if image.mode != "RGB" else image
        to_save.save(
            path,
            format="JPEG",
            quality=quality,
            optimize=True,
            subsampling=0,
        )
        return
    if ext == ".webp":
        to_save = image
        if image.mode not in ("RGB", "RGBA"):
            to_save = image.convert("RGBA")
        to_save.save(path, format="WEBP", quality=quality, method=4)
        return
    if ext == ".png":
        image.save(path, format="PNG", optimize=True)
        return
    image.save(path)
