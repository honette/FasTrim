# Fastrim

画像を開いて範囲を切り、ファイル名を聞かずに別名保存するトリミングアプリです。Windows 11 向けです。

## 必要環境

- Python 3.10 以降

## インストール

```bash
python -m venv .venv
```

Windows:

```bat
.venv\Scripts\pip install -r requirements.txt
```

Linux / macOS:

```bash
.venv/bin/pip install -r requirements.txt
```

## 起動

```bash
python -m fastrim
```

Windows は `run.bat`、Linux / macOS は `./run.sh` でも起動できます。画像ファイルのパスを引数に渡せます。

```bash
python -m fastrim photo.jpg
```

## exe 化（Windows）

```bat
pip install pyinstaller
pyinstaller fastrim.spec
```

`dist\Fastrim.exe` ができます。
