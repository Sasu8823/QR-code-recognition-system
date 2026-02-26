Photo Auto-Organization System
（症例写真 自動整理システム）

■ フォルダ構成（変更しないでください）
ダウンロードしたフォルダは、そのままの構成で使用してください。
```
qr-organized-main/ 
├── main.py 
├── config.json 
├── qr-generator.html 
├── qrcode.min.js 
├── README.md 
```
※ ファイルの場所を変更しないでください。

■ 初回セットアップ（最初の1回だけ）
① Pythonをインストール

https://www.python.org/downloads/

Download Python

「Add Python to PATH」にチェック

Install Now

② 必要な部品をインストール

qr-organized-main フォルダを開く

上部のアドレスバーに cmd と入力してEnter

黒い画面で入力：

pip install uv

次に：

uv sync

エラーが出なければ完了です。

■ 設定

config.json を開く

watch_folder を変更

例：

"watch_folder": "E:\\Dropbox\\症例写真"

保存して閉じる。

■ 毎日の起動方法

qr-organized-main フォルダを開く

アドレスバーに cmd と入力

黒い画面で入力：

uv run python main.py

この画面は閉じないでください。

■ 日常の使い方
① 患者の写真を撮影

1人分ずつ撮影してください。

② QRコードを表示

qr-generator.html をダブルクリック

患者番号を入力

「Generate QR Code」

「Fullscreen QR」を押す

※ htmlファイルはフォルダ内から直接開きます。

③ 最後にQRを撮影

デジカメで画面を撮影

必ず最後に撮影してください

■ 自動整理後
```
Watch Folder/
├── 患者番号/
│   └── YYYY.MM.DD/
│       ├── 001.jpg
│       ├── 002.jpg
│       ├── QR_患者番号.jpg
├── _backup/
├── _done/
├── _error/
■ 重要ルール
```

✔ 患者ごとに完結させる
✔ QRは必ず最後に撮影
✔ 診療時間中は起動したまま

# Photo Auto-Organization System

## What This Does

Automatically organizes clinical photos into folders by patient ID and date. Take photos, display a QR code on screen, photograph it as the last shot, and the system organizes everything.

---

## Step 1: Installation

**If you don't have uv installed:**

```
pip install uv
```

**Then install dependencies:**

```
uv sync
```

---

## Step 2: Setup Folder Path

1. Open **config.json**
2. Change `"watch_folder"` to your folder path
3. Save the file

Example:

```
"watch_folder": "E:\\temp\\dropbox\\test_photos"
```

---

## Step 3: Run the System

```
uv run python main.py
```

Keep this window open during work hours.

---

## How to Use (Daily Workflow)

### 1. Take Patient Photos

- Take all photos for ONE patient with the digital camera
- Photos should be saved to the watch folder

### 2. Display QR Code on Screen

- Open **qr-generator.html** in a browser (double-click it)
- Enter the patient ID
- Click "Generate QR Code"
- Use "Fullscreen QR" for a larger display on screen

### 3. Photograph the QR Code

- With the same camera, take a photo of the QR code displayed on screen
- This must be the **LAST** photo in the session
- The system detects the QR code in the photo and organizes all preceding photos

### Done!

Photos are automatically organized into: `PatientID/Date/photos`

---

## Result

```
Watch Folder/
├── 123456/
│   └── 2026.02.20/
│       ├── photo1.jpg
│       ├── photo2.jpg
│       ├── photo3.jpg
│       └── QR_photo.jpg        <- QR photo is kept
├── _backup/
│   └── 20260220_1430/
│       ├── photo1.jpg           <- backup copies
│       ├── photo2.jpg
│       ├── photo3.jpg
│       └── QR_photo.jpg
```

---

## Safety Features

- **Max photos**: Maximum 200 photos per session (configurable)
- **Time window**: Only photos within 60 minutes before QR photo are included (configurable)
- **Backup**: All photos are backed up before being moved
- **Error log**: Errors are logged and saved to `_error/` folder
- **No QR = No action**: Photos are never moved without a QR code trigger

---

## Configuration (config.json)

| Setting | Default | Description |
|---------|---------|-------------|
| `watch_folder` | (required) | Folder to monitor for photos |
| `max_photos_per_session` | 200 | Max photos per organization session |
| `max_minutes_window` | 60 | Time window in minutes before QR photo |
| `backup_folder_name` | `_backup` | Name of backup folder |
| `error_folder_name` | `_error` | Name of error folder |
| `log_file` | `photo_processor.log` | Log file path |
| `log_level` | `INFO` | Logging level |
| `supported_formats` | jpg, jpeg, png, gif, bmp | Supported image file extensions |

---

## Important Rules

- One patient at a time
- Keep the system running during work hours
- The QR photo must be the LAST photo taken
- Do not manually place files in `_backup` or `_error` folders
