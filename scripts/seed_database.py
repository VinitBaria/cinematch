"""
CineMatch AI - Database Seed Script
Populates MongoDB with:
  1. Movies from processed CSV with ratings aggregated
  2. Demo user accounts (including known SVD user and fresh new user)
  3. Pre-loaded ratings for demo user
"""
import ast
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
from pymongo import MongoClient, UpdateOne

# Add paths
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.config import settings
from backend.app.database import connect_db
from backend.app.security.auth import hash_password

MOVIES_CSV = ROOT_DIR / "data" / "processed" / "movies_processed.csv"
RATINGS_CSV = ROOT_DIR / "data" / "processed" / "train_ratings.csv"

# High quality genre backdrop fallbacks for Netflix look
GENRE_BACKDROPS = {
    "Action": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=1200&auto=format&fit=crop&q=80",
    "Adventure": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1200&auto=format&fit=crop&q=80",
    "Animation": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=1200&auto=format&fit=crop&q=80",
    "Comedy": "https://images.unsplash.com/photo-1514306191717-452ec28c7814?w=1200&auto=format&fit=crop&q=80",
    "Crime": "https://images.unsplash.com/photo-1478760329108-5c3ed9d495a0?w=1200&auto=format&fit=crop&q=80",
    "Drama": "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=1200&auto=format&fit=crop&q=80",
    "Fantasy": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1200&auto=format&fit=crop&q=80",
    "Horror": "https://images.unsplash.com/photo-1509248961158-e54f6934749c?w=1200&auto=format&fit=crop&q=80",
    "Romance": "https://images.unsplash.com/photo-1518199266791-5375a83190b7?w=1200&auto=format&fit=crop&q=80",
    "Sci-Fi": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=1200&auto=format&fit=crop&q=80",
    "Thriller": "https://images.unsplash.com/photo-1478760329108-5c3ed9d495a0?w=1200&auto=format&fit=crop&q=80",
    "Default": "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=1200&auto=format&fit=crop&q=80",
}

# Curated high quality posters for top iconic movies
POPULAR_POSTERS = {
    1: "https://image.tmdb.org/t/p/w500/uXDfjJbdP4ijW5hWSBrPrlKpxab.jpg", # Toy Story
    2: "https://image.tmdb.org/t/p/w500/vgpX75Gvru6mgpA8Gz9UR119hoJ.jpg", # Jumanji
    260: "https://image.tmdb.org/t/p/w500/6FfCtAuVAW8XJjZ7eWeLibRLWTw.jpg", # Star Wars
    296: "https://image.tmdb.org/t/p/w500/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg", # Pulp Fiction
    318: "https://image.tmdb.org/t/p/w500/9cqNxx0GxF0bflZmeSMuL5tnGzr.jpg", # Shawshank Redemption
    356: "https://image.tmdb.org/t/p/w500/arw2vcBveWOVZr6pxd9XTd1TdQa.jpg", # Forrest Gump
    593: "https://image.tmdb.org/t/p/w500/uS9m8OBk1A8eM9I042bx8XXpqAq.jpg", # Silence of the Lambs
    2571: "https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg", # The Matrix
    2959: "https://image.tmdb.org/t/p/w500/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg", # Fight Club
    4993: "https://image.tmdb.org/t/p/w500/6oom5QYQ2yQTMJIbnvbkBL9cDK6.jpg", # LOTR Fellowship
    58559: "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg", # The Dark Knight
    79132: "https://image.tmdb.org/t/p/w500/oYuLEt3zVCKq57qu2F8dT7NIa6f.jpg", # Inception
    109487: "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg", # Interstellar
}


CACHE_PATH = ROOT_DIR / "data" / "processed" / "movie_posters_cache.json"
POSTERS_CACHE = {}
if CACHE_PATH.exists():
    try:
        import json
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            POSTERS_CACHE = {int(k): v for k, v in json.load(f).items()}
    except Exception:
        pass


def get_poster_url(movie_id: int, genres: list, title: str) -> str:
    if movie_id in POSTERS_CACHE:
        return POSTERS_CACHE[movie_id]
    if movie_id in POPULAR_POSTERS:
        return POPULAR_POSTERS[movie_id]
    first_genre = genres[0] if genres else "Default"
    fallback = GENRE_BACKDROPS.get(first_genre, GENRE_BACKDROPS["Default"])
    return fallback


