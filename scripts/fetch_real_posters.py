"""
CineMatch AI - Real Movie Posters Fetcher & Database Updater
Fetches real movie posters using:
  1. Pre-curated MovieLens Amazon/IMDb poster archive (1,592 posters)
  2. The Movie Database (TMDB) API for popular and trending titles
Updates MongoDB with official high-resolution movie cover art.
"""
import sys
import json
import concurrent.futures
from pathlib import Path

# Fix Windows console encoding
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd
import requests
from pymongo import MongoClient, UpdateOne

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.config import settings
from backend.app.database import connect_db

TMDB_API_KEY = "8265bd1679663a7ea12ac168da84d2e8"
CACHE_PATH = ROOT_DIR / "data" / "processed" / "movie_posters_cache.json"
IMDB_POSTERS_URL = "https://raw.githubusercontent.com/babu-thomas/movielens-posters/master/movie_poster.csv"


def fetch_tmdb_poster(item):
    movie_id, tmdb_id = item
    if not tmdb_id or pd.isna(tmdb_id):
        return movie_id, None, None
    try:
        url = f"https://api.themoviedb.org/3/movie/{int(tmdb_id)}?api_key={TMDB_API_KEY}&language=en-US"
        r = requests.get(url, timeout=4)
        if r.status_code == 200:
            data = r.json()
            poster_path = data.get("poster_path")
            backdrop_path = data.get("backdrop_path")
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
            backdrop_url = f"https://image.tmdb.org/t/p/w1280{backdrop_path}" if backdrop_path else None
            return movie_id, poster_url, backdrop_url
    except Exception:
        pass
    return movie_id, None, None


def main():
    print("🎬 Starting Real Movie Poster Enrichment...")
    db = connect_db()

    posters_map = {}

    # 1. Load local cache if exists
    if CACHE_PATH.exists():
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                posters_map = json.load(f)
                # keys might be strings
                posters_map = {int(k): v for k, v in posters_map.items()}
            print(f"Loaded {len(posters_map)} posters from local cache")
        except Exception as e:
            print(f"Cache load error: {e}")

    # 2. Download Amazon/IMDb movie_poster.csv
    print("Fetching MovieLens Amazon/IMDb poster archive...")
    try:
        imdb_df = pd.read_csv(IMDB_POSTERS_URL, header=None, names=["movieId", "posterUrl"])
        for _, row in imdb_df.iterrows():
            mid = int(row["movieId"])
            purl = str(row["posterUrl"]).strip()
            if purl and purl.startswith("http") and mid not in posters_map:
                posters_map[mid] = purl
        print(f"Total posters after IMDb archive: {len(posters_map)}")
    except Exception as e:
        print(f"Error fetching IMDb archive: {e}")

    # 3. Query TMDB for top rated and popular movies in database
    movies_cursor = db.movies.find(
        {"tmdbId": {"$ne": None}},
        {"movieId": 1, "tmdbId": 1, "ratingCount": 1}
    ).sort("ratingCount", -1).limit(600)

    tmdb_tasks = []
    for doc in movies_cursor:
        mid = doc["movieId"]
        # If not present or we want high-res TMDB poster
        if mid not in posters_map or "images-na" in str(posters_map.get(mid, "")):
            tmdb_tasks.append((mid, doc.get("tmdbId")))

    print(f"Fetching {len(tmdb_tasks)} official TMDB posters via multi-threading...")
    updated_from_tmdb = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(fetch_tmdb_poster, tmdb_tasks)
        for mid, poster_url, _ in results:
            if poster_url:
                posters_map[mid] = poster_url
                updated_from_tmdb += 1

    print(f"Enriched {updated_from_tmdb} posters directly from TMDB!")

    # 4. Save cache to disk
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(posters_map, f)
    print(f"Saved {len(posters_map)} posters to {CACHE_PATH}")

    # 5. Bulk update MongoDB
    print("Updating MongoDB movie records with real poster URLs...")
    bulk_ops = []
    for mid, purl in posters_map.items():
        bulk_ops.append(
            UpdateOne(
                {"movieId": mid},
                {"$set": {"posterUrl": purl}}
            )
        )
        if len(bulk_ops) >= 500:
            db.movies.bulk_write(bulk_ops)
            bulk_ops = []

    if bulk_ops:
        db.movies.bulk_write(bulk_ops)

    print("🎉 All movies in MongoDB have been updated with real posters!")


if __name__ == "__main__":
    main()
