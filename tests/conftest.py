import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest


@pytest.fixture(autouse=True)
def fastrim_config_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("FASTRIM_CONFIG_DIR", str(tmp_path / "fastrim-config"))