def seed():
    print("🎬 Starting CineMatch AI Database Seeding...")
    db = connect_db()

    # 1. Load ratings aggregation
    print(f"Reading ratings from {RATINGS_CSV}...")
    ratings_df = pd.read_csv(RATINGS_CSV)
    stats = ratings_df.groupby("movieId").agg(
        avgRating=("rating", "mean"),
        ratingCount=("rating", "count"),
    ).reset_index()
    stats["avgRating"] = stats["avgRating"].round(2)
    stats_dict = stats.set_index("movieId").to_dict(orient="index")

    # 2. Load and insert movies
    print(f"Reading movies from {MOVIES_CSV}...")
    movies_df = pd.read_csv(MOVIES_CSV)
    
    operations = []
    for _, row in movies_df.iterrows():
        mid = int(row["movieId"])
        genres_raw = row.get("genreList", "[]")
        try:
            genres = ast.literal_eval(genres_raw) if isinstance(genres_raw, str) else list(genres_raw)
        except Exception:
            genres = [g.strip() for g in str(row.get("genres", "")).split("|") if g.strip()]

        st = stats_dict.get(mid, {"avgRating": None, "ratingCount": 0})
        title = str(row.get("title", ""))
        clean_title = str(row.get("cleanTitle", title))
        year = float(row["year"]) if pd.notnull(row.get("year")) else None
        tmdb_id = float(row["tmdbId"]) if pd.notnull(row.get("tmdbId")) else None
        poster_url = get_poster_url(mid, genres, title)
        overview = f"A compelling {', '.join(genres) if genres else 'cinematic'} film released in {int(year) if year else 'classic era'}."

        doc = {
            "movieId": mid,
            "title": title,
            "cleanTitle": clean_title,
            "year": year,
            "genres": genres,
            "genreList": genres,
            "tmdbId": tmdb_id,
            "posterUrl": poster_url,
            "overview": overview,
            "avgRating": st["avgRating"],
            "ratingCount": st["ratingCount"],
            "updatedAt": datetime.now(timezone.utc).isoformat(),
        }

        operations.append(UpdateOne({"movieId": mid}, {"$set": doc}, upsert=True))

        if len(operations) >= 1000:
            db.movies.bulk_write(operations)
            operations = []

    if operations:
        db.movies.bulk_write(operations)

    total_movies = db.movies.count_documents({})
    print(f"✅ Loaded {total_movies} movies into MongoDB!")

    # 3. Seed demo users
    print("Seeding demo users...")
    demo_users = [
        {
            "userId": 1,  # Known SVD user
            "name": "Demo Cinephile (Known SVD User)",
            "email": "demo@cinematch.ai",
            "hashedPassword": hash_password("password123"),
            "ratingCount": 0,
            "createdAt": datetime.now(timezone.utc).isoformat(),
        },
        {
            "userId": 999999,  # Fresh user for testing onboarding
            "name": "Alex Newbie (Cold Start User)",
            "email": "alex@cinematch.ai",
            "hashedPassword": hash_password("password123"),
            "ratingCount": 0,
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }
    ]

    for u in demo_users:
        db.users.update_one({"email": u["email"]}, {"$set": u}, upsert=True)
    print("✅ Demo user accounts ready:")
    print("   - demo@cinematch.ai / password123 (SVD user)")
    print("   - alex@cinematch.ai / password123 (Fresh cold start user)")

    # 4. Seed user ratings for demo user (User 1)
    print("Seeding ratings for User 1...")
    user1_ratings = ratings_df[ratings_df["userId"] == 1]
    rating_ops = []
    for _, r in user1_ratings.iterrows():
        rating_doc = {
            "userId": int(r["userId"]),
            "movieId": int(r["movieId"]),
            "rating": float(r["rating"]),
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat(),
        }
        rating_ops.append(
            UpdateOne(
                {"userId": rating_doc["userId"], "movieId": rating_doc["movieId"]},
                {"$set": rating_doc},
                upsert=True
            )
        )
    if rating_ops:
        db.ratings.bulk_write(rating_ops)
        db.users.update_one({"userId": 1}, {"$set": {"ratingCount": len(rating_ops)}})
        print(f"✅ Seeded {len(rating_ops)} ratings for demo user 1")

    print("\n🎉 Database seeding completed successfully!")


if __name__ == "__main__":
    seed()
