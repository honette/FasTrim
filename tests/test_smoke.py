from pathlib import Path

import pytest
from PIL import Image

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from fastrim.app import MainWindow
from fastrim.config import Settings
from fastrim.imageops import load_image


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_load_crop_save_roundtrip(qapp: QApplication, tmp_path: Path) -> None:
    source = tmp_path / "sample.png"
    Image.new("RGB", (320, 240), (30, 80, 160)).save(source)

    settings = Settings(auto_save=False, auto_resize=False, last_dir=str(tmp_path))
    window = MainWindow(settings)
    window.show()
    qapp.processEvents()
    window.open_path(source, populate_list=True)
    assert window.working is not None
    assert window.working.size == (320, 240)
    assert window.file_list.count() == 1

    window.canvas.set_selection_box((20, 10, 120, 90))
    window.save_crop()
    saved = tmp_path / "sample_001.png"
    assert saved.exists()
    cropped = load_image(saved)
    assert cropped.size == (100, 80)
    window.close()


def test_dialogs_construct(qapp: QApplication) -> None:
    from fastrim.config import Settings
    from fastrim.dialogs import NamingDialog, SettingsDialog, ShortcutsDialog

    settings = Settings()
    settings_dialog = SettingsDialog(settings)
    naming = NamingDialog(settings)
    assert naming.preset() == "seq"
    settings_dialog.close()
    naming.close()
    ShortcutsDialog().close()


def test_auto_resize_on_load(qapp: QApplication, tmp_path: Path) -> None:
    source = tmp_path / "wide.jpg"
    Image.new("RGB", (4000, 2000), (1, 2, 3)).save(source, quality=90)
    settings = Settings(auto_resize=True, resize_long_side=1280, dont_upscale=True)
    window = MainWindow(settings)
    window.show()
    qapp.processEvents()
    window.open_path(source)
    assert window.working is not None
    assert window.working.size == (1280, 640)
    window.close()
