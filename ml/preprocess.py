"""
CineMatch AI - Data Preprocessing
Loads MovieLens CSVs, validates, cleans, and creates chronological
train / validation / test splits. Saves processed files and statistics.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

# Fix Windows console encoding
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml.config import (
    RATINGS_CSV,
    MOVIES_CSV,
    LINKS_CSV,
    RATINGS_REQUIRED_COLS,
    MOVIES_REQUIRED_COLS,
    LINKS_REQUIRED_COLS,
    MIN_RATING,
    MAX_RATING,
    RATING_STEP,
    TRAIN_RATIO,
    VALIDATION_RATIO,
    TRAIN_DATA_PATH,
    VALIDATION_DATA_PATH,
    TEST_DATA_PATH,
    MOVIES_PROCESSED_PATH,
    DATASET_STATS_PATH,
    ID_MAPPINGS_PATH,
    PROCESSED_DATA_DIR,
    APP_USER_ID_OFFSET,
    RANDOM_SEED,
)


def load_and_validate_ratings(path: Path) -> pd.DataFrame:
    """Load ratings.csv and validate schema and value ranges."""
    print("📊 Loading ratings.csv...")
    df = pd.read_csv(path)

    # Check required columns
    missing = set(RATINGS_REQUIRED_COLS) - set(df.columns)
    if missing:
        raise ValueError(f"ratings.csv missing columns: {missing}")

    initial_count = len(df)
    print(f"   Raw rows: {initial_count:,}")

    # Drop rows with nulls in required columns
    df = df.dropna(subset=RATINGS_REQUIRED_COLS)

    # Validate types
    df["userId"] = df["userId"].astype(int)
    df["movieId"] = df["movieId"].astype(int)
    df["rating"] = df["rating"].astype(float)
    df["timestamp"] = df["timestamp"].astype(int)

    # Validate rating range
    valid_ratings = (df["rating"] >= MIN_RATING) & (df["rating"] <= MAX_RATING)
    invalid_count = (~valid_ratings).sum()
    if invalid_count > 0:
        print(f"   ⚠️  Removing {invalid_count} ratings outside [{MIN_RATING}, {MAX_RATING}]")
        df = df[valid_ratings]

    # Validate rating step (0.5 increments)
    valid_steps = (df["rating"] % RATING_STEP == 0)
    invalid_steps = (~valid_steps).sum()
    if invalid_steps > 0:
        print(f"   ⚠️  Removing {invalid_steps} ratings not in {RATING_STEP} increments")
        df = df[valid_steps]

    # Handle duplicate (userId, movieId) — keep latest by timestamp
    before_dedup = len(df)
    df = df.sort_values("timestamp").drop_duplicates(
        subset=["userId", "movieId"], keep="last"
    )
    dupes_removed = before_dedup - len(df)
    if dupes_removed > 0:
        print(f"   ⚠️  Removed {dupes_removed} duplicate user-movie ratings (kept latest)")

    final_count = len(df)
    removed = initial_count - final_count
    print(f"   ✅ Clean rows: {final_count:,} (removed {removed})")

    return df.reset_index(drop=True)


def load_and_validate_movies(path: Path) -> pd.DataFrame:
    """Load movies.csv and validate."""
    print("🎬 Loading movies.csv...")
    df = pd.read_csv(path)

    missing = set(MOVIES_REQUIRED_COLS) - set(df.columns)
    if missing:
        raise ValueError(f"movies.csv missing columns: {missing}")

    df = df.dropna(subset=["movieId", "title"])
    df["movieId"] = df["movieId"].astype(int)

    # Extract year from title like "Toy Story (1995)"
    df["year"] = df["title"].str.extract(r"\((\d{4})\)").astype(float)
    df["cleanTitle"] = df["title"].str.replace(r"\s*\(\d{4}\)\s*$", "", regex=True).str.strip()

    # Parse genres
    df["genreList"] = df["genres"].apply(
        lambda g: g.split("|") if pd.notna(g) and g != "(no genres listed)" else []
    )

    print(f"   ✅ Movies loaded: {len(df):,}")
    return df


def load_and_validate_links(path: Path) -> pd.DataFrame:
    """Load links.csv for TMDB ID mapping."""
    print("🔗 Loading links.csv...")
    df = pd.read_csv(path)

    missing = set(LINKS_REQUIRED_COLS) - set(df.columns)
    if missing:
        raise ValueError(f"links.csv missing columns: {missing}")

    df["movieId"] = df["movieId"].astype(int)
    # tmdbId may have NaN
    df["tmdbId"] = pd.to_numeric(df["tmdbId"], errors="coerce")

    print(f"   ✅ Links loaded: {len(df):,}")
    return df


def chronological_split(
    ratings: pd.DataFrame,
    train_ratio: float,
    val_ratio: float,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split ratings chronologically per user.
    Each user's ratings are sorted by timestamp, then the first train_ratio
    go to train, next val_ratio to validation, remainder to test.
    This prevents data leakage from future ratings into training.
    """
    print("✂️  Creating chronological train/val/test splits...")

    train_parts = []
    val_parts = []
    test_parts = []

    for user_id, user_df in ratings.groupby("userId"):
        user_sorted = user_df.sort_values("timestamp")
        n = len(user_sorted)

        train_end = max(1, int(n * train_ratio))
        val_end = max(train_end + 1, int(n * (train_ratio + val_ratio)))

        train_parts.append(user_sorted.iloc[:train_end])
        val_parts.append(user_sorted.iloc[train_end:val_end])
        test_parts.append(user_sorted.iloc[val_end:])

    train = pd.concat(train_parts, ignore_index=True)
    val = pd.concat(val_parts, ignore_index=True)
    test = pd.concat(test_parts, ignore_index=True)

    print(f"   Train: {len(train):,} ratings")
    print(f"   Validation: {len(val):,} ratings")
    print(f"   Test: {len(test):,} ratings")
    print(f"   Total: {len(train) + len(val) + len(test):,}")

    return train, val, test


