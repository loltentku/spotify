# Spotify Personal Listening Lakehouse

โปรเจกต์เก็บข้อมูลการฟังเพลงส่วนตัวจาก Spotify API เป็นไฟล์ JSON ใน landing zone
และเตรียม market dataset จาก Kaggle เพื่อใช้ต่อยอดการวิเคราะห์รสนิยมการฟังเพลง
เป้าหมายระยะถัดไปคือโหลดข้อมูลเข้า Medallion architecture (Bronze → Silver → Gold)
บน Databricks; ปัจจุบันส่วนที่ทำงานได้อยู่ใน local scripts ยังไม่มี Databricks notebooks/jobs
สำหรับ Silver, Gold หรือ orchestration

## สถานะ
- [x] Spotify OAuth และ local landing ingestion
- [x] Last.fm artist-tag enrichment
- [x] มี market CSV ใน local path และมีสคริปต์ตรวจสอบ schema/preview
- [ ] โหลด landing และ market data เข้า Databricks Bronze
- [ ] Silver: clean, deduplicate และ join ข้อมูล
- [ ] Gold: สร้าง aggregations และเปรียบเทียบ personal กับ market
- [ ] Databricks Workflows, Unity Catalog และ dashboard

## เริ่มใช้งาน

ต้องใช้ Python และ Spotify account ที่อนุญาตให้แอปเข้าถึงข้อมูลตาม scopes ด้านล่าง

1. สร้างแอปที่ [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   และเพิ่ม Redirect URI `http://127.0.0.1:8888/callback` ในการตั้งค่าแอป
2. สร้าง virtual environment และติดตั้ง dependencies (ตัวอย่าง PowerShell):
   ```bash
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```
3. คัดลอก `.env.example` เป็น `.env` แล้วกำหนด `SPOTIFY_CLIENT_ID`,
   `SPOTIFY_CLIENT_SECRET` และ `SPOTIFY_REDIRECT_URI` ให้ตรงกับแอปของคุณ
   สำหรับดึง artist tags ให้เพิ่ม `LASTFM_API_KEY` ด้วย (สมัคร API key ได้ที่
   [Last.fm API](https://www.last.fm/api/account/create))
4. ทดสอบการเชื่อมต่อ Spotify จากโฟลเดอร์โปรเจกต์:
   ```bash
   python src\auth.py
   ```
   ครั้งแรกจะเปิด browser ให้เข้าสู่ระบบและอนุญาต scopes `user-read-recently-played`,
   `user-top-read` และ `playlist-read-private` จากนั้น Spotipy จะเก็บ token cache
   ใน `.cache` ตาม working directory เพื่อ refresh token ในการรันครั้งถัดไป

## งานที่ทำได้ในปัจจุบัน

### Spotify landing ingestion

รันจากโฟลเดอร์โปรเจกต์หลังตั้งค่า OAuth แล้ว:

```bash
python src\ingest_landing.py
```

สคริปต์ดึง recently played, top tracks และ top artists สำหรับ `short_term`,
`medium_term`, `long_term` รวมถึง playlists แล้วเขียน raw JSON แบบ append-only
ลง `data/landing/<dataset>/ingestion_date=YYYY-MM-DD/` โดยใช้ UTC ingestion timestamp
ในชื่อไฟล์ ตัวอย่าง dataset คือ `recently_played`, `top_tracks_short_term`,
`top_artists_long_term` และ `playlists`

Spotify ให้ recently played ได้สูงสุด 50 รายการล่าสุดต่อ request จึงควรรันสม่ำเสมอ
เพื่อสะสมประวัติ ขณะนี้ไม่มี audio features: Spotify ปิด endpoint นี้สำหรับแอปที่สร้าง
หลังวันที่ 27 พฤศจิกายน 2024

### Artist tags จาก Last.fm

```bash
python src\enrich_artist_tags.py
```

สคริปต์รวบรวมชื่อศิลปินจาก top artists, top tracks และ recently played ใน landing
แล้วดึง raw top-tags response จาก Last.fm เฉพาะศิลปินที่ยังไม่เคยบันทึกสำเร็จ
ผลลัพธ์อยู่ที่ `data/landing/artist_tags/ingestion_date=YYYY-MM-DD/`
ศิลปินที่ request ล้มเหลวจะถูกลองใหม่ในรอบถัดไป ต้องกำหนด `LASTFM_API_KEY` ใน `.env`

### Market dataset

วางไฟล์ Kaggle CSV ที่ `data/market/raw/spotify_tracks.csv` แล้วตรวจสอบด้วย:

```bash
python src\verify_market_dataset.py
```

ตัวตรวจอ่านไฟล์ด้วย pandas, แสดงจำนวนแถว/คอลัมน์และตัวอย่างข้อมูล และแจ้งว่าพบ
คอลัมน์ `track_genre`, `artists`, `track_name`, `danceability`, `energy`, `valence`,
`tempo` และ `popularity` ครบหรือไม่ สคริปต์นี้เป็นเพียงการตรวจไฟล์ในเครื่อง
ไม่ได้นำ market data เข้า Databricks หรือแปลงข้อมูล

### ตั้งเวลารันบน Windows

มี batch script ที่ `scripts/run_ingestion.bat` สำหรับรัน ingestion และตามด้วย
artist-tag enrichment พร้อมบันทึก log รายวันไว้ใน `logs/` ก่อนใช้ Task Scheduler
ให้แก้ `PROJECT_DIR` และ `PYTHON_EXE` ต้นไฟล์ให้ตรงกับตำแหน่งโปรเจกต์และ Python
ของเครื่องคุณ สคริปต์เปลี่ยน working directory ไปที่ `src` ก่อนรัน ดังนั้น token
cache ของการรันแบบ batch จะอยู่ใน `src/.cache`; การยืนยันตัวตนครั้งแรกสำหรับงานที่ตั้งเวลา
ควรทำจาก `src` เช่น:

```bash
cd src
python auth.py
```

หากไม่มี `LASTFM_API_KEY` ส่วน enrichment จะบันทึกข้อผิดพลาดลง log แต่ exit code
ของ batch ยังคงสะท้อนผลของ Spotify ingestion หลัก

## โครงสร้างโปรเจค

```
.
├── data/
│   ├── landing/          # JSON จาก Spotify และ Last.fm แบ่งตาม ingestion_date
│   └── market/raw/       # spotify_tracks.csv จาก Kaggle
├── logs/                 # log จากการรันตามเวลา
├── scripts/
│   └── run_ingestion.bat  # Windows scheduled ingestion + enrichment
├── src/
│   ├── auth.py
│   ├── spotify_client.py
│   ├── ingest_landing.py
│   ├── lastfm_client.py
│   ├── enrich_artist_tags.py
│   └── verify_market_dataset.py
├── requirements.txt
└── .env.example
```

อย่า commit `.env` หรือ token cache; ทั้งสองอย่างมีข้อมูลลับและถูกระบุไว้ใน `.gitignore`
