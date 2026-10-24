"""
CineMatch AI - Recommendation Generation
Loads the trained SVD model and generates top-N recommendations.

Handles:
  - Known SVD users → SVD predictions
  - Unknown users → raises clear error (cold-start handled at API layer)
  - Known movies only (unknown movies excluded from SVD predictions)
  - Excludes already-rated movies
"""

import json
import sys
from pathlib import Path
from typing import Optional

# Fix Windows console encoding
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import types
import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if "surprise.similarities" not in sys.modules:
    try:
        from scripts.patch_surprise import SIM_CONTENT
        _sim_mod = types.ModuleType("surprise.similarities")
        exec(SIM_CONTENT, _sim_mod.__dict__)
        sys.modules["surprise.similarities"] = _sim_mod
    except Exception:
        pass

from ml.config import (
    MODEL_PATH,
    MODEL_METADATA_PATH,
    MOVIES_PROCESSED_PATH,
    TRAIN_DATA_PATH,
    ARTIFACTS_DIR,
    RANDOM_SEED,
)


class SVDRecommender:
    """
    Wraps the trained SVD model for inference.
    Designed to be loaded once and reused across API requests.
    """

    def __init__(self, model_path: Path = MODEL_PATH, metadata_path: Path = MODEL_METADATA_PATH):
        self.model = None
        self.metadata = None
        self.known_user_ids = set()
        self.known_movie_ids = set()
        self.model_version = "unknown"
        self._loaded = False

        self._load(model_path, metadata_path)

    def _load(self, model_path: Path, metadata_path: Path):
        """Load model and metadata from disk."""
        if not model_path.exists():
            raise FileNotFoundError(
                f"Model not found at {model_path}. Run train.py first."
            )
        if not metadata_path.exists():
            raise FileNotFoundError(
                f"Metadata not found at {metadata_path}. Run train.py first."
            )

        self.model = joblib.load(model_path)

        with open(metadata_path) as f:
            self.metadata = json.load(f)

        self.known_user_ids = set(self.metadata.get("known_user_ids", []))
        self.known_movie_ids = set(self.metadata.get("known_movie_ids", []))
        self.model_version = self.metadata.get("model_version", "unknown")
        self._loaded = True

        print(f"✅ SVD Recommender loaded (version: {self.model_version})")
        print(f"   Known users: {len(self.known_user_ids):,}")
        print(f"   Known movies: {len(self.known_movie_ids):,}")

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def is_known_user(self, user_id: int) -> bool:
        """Check if a user was in the training data."""
        return user_id in self.known_user_ids

    def is_known_movie(self, movie_id: int) -> bool:
        """Check if a movie was in the training data."""
        return movie_id in self.known_movie_ids

    def predict_rating(self, user_id: int, movie_id: int) -> Optional[float]:
        """
        Predict a single rating.
        Returns None if user or movie is unknown to the model.
        """
        if not self.is_known_user(user_id):
            return None
        if not self.is_known_movie(movie_id):
            return None

        pred = self.model.predict(user_id, movie_id)
        return round(float(pred.est), 4)

    def recommend(
        self,
        user_id: int,
        rated_movie_ids: set[int],
        n: int = 10,
        movie_details: Optional[dict] = None,
    ) -> list[dict]:
        """
        Generate top-N recommendations for a known SVD user.

        Args:
            user_id: The user's ID (must be in known_user_ids).
            rated_movie_ids: Set of movieIds the user has already rated
                             (includes both training and live ratings).
            n: Number of recommendations to return.
            movie_details: Optional dict mapping movieId → movie info dict.

        Returns:
            List of recommendation dicts sorted by predicted rating.

        Raises:
            ValueError: If user is unknown to the model.
        """
        if not self.is_known_user(user_id):
            raise ValueError(
                f"User {user_id} is not known to the SVD model. "
                f"Use cold-start recommendations instead."
            )

        # Candidate movies: known to SVD AND not already rated
        candidate_ids = self.known_movie_ids - rated_movie_ids

        if not candidate_ids:
            return []

        # Predict ratings for all candidates
        predictions = []
        for movie_id in candidate_ids:
            pred = self.model.predict(user_id, movie_id)
            predictions.append((movie_id, float(pred.est)))

        # Sort by predicted rating descending
        predictions.sort(key=lambda x: x[1], reverse=True)

        # Take top N
        top_n = predictions[:n]

        # Build result
        results = []
        for movie_id, pred_rating in top_n:
            rec = {
                "movieId": movie_id,
                "predictedRating": round(pred_rating, 4),
                "recommendationStrategy": "svd_collaborative_filtering",
                "modelVersion": self.model_version,
            }

            # Enrich with movie details if provided
            if movie_details and movie_id in movie_details:
                details = movie_details[movie_id]
                rec["title"] = details.get("title", "Unknown")
                rec["year"] = details.get("year")
                rec["posterUrl"] = details.get("posterUrl")
                rec["genres"] = details.get("genres", [])

            results.append(rec)

        return results

    def get_model_info(self) -> dict:
        """Return model metadata for API responses."""
        return {
            "modelVersion": self.model_version,
            "algorithm": self.metadata.get("algorithm", "SVD"),
            "parameters": self.metadata.get("parameters", {}),
            "trainsetStats": self.metadata.get("trainset_stats", {}),
            "trainedAt": self.metadata.get("trained_at", ""),
            "knownUsers": len(self.known_user_ids),
            "knownMovies": len(self.known_movie_ids),
        }