def compute_statistics(
    ratings: pd.DataFrame,
    movies: pd.DataFrame,
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
) -> dict:
    """Compute and return dataset statistics."""
    stats = {
        "total_ratings": int(len(ratings)),
        "total_users": int(ratings["userId"].nunique()),
        "total_movies": int(ratings["movieId"].nunique()),
        "total_movies_catalog": int(len(movies)),
        "rating_range": [float(MIN_RATING), float(MAX_RATING)],
        "mean_rating": float(ratings["rating"].mean()),
        "median_rating": float(ratings["rating"].median()),
        "std_rating": float(ratings["rating"].std()),
        "sparsity": float(
            1.0 - len(ratings)
            / (ratings["userId"].nunique() * ratings["movieId"].nunique())
        ),
        "ratings_per_user": {
            "mean": float(ratings.groupby("userId").size().mean()),
            "median": float(ratings.groupby("userId").size().median()),
            "min": int(ratings.groupby("userId").size().min()),
            "max": int(ratings.groupby("userId").size().max()),
        },
        "ratings_per_movie": {
            "mean": float(ratings.groupby("movieId").size().mean()),
            "median": float(ratings.groupby("movieId").size().median()),
            "min": int(ratings.groupby("movieId").size().min()),
            "max": int(ratings.groupby("movieId").size().max()),
        },
        "splits": {
            "train": int(len(train)),
            "validation": int(len(val)),
            "test": int(len(test)),
        },
        "timestamp_range": {
            "min": int(ratings["timestamp"].min()),
            "max": int(ratings["timestamp"].max()),
            "min_date": datetime.fromtimestamp(
                ratings["timestamp"].min(), tz=timezone.utc
            ).isoformat(),
            "max_date": datetime.fromtimestamp(
                ratings["timestamp"].max(), tz=timezone.utc
            ).isoformat(),
        },
        "app_user_id_offset": APP_USER_ID_OFFSET,
        "max_movielens_user_id": int(ratings["userId"].max()),
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }
    return stats


def create_id_mappings(ratings: pd.DataFrame, movies: pd.DataFrame) -> dict:
    """
    Create mappings to prevent ID collisions.
    MovieLens userIds stay as-is in the model.
    Application users get IDs starting at APP_USER_ID_OFFSET.
    """
    movielens_user_ids = sorted(ratings["userId"].unique().tolist())
    movielens_movie_ids = sorted(ratings["movieId"].unique().tolist())
    catalog_movie_ids = sorted(movies["movieId"].unique().tolist())

    mappings = {
        "movielens_user_ids": movielens_user_ids,
        "movielens_movie_ids": movielens_movie_ids,
        "catalog_movie_ids": catalog_movie_ids,
        "app_user_id_offset": APP_USER_ID_OFFSET,
        "max_movielens_user_id": max(movielens_user_ids),
        "max_movielens_movie_id": max(movielens_movie_ids),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    return mappings


def main():
    print("=" * 60)
    print("  CineMatch AI - Data Preprocessing")
    print("=" * 60)
    print()

    np.random.seed(RANDOM_SEED)

    # ── Load and Validate ──
    ratings = load_and_validate_ratings(RATINGS_CSV)
    movies = load_and_validate_movies(MOVIES_CSV)
    links = load_and_validate_links(LINKS_CSV)

    # ── Merge TMDB IDs into movies ──
    movies = movies.merge(
        links[["movieId", "tmdbId", "imdbId"]], on="movieId", how="left"
    )

    # ── Chronological Split ──
    train, val, test = chronological_split(ratings, TRAIN_RATIO, VALIDATION_RATIO)

    # ── Compute Stats ──
    stats = compute_statistics(ratings, movies, train, val, test)
    id_maps = create_id_mappings(ratings, movies)

    # ── Save Processed Data ──
    print("\n💾 Saving processed datasets...")
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    train.to_csv(TRAIN_DATA_PATH, index=False)
    val.to_csv(VALIDATION_DATA_PATH, index=False)
    test.to_csv(TEST_DATA_PATH, index=False)
    movies.to_csv(MOVIES_PROCESSED_PATH, index=False)

    with open(DATASET_STATS_PATH, "w") as f:
        json.dump(stats, f, indent=2)

    with open(ID_MAPPINGS_PATH, "w") as f:
        json.dump(id_maps, f, indent=2)

    print(f"   ✅ Train:       {TRAIN_DATA_PATH}")
    print(f"   ✅ Validation:  {VALIDATION_DATA_PATH}")
    print(f"   ✅ Test:        {TEST_DATA_PATH}")
    print(f"   ✅ Movies:      {MOVIES_PROCESSED_PATH}")
    print(f"   ✅ Stats:       {DATASET_STATS_PATH}")
    print(f"   ✅ ID Mappings: {ID_MAPPINGS_PATH}")

    # ── Summary ──
    print("\n📊 Dataset Summary:")
    print(f"   Users:    {stats['total_users']:,}")
    print(f"   Movies:   {stats['total_movies']:,} (rated) / {stats['total_movies_catalog']:,} (catalog)")
    print(f"   Ratings:  {stats['total_ratings']:,}")
    print(f"   Sparsity: {stats['sparsity']:.4%}")
    print(f"   Mean:     {stats['mean_rating']:.3f}")
    print(f"   Period:   {stats['timestamp_range']['min_date'][:10]} → {stats['timestamp_range']['max_date'][:10]}")
    print(f"\n🎉 Preprocessing complete!")


if __name__ == "__main__":
    main()
