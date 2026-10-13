"""
src/enrich_artist_tags.py

อ่านชื่อศิลปินทั้งหมดที่เคยเจอใน landing zone (top_artists, top_tracks,
recently_played) แล้วไปดึง genre tag จาก Last.fm เขียนเป็น dataset ใหม่
`artist_tags` ใน landing zone รูปแบบเดียวกับ dataset อื่น

หลักการ:
- ดึงเฉพาะศิลปินที่ "ยังไม่เคยดึง" (ดูจากไฟล์ artist_tags ที่มีอยู่แล้ว)
  ทำให้รันซ้ำทุกวันได้ ยิง API เฉพาะศิลปินใหม่ที่เพิ่งเจอ
- เก็บ raw response จาก Last.fm ไว้ครบ ไม่กรอง tag ที่นี่ (เป็นงานของ Silver)
- ถ้าศิลปินคนไหนดึงไม่สำเร็จ (เครือข่ายมีปัญหา) จะข้ามไปก่อน
  รอบถัดไปจะลองใหม่เองเพราะยังไม่ถูกบันทึกว่าดึงแล้ว

ต้องมี LASTFM_API_KEY ในไฟล์ .env
"""

import json
import logging
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

from lastfm_client import fetch_artist_top_tags, polite_sleep
from spotify_client import utc_ingestion_timestamp

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

LANDING_ROOT = Path(__file__).resolve().parent.parent / "data" / "landing"
DATASET_NAME = "artist_tags"


def _read_json_files(dataset_dir: Path) -> list:
    """อ่านทุกไฟล์ JSON (array) ใน dataset หนึ่ง คืนเป็น list ของ record รวมกัน"""
    records: list = []
    for path in sorted(dataset_dir.glob("ingestion_date=*/*.json")):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            records.extend(data)
    return records


def collect_artist_names(landing_root: Path) -> set[str]:
    """รวบรวมชื่อศิลปินที่ไม่ซ้ำกันจาก dataset ใน landing zone ทั้งหมดที่มีชื่อศิลปินอยู่"""
    names: set[str] = set()

    # top_artists_*: แต่ละ record คือ artist object ตรงๆ
    for d in landing_root.glob("top_artists_*"):
        for artist in _read_json_files(d):
            if artist.get("name"):
                names.add(artist["name"])

    # top_tracks_*: แต่ละ record คือ track object มี artists[]
    for d in landing_root.glob("top_tracks_*"):
        for track in _read_json_files(d):
            for artist in track.get("artists", []) or []:
                if artist.get("name"):
                    names.add(artist["name"])

    # recently_played: record = {"track": {..., "artists": [...]}, "played_at": ...}
    rp_dir = landing_root / "recently_played"
    if rp_dir.exists():
        for item in _read_json_files(rp_dir):
            for artist in (item.get("track") or {}).get("artists", []) or []:
                if artist.get("name"):
                    names.add(artist["name"])

    return names


def already_fetched_names(landing_root: Path) -> set[str]:
    """ชื่อศิลปินที่เคยดึง tag สำเร็จแล้ว (อยู่ในไฟล์ artist_tags เดิม)"""
    dataset_dir = landing_root / DATASET_NAME
    if not dataset_dir.exists():
        return set()
    return {r["artist_name"] for r in _read_json_files(dataset_dir) if r.get("artist_name")}


def write_records(records: list[dict], ingestion_ts: str) -> Path:
    ingestion_date = ingestion_ts.split("T")[0]
    out_dir = LANDING_ROOT / DATASET_NAME / f"ingestion_date={ingestion_date}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"data_{ingestion_ts.replace('-', '').replace(':', '')}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    return out_file


def run() -> None:
    api_key = os.environ.get("LASTFM_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ไม่พบ LASTFM_API_KEY — ใส่ในไฟล์ .env "
            "(สมัครฟรีที่ https://www.last.fm/api/account/create)"
        )

    all_names = collect_artist_names(LANDING_ROOT)
    todo = sorted(all_names - already_fetched_names(LANDING_ROOT))
    logger.info(f"ศิลปินทั้งหมด {len(all_names)} คน, ต้องดึงใหม่ {len(todo)} คน")

    if not todo:
        logger.info("ไม่มีศิลปินใหม่ ข้ามการดึง")
        return

    ingestion_ts = utc_ingestion_timestamp()
    records: list[dict] = []
    failed = 0

    with requests.Session() as session:
        for name in todo:
            try:
                response = fetch_artist_top_tags(api_key, name, session=session)
            except requests.RequestException as e:
                failed += 1
                logger.warning(f"ดึงไม่สำเร็จ ({name}): {e}")
                continue

            records.append(
                {
                    "artist_name": name,
                    "fetched_at": ingestion_ts,
                    "response": response,
                }
            )
            polite_sleep()

    if records:
        path = write_records(records, ingestion_ts)
        logger.info(f"artist_tags: {len(records)} คน -> {path}")
    if failed:
        logger.warning(f"ข้าม {failed} คน (จะลองใหม่ในรอบถัดไป)")


if __name__ == "__main__":
    run()
