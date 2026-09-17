# AGENTS.md

このファイルは、このリポジトリで作業するAIコーディングエージェントへの指示です。

## プロジェクト概要

FasTrim は JTrim 代替のデスクトップ画像トリマー。Python 3 + PySide6 + Pillow。
配布先は Windows 11 の `.exe`（`fastrim.spec`）。製品仕様の正は `IDEA.txt`。UI 文言は英語。

## よく使うコマンド

リポジトリルート、venv 前提。

- 依存インストール（Linux）: `python3 -m venv .venv` → `source .venv/bin/activate` → `pip install -r requirements.txt`
- 依存インストール（Windows / Git Bash）: `python -m venv .venv_win` → `source .venv_win/Scripts/activate` → `pip install -r requirements.txt`
- 起動: activate 済みなら `python -m fastrim`。または `./run.sh`
- テスト全体: `pip install pytest` のあと `python -m pytest`
- テスト単体: `python -m pytest tests/test_naming.py::test_next_seq_skips_existing`
- exe 化（Windows / Git Bash のみ）: `source .venv_win/Scripts/activate` → `pip install pyinstaller` → `pyinstaller fastrim.spec` → `dist/FasTrim.exe`

Lint / 整形 / CI の設定はない。作らない。

## アーキテクチャ

画像処理と命名は Qt 非依存。UI がそれらを呼ぶ。ドメイン → UI の import はしない。

- ドメイン: `fastrim/geom.py`, `imageops.py`, `naming.py`, `config.py`, `constants.py`
- UI: `fastrim/app.py`, `canvas.py`, `dialogs.py`, `theme.py`

データ流: ファイル → `load_image` が `source`。`rotation` と `long_side` を毎回 `render_working(source, ...)` に渡して `working` を作り直す。クロップは `working` 上のピクセル。保存先は `naming.next_dest_path`。元ファイルは上書きしない。

選択範囲は PIL と同じ **左上 inclusive・右下 exclusive** の `(l, t, r, b)`。`QRect.right()`（inclusive）と混同しない。

## このリポジトリ固有のルール

- サイドバー一覧は、画像未オープンの状態からロードしたときだけ作り直す。一覧からの切替では再スキャンしない（`open_path` の `populate_list` は `self.path is None`）
- グリッドスナップとアスペクト比固定は排他。両方 True にしない
- 回転・リサイズは `source` から再計算する。`working` へ重ね掛けしない
- 既定では小さい画像を拡大しない（`dont_upscale`）
- 保存は常に別名。衝突したら連番を進める
- `pil_to_qpixmap` は `QImage.copy()` が必要（PIL バッファは一時的）
- HEIC は `pillow-heif` があれば有効。必須依存に足さない
- 仕様を足す・変えるときは `IDEA.txt` と矛盾させない。UI 文言は英語のまま（CJK フォントが無い環境でも読めるようにする）
- アイコンは `assets/FasTrim.ico`（+ `assets/icon.png`）。タスクバーと exe は ico、実行時は `theme.asset_path` が PyInstaller の `_MEIPASS` も見る。デザイン変更時は `fastrim.theme.make_app_icon` の描画と揃える

## 注意

- 設定は `%APPDATA%/FasTrim/settings.json`（Windows）または `~/.config/fastrim/settings.json`。ユーザー設定を汚さない。退避先は環境変数 `FASTRIM_CONFIG_DIR`。`tests/conftest.py` がテスト中に一時ディレクトリへ向ける
- 同 conftest が `QT_QPA_PLATFORM=offscreen` をセットする。ヘッドレスで `MainWindow` を直に使うなら同じ変数が要る
- `pytest` は `requirements.txt` に入っていない
- venv は OS 専用。Linux は `.venv`、Windows は `.venv_win`。混ぜない
- Windows の作業・ビルドは Git Bash 前提（cmd / PowerShell ではない）。activate は `source .venv_win/Scripts/activate`
- `dist/` `build/` `.venv/` `.venv_win/` は生成物。コミットしない。`assets/` はコミットする
- エージェント向け指示は `AGENTS.md` のみ。`CLAUDE.md` / `.cursorrules` / `.github/copilot-instructions.md` などは作らない
