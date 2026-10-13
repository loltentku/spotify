"""
src/ingest_landing.py

สคริปต์หลักที่รันทุกวัน (เช่นผ่าน Task Scheduler / cron / Databricks Job)
ดึงข้อมูลดิบจาก Spotify API แล้วเขียนเป็นไฟล์ JSON ลง "landing zone"
(data/landing/) โดยแบ่ง partition ตามวันที่ที่ดึง (ingestion_date)

เหตุผลที่แยก landing zone ออกจาก Bronze Delta table:
- Auto Loader บน Databricks ถูกออกแบบมาให้อ่านไฟล์ที่ "ตกลงมา" ใน storage
  location เรื่อยๆ (append-only files) แล้ว incremental load เข้า Delta
  table เอง — เราจึงต้องมีจุดที่ "ทิ้งไฟล์ดิบ" ก่อนเสมอ
- แยกความรับผิดชอบชัดเจน: สคริปต์นี้ทำหน้าที่แค่ "ดึงข้อมูล" ส่วน
  Bronze notebook (บน Databricks) ทำหน้าที่ "โหลดเข้า Delta table"

โครงสร้างไฟล์ที่ได้:
    data/landing/
      recently_played/ingestion_date=2026-09-27/data_20260927T101530.json
      top_tracks/ingestion_date=2026-09-27/data_20260927T101530.json
      top_artists/ingestion_date=2026-09-27/data_20260927T101530.json
      playlists/ingestion_date=2026-09-27/data_20260927T101530.json

หมายเหตุ: ไม่มี audio_features เพราะ Spotify ปิด endpoint นี้ถาวร
สำหรับ App ที่สร้างหลัง 27 พ.ย. 2024 (คืนค่า 403 เสมอ ไม่มีทางแก้)
วิเคราะห์รสนิยมเพลงจึงใช้ genre จาก top_artists แทน
"""

import json
import logging
from pathlib import Path

from auth import get_spotify_client
from spotify_client import (
    fetch_recently_played,
    fetch_top_tracks,
    fetch_top_artists,
    fetch_saved_playlists,
    utc_ingestion_timestamp,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

LANDING_ROOT = Path(__file__).resolve().parent.parent / "data" / "landing"


def write_json(dataset_name: str, records: list[dict], ingestion_ts: str) -> Path:
    """
    เขียน records เป็นไฟล์ JSON ลง landing zone แบ่ง partition ตามวันที่
    คืนค่า path ของไฟล์ที่เขียน (ใช้ log ตรวจสอบ)
    """
    ingestion_date = ingestion_ts.split("T")[0]
    out_dir = LANDING_ROOT / dataset_name / f"ingestion_date={ingestion_date}"
    out_dir.mkdir(parents=True, exist_ok=True)

    out_file = out_dir / f"data_{ingestion_ts.replace('-', '').replace(':', '')}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    return out_file


def run() -> None:
    sp = get_spotify_client()
    ingestion_ts = utc_ingestion_timestamp()
    logger.info(f"เริ่ม ingestion รอบ {ingestion_ts}")

    # 1. Recently played — ต้องดึงทุกวันเพราะ Spotify เก็บแค่ 50 รายการล่าสุด
    recently_played = fetch_recently_played(sp)
    path = write_json("recently_played", recently_played, ingestion_ts)
    logger.info(f"recently_played: {len(recently_played)} รายการ -> {path}")

    # 2. Top tracks/artists — ดึงทั้ง 3 time range เก็บไว้เปรียบเทียบ trend
    for time_range in ["short_term", "medium_term", "long_term"]:
        top_tracks = fetch_top_tracks(sp, time_range=time_range)
        path = write_json(f"top_tracks_{time_range}", top_tracks, ingestion_ts)
        logger.info(f"top_tracks_{time_range}: {len(top_tracks)} รายการ -> {path}")

        top_artists = fetch_top_artists(sp, time_range=time_range)
        path = write_json(f"top_artists_{time_range}", top_artists, ingestion_ts)
        logger.info(f"top_artists_{time_range}: {len(top_artists)} รายการ -> {path}")

    # 3. Playlists
    playlists = fetch_saved_playlists(sp)
    path = write_json("playlists", playlists, ingestion_ts)
    logger.info(f"playlists: {len(playlists)} รายการ -> {path}")

    logger.info("ingestion เสร็จสมบูรณ์")


if __name__ == "__main__":
    run()