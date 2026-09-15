from datetime import datetime
from pathlib import Path

from fastrim.naming import example_name, next_dest_path


def test_example_name_seq() -> None:
    assert example_name("photo.jpg", preset="seq", digits=3, subfolder="", ext=".jpg") == "photo_001.jpg"
    assert (
        example_name("photo.jpg", preset="seq", digits=3, subfolder="trim", ext=".jpg")
        == "trim/photo_001.jpg"
    )


def test_example_name_datetime_and_seq_only() -> None:
    assert "20260915_143052" in example_name(
        "photo.jpg", preset="datetime", digits=3, subfolder="", ext=".jpg"
    )
    assert example_name("photo.jpg", preset="seq_only", digits=3, subfolder="", ext=".png") == "001.png"


def test_next_seq_skips_existing(tmp_path: Path) -> None:
    source = tmp_path / "cat.jpg"
    source.write_bytes(b"x")
    (tmp_path / "cat_001.jpg").write_bytes(b"x")
    (tmp_path / "cat_002.jpg").write_bytes(b"x")
    dest = next_dest_path(source, preset="seq", digits=3, ext=".jpg")
    assert dest.name == "cat_003.jpg"


def test_next_seq_never_overwrites_source(tmp_path: Path) -> None:
    source = tmp_path / "001.jpg"
    source.write_bytes(b"x")
    dest = next_dest_path(source, preset="seq_only", digits=3, ext=".jpg")
    assert dest.name == "002.jpg"


def test_datetime_collision(tmp_path: Path) -> None:
    source = tmp_path / "shot.png"
    source.write_bytes(b"x")
    now = datetime(2026, 9, 15, 14, 30, 52)
    first = tmp_path / "shot_20260915_143052.png"
    first.write_bytes(b"x")
    dest = next_dest_path(source, preset="datetime", ext=".png", now=now)
    assert dest.name == "shot_20260915_143052_2.png"


def test_subfolder_created(tmp_path: Path) -> None:
    source = tmp_path / "a.webp"
    source.write_bytes(b"x")
    dest = next_dest_path(source, preset="seq", digits=2, subfolder="trim", ext=".webp")
    assert dest == tmp_path / "trim" / "a_01.webp"
    assert dest.parent.is_dir()
