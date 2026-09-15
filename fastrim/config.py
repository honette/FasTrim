from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

from fastrim.constants import APP_NAME, PRESET_SEQ


def config_dir() -> Path:
    override = os.environ.get("FASTRIM_CONFIG_DIR")
    if override:
        return Path(override)
    if os.name == "nt":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / APP_NAME
    return Path.home() / ".config" / APP_NAME.lower()


def config_path() -> Path:
    return config_dir() / "settings.json"


@dataclass
class Settings:
    auto_save: bool = False
    auto_resize: bool = False
    resize_long_side: int = 1920
    dont_upscale: bool = True
    grid_enabled: bool = False
    grid_spacing: int = 16
    aspect_enabled: bool = False
    aspect_ratio: str = "16:9"
    zoom_mode: str = "fit"
    naming_preset: str = PRESET_SEQ
    seq_digits: int = 3
    subfolder: str = ""
    output_format: str = "original"
    jpeg_quality: int = 92
    last_dir: str = ""
    window_x: int = -1
    window_y: int = -1
    window_w: int = 1280
    window_h: int = 800
    splitter: list[int] = field(default_factory=lambda: [980, 240])

    def to_json(self) -> dict:
        return asdict(self)

    @classmethod
    def from_json(cls, data: dict) -> "Settings":
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        filtered = {k: v for k, v in data.items() if k in known}
        settings = cls(**filtered)
        if settings.grid_enabled and settings.aspect_enabled:
            settings.aspect_enabled = False
        settings.seq_digits = max(1, min(8, int(settings.seq_digits)))
        settings.grid_spacing = max(2, min(512, int(settings.grid_spacing)))
        settings.jpeg_quality = max(1, min(100, int(settings.jpeg_quality)))
        return settings


def load_settings() -> Settings:
    path = config_path()
    if not path.exists():
        return Settings()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return Settings.from_json(data)
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        pass
    return Settings()


def save_settings(settings: Settings) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(settings.to_json(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
