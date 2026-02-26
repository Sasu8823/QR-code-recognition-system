import os
import sys
import json
import time
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List

import cv2
from pyzbar import pyzbar
from PIL import Image
from PIL.ExifTags import TAGS
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class PhotoProcessor:
    def __init__(self, config_path: str = "config.json"):
        self.config = self.load_config(config_path)
        self.watch_folder = Path(self.config['watch_folder'])

        self.max_photos_per_session = self.config.get('max_photos_per_session', 200)
        self.max_minutes_window = self.config.get('max_minutes_window', 60)
        self.startup_scan_minutes = self.config.get('startup_scan_minutes', 30)

        self.backup_folder_name = self.config.get('backup_folder_name', '_backup')
        self.error_folder_name = self.config.get('error_folder_name', '_error')
        self.done_folder_name = self.config.get('done_folder_name', '_done')

        self.stop_on_error = self.config.get('stop_on_error', True)

        self.stop_requested = False

        self.setup_logging()

        if not self.watch_folder.exists():
            raise FileNotFoundError(f"Watch folder not found: {self.watch_folder}")

        self.logger.info("Photo Processor initialized")

    def load_config(self, config_path: str) -> dict:
        with open(config_path, 'r') as f:
            return json.load(f)

    def setup_logging(self):
        log_file = self.config.get('log_file', 'photo_processor.log')
        log_level = getattr(logging, self.config.get('log_level', 'INFO').upper())

        self.logger = logging.getLogger('PhotoProcessor')
        self.logger.setLevel(log_level)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        console_handler = logging.StreamHandler()

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def is_image_file(self, path: Path) -> bool:
        return path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']

    def get_image_timestamp(self, path: Path) -> datetime:
        try:
            image = Image.open(path)
            exif = image._getexif()
            if exif:
                for tag_id, value in exif.items():
                    if TAGS.get(tag_id) in ['DateTimeOriginal', 'DateTime']:
                        return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
        except:
            pass
        return datetime.fromtimestamp(path.stat().st_mtime)

    def detect_qr(self, path: Path) -> Optional[str]:
        image = cv2.imread(str(path))
        if image is None:
            return None
        codes = pyzbar.decode(image)
        if not codes:
            return None
        data = codes[0].data.decode('utf-8')
        if data.startswith("PATIENT_ID:"):
            return data.replace("PATIENT_ID:", "").strip()
        return data.strip()

    def _collect_session_photos(self, qr_time: datetime, qr_path: Path):
        cutoff = qr_time - timedelta(minutes=self.max_minutes_window)
        photos = []
        for f in self.watch_folder.iterdir():
            if not f.is_file():
                continue
            if f.name.startswith('_'):
                continue
            if not self.is_image_file(f):
                continue
            if f == qr_path:
                continue
            ts = self.get_image_timestamp(f)
            if cutoff <= ts <= qr_time:
                photos.append(f)
        photos.sort(key=lambda p: self.get_image_timestamp(p))
        return photos

    def _backup(self, session_id, photos, qr_photo, patient_id):
        backup_dir = self.watch_folder / self.backup_folder_name / session_id
        backup_dir.mkdir(parents=True, exist_ok=True)

        for p in photos:
            shutil.copy2(str(p), str(backup_dir / p.name))
        shutil.copy2(str(qr_photo), str(backup_dir / f"QR_{patient_id}{qr_photo.suffix}"))

    def _write_done(self, session_id, patient_id, count):
        done_dir = self.watch_folder / self.done_folder_name
        done_dir.mkdir(parents=True, exist_ok=True)
        with open(done_dir / f"done_{session_id}_{patient_id}.txt", "w", encoding="utf-8") as f:
            f.write(f"Patient: {patient_id}\nFiles moved: {count}\nCompleted: {datetime.now()}\n")

    def _write_error(self, session_id, patient_id, error):
        error_dir = self.watch_folder / self.error_folder_name
        error_dir.mkdir(parents=True, exist_ok=True)
        with open(error_dir / f"error_{session_id}.txt", "w", encoding="utf-8") as f:
            f.write(str(error))

    def organize(self, patient_id, photos, qr_photo, qr_time):
        date_folder = qr_time.strftime("%Y.%m.%d")
        dest = self.watch_folder / patient_id / date_folder
        dest.mkdir(parents=True, exist_ok=True)

        moved = 0
        for i, p in enumerate(photos):
            new_name = f"{i+1:03d}{p.suffix}"
            shutil.move(str(p), str(dest / new_name))
            moved += 1

        shutil.move(str(qr_photo), str(dest / f"QR_{patient_id}{qr_photo.suffix}"))
        moved += 1
        return moved

    def process_qr(self, qr_path: Path, patient_id: str):
        qr_time = self.get_image_timestamp(qr_path)
        session_id = qr_time.strftime("%Y%m%d_%H%M%S")

        try:
            photos = self._collect_session_photos(qr_time, qr_path)

            if len(photos) > self.max_photos_per_session:
                raise Exception("Too many photos in session")

            self._backup(session_id, photos, qr_path, patient_id)
            moved = self.organize(patient_id, photos, qr_path, qr_time)
            self._write_done(session_id, patient_id, moved)

            self.logger.info(f"OK patient={patient_id} count={moved} session={session_id}")

        except Exception as e:
            self.logger.error(str(e))
            self._write_error(session_id, patient_id, e)
            if self.stop_on_error:
                self.stop_requested = True

    def scan_startup(self):
        cutoff = datetime.now() - timedelta(minutes=self.startup_scan_minutes)
        for f in self.watch_folder.iterdir():
            if f.is_file() and self.is_image_file(f):
                if self.get_image_timestamp(f) >= cutoff:
                    pid = self.detect_qr(f)
                    if pid:
                        self.process_qr(f, pid)

    def run(self):
        self.scan_startup()

        event_handler = PhotoEventHandler(self)
        observer = Observer()
        observer.schedule(event_handler, str(self.watch_folder), recursive=False)
        observer.start()

        try:
            while not self.stop_requested:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

        observer.stop()
        observer.join()


class PhotoEventHandler(FileSystemEventHandler):
    def __init__(self, processor):
        self.processor = processor

    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        time.sleep(2)
        if self.processor.is_image_file(path):
            pid = self.processor.detect_qr(path)
            if pid:
                self.processor.process_qr(path, pid)


if __name__ == "__main__":
    processor = PhotoProcessor()
    processor.run()