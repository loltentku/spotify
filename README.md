# Spotify Personal Listening Lakehouse

This project started with a simple question: what do I actually listen to, and when?
To answer it, I built a data pipeline that pulls my Spotify history every day, adds genre tags from Last.fm,
processes everything on Databricks using a Bronze → Silver → Gold layout, and shows the results in a Power BI dashboard.

![Dashboard](dash.png)

## How it fits together

```
Spotify API ──┐
              ├─► Python ingestion ─► JSON landing ─► Databricks Volume
Last.fm API ──┘   (runs daily)                             │
                                                           ▼
                                     Bronze  ─►  Silver  ─►  Gold  ─►  Power BI
                                  (Auto Loader)  (clean)   (4 tables)  (DirectQuery)
```

- **Ingestion:** Python scripts pull recently played tracks, top tracks, top artists and playlists,
  and save them as raw, append-only JSON files partitioned by date. A Windows Task Scheduler job runs them daily.
- **Bronze:** loads the JSON into Delta tables with Auto Loader, incrementally, so old files are never re-read.
- **Silver:** flattens nested structs, fixes data types and removes duplicates.
- **Gold:** four analytics tables: genre mix, taste over time, listening hours, and a library overview.
- **Dashboard:** Power BI connects to a Databricks SQL warehouse and reads the Gold tables directly.

## What got in the way

**Spotify no longer returns artist genres,** and the audio-features endpoint returns 403 for newer apps.
I looked up each artist on Last.fm to get genre tags instead. That brought in some junk tags
(`all`, `female vocalists`), which have to be filtered out before picking the top 5 per artist,
otherwise they use up the slots. Tags that mean the same thing (`thai`, `thailand`, `t-pop`) are merged into one so a single genre isn't split across several bars.

**The Kaggle dataset can't be used to compare genres.** I originally planned to compare my taste with "the market,"
but the dataset is sampled roughly evenly across genres (114 genres, about 114,000 rows), so its genre shares say nothing about
what is actually popular. Last.fm tags and Kaggle genres are also different taxonomies, so I kept them separate instead of joining them.

**Spotify only returns the last 50 plays per request.** A day without a run means that day's history is gone for good,
so the landing zone is append-only and ingestion runs daily.

**Smaller problems:** the Kaggle CSV has rows where columns are shifted (track names with quotes), so I used `try_cast`
and filtered out the bad rows. Play times are converted from UTC to Bangkok time before counting by hour.
Power BI in DirectQuery mode rejects some DAX functions (such as `FORMAT`), so the hour labels are built with plain `IF` and `INT` instead.

## Dashboard

- KPIs: total playlists, average tracks per playlist, share of collaborative playlists, total plays
- Top 10 genres across the artists I listen to
- A heatmap of how my taste shifts across the last 4 weeks, 6 months and 12 months
- What time of day I listen (Bangkok time)

## Tech stack

Python (Spotipy, pandas) · Databricks (Delta Lake, Auto Loader, PySpark, Unity Catalog Volumes) ·
Last.fm API · Power BI · Windows Task Scheduler

