# Spotify Personal Listening Lakehouse

Medallion architecture pipeline (Bronze → Silver → Gold) บน Databricks
ที่ดึงข้อมูลการฟังเพลงส่วนตัวจาก Spotify API เปรียบเทียบกับ market
dataset (Kaggle) เพื่อวิเคราะห์รสนิยมการฟังเพลง

## สถานะโปรเจค
- [x] Step 1: Project setup + Spotify OAuth authentication
- [ ] Step 2: Bronze layer ingestion (recently played, top items, audio features)
- [ ] Step 3: Kaggle market dataset ingestion
- [ ] Step 4: Silver layer (clean, dedupe, join)
- [ ] Step 5: Gold layer (aggregations, personal vs market comparison)
- [ ] Step 6: Databricks Workflows orchestration
- [ ] Step 7: Unity Catalog setup + dashboard

## Setup (Step 1)

1. สร้าง Spotify App ที่ https://developer.spotify.com/dashboard
   - Redirect URI: `http://localhost:8888/callback`
2. คัดลอก `.env.example` เป็น `.env` แล้วใส่ Client ID/Secret ของคุณ
3. ติดตั้ง dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. ทดสอบ authentication:
   ```bash
   python src/auth.py
   ```
   ครั้งแรกจะเปิด browser ให้ login Spotify — หลังจากนั้น token จะถูก
   cache ไว้ที่ `.cache` ทำให้ script อื่นๆ (bronze ingestion) รันต่อ
   ได้โดยไม่ต้อง login ใหม่ทุกครั้ง

## โครงสร้างโปรเจค
```
spotify-lakehouse-pipeline/
├── config/          # การตั้งค่า schema, table names
├── notebooks/        # Databricks notebooks (bronze/silver/gold)
├── src/              # โค้ด Python ที่ใช้ร่วมกัน (auth, API clients)
├── docs/              # architecture diagram, screenshots
├── requirements.txt
└── .env.example
```
