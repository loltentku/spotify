"""
src/auth.py

จัดการ Spotify OAuth authentication สำหรับ pipeline นี้

ทำไมใช้ spotipy แทนเรียก raw API เอง:
- จัดการ token refresh อัตโนมัติให้ (access token หมดอายุทุก 1 ชม.)
- cache token ไว้ที่ .cache ทำให้รันซ้ำ (เช่น จาก Databricks Job ทุกวัน)
  โดยไม่ต้อง login ใหม่ทุกครั้ง — สำคัญมากเพราะ pipeline นี้ต้องรัน
  unattended (ไม่มีคนคอยกด login ทุกวัน)

การใช้งานครั้งแรก:
    python src/auth.py
จะเปิด browser ให้ login Spotify ครั้งเดียว หลังจากนั้น refresh token
จะถูกเก็บไว้ใน .cache และสคริปต์อื่นๆ (ingest_bronze.py) จะใช้ต่อได้เลย
โดยไม่ต้อง interactive login อีก
"""

import os
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
import spotipy

load_dotenv()

# Scope ที่ pipeline นี้ต้องใช้ — ขอเท่าที่จำเป็น (principle of least privilege)
SCOPES = " ".join([
    "user-read-recently-played",
    "user-top-read",
    "playlist-read-private",
])


def get_spotify_client() -> spotipy.Spotify:
    """
    คืนค่า authenticated Spotify client พร้อมใช้งาน
    ใช้ฟังก์ชันนี้จากทุกสคริปต์ที่ต้องเรียก Spotify API
    """
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.environ.get("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")

    if not client_id or not client_secret:
        raise EnvironmentError(
            "ไม่พบ SPOTIFY_CLIENT_ID หรือ SPOTIFY_CLIENT_SECRET — "
            "ตรวจสอบว่าคัดลอก .env.example เป็น .env และใส่ค่าแล้ว"
        )

    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=SCOPES,
        cache_path=".cache",  # เก็บ refresh token ไว้ที่นี่ (อยู่ใน .gitignore แล้ว)
        open_browser=True,
    )

    return spotipy.Spotify(auth_manager=auth_manager)


def verify_connection() -> None:
    """ทดสอบว่า auth ผ่านจริง โดยดึงข้อมูล profile ตัวเองมาแสดง"""
    sp = get_spotify_client()
    me = sp.current_user()
    print(f"✅ เชื่อมต่อสำเร็จ ล็อกอินในชื่อ: {me['display_name']} (id: {me['id']})")
    print(f"   Product tier: {me.get('product', 'unknown')}")
    print(f"   Followers: {me.get('followers', {}).get('total', 0)}")


if __name__ == "__main__":
    verify_connection()
