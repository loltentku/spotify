"""
src/lastfm_client.py

ดึง genre tag ของศิลปินจาก Last.fm API (artist.getTopTags)

ทำไมต้องใช้ Last.fm: Spotify เอา field `genres` ออกจาก artist object แล้ว
(การเปลี่ยนแปลง API เดือน ก.พ. 2026) จึงต้องหา genre จากแหล่งอื่น

หมายเหตุ: ฟังก์ชันนี้คืนค่า raw response จาก Last.fm ตามที่ได้รับ
ไม่กรอง/ไม่ normalize tag — หน้าที่นั้นเป็นของ Silver layer
"""

import time
from typing import Any

import requests

LASTFM_URL = "https://ws.audioscrobbler.com/2.0/"


def fetch_artist_top_tags(
    api_key: str,
    artist_name: str,
    session: requests.Session | None = None,
    timeout: int = 15,
) -> dict[str, Any]:
    """
    คืนค่า raw JSON จาก artist.getTopTags
    ถ้าไม่เจอศิลปิน Last.fm จะคืน {"error": 6, "message": "..."} ซึ่งเราเก็บไว้ตามนั้น
    (ให้ Silver layer ตัดสินใจเองว่าจะจัดการยังไง) แต่ถ้า HTTP/เครือข่ายมีปัญหา
    จะ raise exception เพื่อให้ผู้เรียกข้ามศิลปินคนนั้นไปก่อน
    """
    http = session or requests
    response = http.get(
        LASTFM_URL,
        params={
            "method": "artist.gettoptags",
            "artist": artist_name,
            "api_key": api_key,
            "autocorrect": 1,
            "format": "json",
        },
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def polite_sleep(seconds: float = 0.25) -> None:
    """หน่วงเวลาเล็กน้อยระหว่าง request เพื่อไม่ยิง Last.fm ถี่เกินไป"""
    time.sleep(seconds)
