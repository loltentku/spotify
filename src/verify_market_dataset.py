"""
src/verify_market_dataset.py

ตรวจสอบไฟล์ Kaggle market dataset ที่ดาวน์โหลดมาว่า:
1. หาไฟล์เจอไหม (path ถูกต้อง)
2. อ่านด้วย pandas ได้ไหม (ไม่มีปัญหา encoding/format)
3. มี column ที่ pipeline ต้องใช้ครบไหม (genre, audio features)
4. ให้ preview ข้อมูลคร่าวๆ เพื่อเช็คด้วยตา

รันครั้งเดียวหลังโหลดไฟล์มาวาง ไม่ต้องรันซ้ำทุกวัน (market dataset
เป็น one-time batch load ไม่เหมือนฝั่ง Spotify ที่ต้องรันทุกวัน)
"""

import sys
from pathlib import Path

import pandas as pd

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "market" / "raw" / "spotify_tracks.csv"

# Column ที่ pipeline คาดว่าจะต้องใช้ใน Silver/Gold layer ภายหลัง
# (ชื่อ column อาจต่างกันเล็กน้อยตามเวอร์ชัน dataset บน Kaggle จึงต้อง verify ก่อน)
EXPECTED_COLUMNS = [
    "track_genre",
    "artists",
    "track_name",
    "danceability",
    "energy",
    "valence",
    "tempo",
    "popularity",
]


def verify() -> None:
    if not CSV_PATH.exists():
        print(f"❌ ไม่พบไฟล์ที่ {CSV_PATH}")
        print("   ตรวจสอบว่าวางไฟล์ตาม path ที่กำหนดแล้วหรือยัง")
        sys.exit(1)

    print(f"✅ พบไฟล์ที่ {CSV_PATH}")

    try:
        df = pd.read_csv(CSV_PATH)
    except Exception as e:
        print(f"❌ อ่านไฟล์ไม่ได้: {e}")
        sys.exit(1)

    print(f"✅ อ่านไฟล์สำเร็จ: {len(df):,} แถว, {len(df.columns)} คอลัมน์")
    print(f"\nรายชื่อคอลัมน์ทั้งหมด:\n{list(df.columns)}")

    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        print(f"\n⚠️  ไม่พบคอลัมน์ที่คาดไว้: {missing}")
        print("   อาจเป็นเพราะ Kaggle เปลี่ยนชื่อคอลัมน์ในเวอร์ชันใหม่ — ต้องเช็คชื่อจริงแล้วปรับโค้ดขั้นต่อไป")
    else:
        print("\n✅ มีคอลัมน์ที่ต้องใช้ครบทุกตัว")

    print("\nตัวอย่างข้อมูล 5 แถวแรก:")
    preview_cols = [c for c in EXPECTED_COLUMNS if c in df.columns][:5]
    print(df[preview_cols].head().to_string())

    if "track_genre" in df.columns:
        n_genres = df["track_genre"].nunique()
        print(f"\nจำนวนแนวเพลง (genre) ที่ไม่ซ้ำกัน: {n_genres}")


if __name__ == "__main__":
    verify()