@echo off

SET PROJECT_DIR=C:\Users\User\Downloads\spotify
SET PYTHON_EXE=C:\Users\User\AppData\Local\Programs\Python\Python313\python.exe

SET LOG_DIR=%PROJECT_DIR%\logs
IF NOT EXIST "%LOG_DIR%" MKDIR "%LOG_DIR%"

FOR /F "tokens=1-3 delims=/ " %%a IN ('date /t') DO SET TODAY=%%c-%%a-%%b
SET LOG_FILE=%LOG_DIR%\ingestion_%TODAY%.log

cd /d "%PROJECT_DIR%\src"
"%PYTHON_EXE%" ingest_landing.py >> "%LOG_FILE%" 2>&1
SET INGEST_EXIT=%ERRORLEVEL%

REM ดึง genre tag ของศิลปินใหม่จาก Last.fm (ต้องมี LASTFM_API_KEY ใน .env)
REM รันหลัง ingestion เสมอ และไม่กระทบ exit code ของ ingestion หลัก
"%PYTHON_EXE%" enrich_artist_tags.py >> "%LOG_FILE%" 2>&1

REM exit code ของ ingestion หลักส่งต่อให้ Task Scheduler รู้ว่าสำเร็จหรือ fail
EXIT /B %INGEST_EXIT%