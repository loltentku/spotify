"""
src/spotify_client.py

รวมฟังก์ชันดึงข้อมูลดิบจาก Spotify API แต่ละประเภท
แต่ละฟังก์ชันคืนค่าเป็น raw dict/list ตามที่ Spotify API ส่งมา
(ไม่แปลงอะไรทั้งสิ้น — หน้าที่ของ Bronze layer คือเก็บ raw as-is)
"""

from datetime import datetime, timezone
from typing import Any
from spotipy import Spotify


def fetch_recently_played(sp: Spotify, limit: int = 50) -> list[dict[str, Any]]:
    """
    ดึงประวัติการฟังล่าสุด — Spotify จำกัดไว้แค่ 50 รายการล่าสุดเท่านั้น
    (ไม่มี pagination ย้อนหลังไกลกว่านี้) จึงต้องรัน ingestion นี้ทุกวัน
    เพื่อสะสมประวัติไปเรื่อยๆ แทนที่จะดึงย้อนหลังทีเดียว
    """
    result = sp.current_user_recently_played(limit=limit)
    return result.get("items", [])


def fetch_top_tracks(sp: Spotify, time_range: str = "short_term", limit: int = 50) -> list[dict[str, Any]]:
    """
    ดึง top tracks ของผู้ใช้
    time_range: short_term (~4 สัปดาห์), medium_term (~6 เดือน), long_term (หลายปี)
    """
    result = sp.current_user_top_tracks(time_range=time_range, limit=limit)
    return result.get("items", [])


def fetch_top_artists(sp: Spotify, time_range: str = "short_term", limit: int = 50) -> list[dict[str, Any]]:
    """ดึง top artists ของผู้ใช้ ในช่วงเวลาเดียวกับ fetch_top_tracks"""
    result = sp.current_user_top_artists(time_range=time_range, limit=limit)
    return result.get("items", [])


def fetch_saved_playlists(sp: Spotify, limit: int = 50) -> list[dict[str, Any]]:
    """ดึงรายชื่อ playlist ทั้งหมดที่ผู้ใช้มี (ทั้งที่สร้างเองและ follow)"""
    result = sp.current_user_playlists(limit=limit)
    return result.get("items", [])



def utc_ingestion_timestamp() -> str:
    """timestamp กลางที่ทุก ingestion script ใช้ร่วมกัน เพื่อให้ partition ตรงกัน"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")