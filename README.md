# Fastrim

画像を開いて範囲を切り、ファイル名を聞かずに別名保存するトリミングアプリです。Windows 11 向けです。

venv は OS をまたげません。Linux 用は `.venv`、Windows 用は `.venv_win` です。
Windows でのコマンドは **Git Bash** 前提です。

## 必要環境

- Python 3.10 以降
- Windows では Git Bash（Git for Windows）

## インストール（Linux / macOS）

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 起動

venv を activate した状態で:

```bash
python -m fastrim
```

または `./run.sh`

画像ファイルのパスを引数に渡せます。

```bash
python -m fastrim photo.jpg
```

## exe 化（Windows / Git Bash）

Linux からは作れません。venv を activate した Git Bash で:

```bash
python -m venv .venv_win
.venv_win/Scripts/pip install -r requirements.txt
.venv_win/Scripts/pip install pyinstaller
.venv_win/Scripts/pyinstaller fastrim.spec
```

`dist/Fastrim.exe` ができます。
