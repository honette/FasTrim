from pathlib import Path

from PIL import Image

from fastrim.imageops import (
    crop_image,
    effective_ext,
    list_images,
    render_working,
    resize_long_side,
    rotate_image,
    save_image,
)


def _rgb(width: int, height: int, color: tuple[int, int, int] = (10, 20, 30)) -> Image.Image:
    return Image.new("RGB", (width, height), color)


def test_resize_long_side_down() -> None:
    out = resize_long_side(_rgb(4000, 2000), 1920, dont_upscale=True)
    assert out.size == (1920, 960)


def test_resize_does_not_upscale() -> None:
    src = _rgb(800, 600)
    assert resize_long_side(src, 1920, dont_upscale=True).size == (800, 600)
    assert resize_long_side(src, 1920, dont_upscale=False).size == (1920, 1440)


def test_rotate_swaps_dimensions() -> None:
    src = _rgb(200, 100, (255, 0, 0))
    src.putpixel((199, 0), (0, 255, 0))
    rotated = rotate_image(src, 90)
    assert rotated.size == (100, 200)
    # 右上 → 右下（時計回り90度）
    assert rotated.getpixel((99, 199)) == (0, 255, 0)


def test_render_rotate_then_resize() -> None:
    out = render_working(_rgb(2000, 1000), rotation=90, long_side=500, dont_upscale=True)
    assert out.size == (250, 500)


def test_crop_and_save_jpeg(tmp_path: Path) -> None:
    src = _rgb(100, 80, (255, 128, 0))
    cropped = crop_image(src, (10, 10, 40, 30))
    assert cropped.size == (30, 20)
    dest = tmp_path / "out.jpg"
    save_image(cropped, dest, jpeg_quality=90)
    assert dest.exists()
    with Image.open(dest) as saved:
        assert saved.size == (30, 20)


def test_effective_ext() -> None:
    assert effective_ext(Path("a.png"), "original") == ".png"
    assert effective_ext(Path("a.heic"), "original") == ".jpg"
    assert effective_ext(Path("a.png"), "jpeg") == ".jpg"


def test_first_openable_path(tmp_path: Path) -> None:
    from fastrim.imageops import first_openable_path

    image = tmp_path / "shot.jpg"
    image.write_bytes(b"x")
    other = tmp_path / "notes.txt"
    other.write_bytes(b"x")
    nested = tmp_path / "album"
    nested.mkdir()
    (nested / "a.png").write_bytes(b"x")
    assert first_openable_path([other, image]) == image
    assert first_openable_path([other]) is None
    found = first_openable_path([nested])
    assert found is not None
    assert found.name == "a.png"


def test_list_images_natural_sort(tmp_path: Path) -> None:
    for name in ("img10.jpg", "img2.jpg", "img1.jpg", "notes.txt"):
        (tmp_path / name).write_bytes(b"not-an-image")
    names = [p.name for p in list_images(tmp_path)]
    assert names == ["img1.jpg", "img2.jpg", "img10.jpg"]