def get_popular_movies(
    train_path: Path = TRAIN_DATA_PATH,
    movies_path: Path = MOVIES_PROCESSED_PATH,
    min_ratings: int = 10,
    n: int = 20,
    exclude_movie_ids: set[int] = None,
) -> list[dict]:
    """
    Generate popularity-based recommendations using Bayesian weighted scores.
    Used for cold-start (Case A: zero-ratings user).

    Uses the formula:
        weighted_score = (v / (v + m)) * R + (m / (v + m)) * C
    where:
        v = number of ratings for the movie
        m = minimum ratings threshold
        R = average rating for the movie
        C = global mean rating
    """
    train_df = pd.read_csv(train_path)
    movies_df = pd.read_csv(movies_path)

    if exclude_movie_ids is None:
        exclude_movie_ids = set()

    # Compute per-movie stats
    movie_stats = train_df.groupby("movieId").agg(
        avg_rating=("rating", "mean"),
        count=("rating", "count"),
    ).reset_index()

    # Filter by minimum ratings
    movie_stats = movie_stats[movie_stats["count"] >= min_ratings]

    # Global mean
    C = float(train_df["rating"].mean())
    m = min_ratings

    # Bayesian weighted score
    movie_stats["weighted_score"] = (
        (movie_stats["count"] / (movie_stats["count"] + m)) * movie_stats["avg_rating"]
        + (m / (movie_stats["count"] + m)) * C
    )

    # Exclude already rated
    movie_stats = movie_stats[~movie_stats["movieId"].isin(exclude_movie_ids)]

    # Sort and take top N
    movie_stats = movie_stats.sort_values("weighted_score", ascending=False).head(n)

    # Merge movie details
    movie_stats = movie_stats.merge(movies_df[["movieId", "title", "year"]], on="movieId", how="left")

    results = []
    for _, row in movie_stats.iterrows():
        results.append({
            "movieId": int(row["movieId"]),
            "title": row.get("title", "Unknown"),
            "year": row.get("year"),
            "predictedRating": None,  # No personalized prediction
            "popularityScore": round(float(row["weighted_score"]), 4),
            "ratingCount": int(row["count"]),
            "avgRating": round(float(row["avg_rating"]), 2),
            "recommendationStrategy": "popularity_bayesian_weighted",
            "modelVersion": None,
        })

    return results


def demo_recommendations():
    """Demo: generate recommendations for a sample user."""
    print("=" * 60)
    print("  CineMatch AI - Recommendation Demo")
    print("=" * 60)
    print()

    # Load recommender
    try:
        recommender = SVDRecommender()
    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)

    # Load training data to find rated movies
    train_df = pd.read_csv(TRAIN_DATA_PATH)
    movies_df = pd.read_csv(MOVIES_PROCESSED_PATH)

    # Build movie details lookup
    movie_details = {}
    for _, row in movies_df.iterrows():
        movie_details[int(row["movieId"])] = {
            "title": row.get("title", "Unknown"),
            "year": row.get("year"),
        }

    # Pick a sample known user
    sample_user = list(recommender.known_user_ids)[0]
    user_rated = set(
        train_df[train_df["userId"] == sample_user]["movieId"].tolist()
    )

    print(f"\n👤 User {sample_user} has rated {len(user_rated)} movies in training")

    # SVD recommendations
    print(f"\n🎬 Top 10 SVD Recommendations:")
    print("-" * 60)
    recs = recommender.recommend(
        user_id=sample_user,
        rated_movie_ids=user_rated,
        n=10,
        movie_details=movie_details,
    )
    for i, rec in enumerate(recs, 1):
        title = rec.get("title", "Unknown")
        year = rec.get("year", "")
        pred = rec["predictedRating"]
        print(f"   {i:2d}. {title} ({year}) — predicted: {pred:.2f}")

    # Popularity recommendations (cold start)
    print(f"\n🔥 Top 10 Popular Movies (cold-start fallback):")
    print("-" * 60)
    popular = get_popular_movies(n=10)
    for i, rec in enumerate(popular, 1):
        title = rec.get("title", "Unknown")
        year = rec.get("year", "")
        score = rec["popularityScore"]
        count = rec["ratingCount"]
        print(f"   {i:2d}. {title} ({year}) — score: {score:.2f} ({count} ratings)")

    # Unknown user test
    unknown_user = 999999
    print(f"\n❓ Testing unknown user {unknown_user}:")
    if recommender.is_known_user(unknown_user):
        print("   Unexpectedly known!")
    else:
        print("   ✅ Correctly identified as unknown user")
        print("   → Would serve popularity recommendations")

    print(f"\n📊 Model info:")
    info = recommender.get_model_info()
    for k, v in info.items():
        print(f"   {k}: {v}")


if __name__ == "__main__":
    demo_recommendations()
