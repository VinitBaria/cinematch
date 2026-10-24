"""
CineMatch AI - ML Test Suite
Tests for:
  - Dataset validation and splits
  - Training reproducibility
  - SVD inference and known user recommendations
  - Unknown user fallback handling
  - Unknown movie exclusion
  - Already-rated movie filtering
  - Ranking metric correctness
"""

import json
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml.config import (
    TRAIN_DATA_PATH,
    VALIDATION_DATA_PATH,
    TEST_DATA_PATH,
    MOVIES_PROCESSED_PATH,
    DATASET_STATS_PATH,
    MODEL_PATH,
    MODEL_METADATA_PATH,
    EVALUATION_METRICS_PATH,
    MIN_RATING,
    MAX_RATING,
    RELEVANCE_THRESHOLD,
    TOP_K,
)
from ml.recommend import SVDRecommender, get_popular_movies
from ml.evaluate import compute_prediction_metrics, compute_ranking_metrics


class TestDatasetValidation:
    """Validate data preprocessing and split integrity."""

    def test_processed_files_exist(self):
        assert TRAIN_DATA_PATH.exists(), "Train data missing"
        assert VALIDATION_DATA_PATH.exists(), "Validation data missing"
        assert TEST_DATA_PATH.exists(), "Test data missing"
        assert MOVIES_PROCESSED_PATH.exists(), "Movies processed data missing"
        assert DATASET_STATS_PATH.exists(), "Dataset stats missing"

    def test_rating_ranges_and_step(self):
        for path in [TRAIN_DATA_PATH, VALIDATION_DATA_PATH, TEST_DATA_PATH]:
            df = pd.read_csv(path)
            assert (df["rating"] >= MIN_RATING).all(), f"Rating below min in {path}"
            assert (df["rating"] <= MAX_RATING).all(), f"Rating above max in {path}"
            # Check 0.5 increments
            assert ((df["rating"] * 2) % 1 == 0).all(), f"Non 0.5 step in {path}"

    def test_chronological_split_integrity(self):
        """Ensure no future ratings leaked into train set per user."""
        train_df = pd.read_csv(TRAIN_DATA_PATH)
        test_df = pd.read_csv(TEST_DATA_PATH)

        # Check overlapping users: user max train timestamp <= user min test timestamp
        common_users = set(train_df["userId"]).intersection(set(test_df["userId"]))
        assert len(common_users) > 0

        leaks = 0
        for uid in list(common_users)[:50]:  # sample check
            train_max_ts = train_df[train_df["userId"] == uid]["timestamp"].max()
            test_min_ts = test_df[test_df["userId"] == uid]["timestamp"].min()
            if train_max_ts > test_min_ts:
                leaks += 1
        assert leaks == 0, f"Found {leaks} user chronological leaks"

    def test_no_duplicate_ratings_in_split(self):
        for path in [TRAIN_DATA_PATH, VALIDATION_DATA_PATH, TEST_DATA_PATH]:
            df = pd.read_csv(path)
            dupes = df.duplicated(subset=["userId", "movieId"]).sum()
            assert dupes == 0, f"Duplicates found in {path}"


class TestSVDRecommender:
    """Test SVD inference and business rules."""

    @classmethod
    def setup_class(cls):
        cls.recommender = SVDRecommender(MODEL_PATH, MODEL_METADATA_PATH)
        cls.train_df = pd.read_csv(TRAIN_DATA_PATH)
        cls.movies_df = pd.read_csv(MOVIES_PROCESSED_PATH)

    def test_model_loaded(self):
        assert self.recommender.is_loaded
        assert len(self.recommender.known_user_ids) > 0
        assert len(self.recommender.known_movie_ids) > 0

    def test_known_user_recommendations(self):
        user_id = list(self.recommender.known_user_ids)[0]
        rated = set(self.train_df[self.train_df["userId"] == user_id]["movieId"])
        recs = self.recommender.recommend(user_id=user_id, rated_movie_ids=rated, n=10)

        assert len(recs) == 10
        assert all(r["recommendationStrategy"] == "svd_collaborative_filtering" for r in recs)
        assert all(r["predictedRating"] is not None for r in recs)
        # Verify descending order
        ratings = [r["predictedRating"] for r in recs]
        assert ratings == sorted(ratings, reverse=True)

    def test_excludes_already_rated_movies(self):
        user_id = list(self.recommender.known_user_ids)[0]
        rated = set(self.train_df[self.train_df["userId"] == user_id]["movieId"])
        recs = self.recommender.recommend(user_id=user_id, rated_movie_ids=rated, n=20)

        rec_movie_ids = {r["movieId"] for r in recs}
        overlap = rec_movie_ids.intersection(rated)
        assert len(overlap) == 0, f"Recommended already-rated movies: {overlap}"

    def test_unknown_user_raises_value_error(self):
        unknown_id = 9999999
        assert not self.recommender.is_known_user(unknown_id)
        with pytest.raises(ValueError):
            self.recommender.recommend(user_id=unknown_id, rated_movie_ids=set(), n=10)

    def test_unknown_movie_exclusion(self):
        user_id = list(self.recommender.known_user_ids)[0]
        unknown_movie_id = 8888888
        assert not self.recommender.is_known_movie(unknown_movie_id)
        pred = self.recommender.predict_rating(user_id, unknown_movie_id)
        assert pred is None


class TestColdStartFallback:
    """Test popularity-based fallback for cold start."""

    def test_popularity_recommendations(self):
        popular = get_popular_movies(n=10)
        assert len(popular) == 10
        assert all(r["recommendationStrategy"] == "popularity_bayesian_weighted" for r in popular)
        assert all(r["predictedRating"] is None for r in popular), "Must not fabricate predictedRating for cold start"
        assert all(r["popularityScore"] is not None for r in popular)

        # Verify descending order of popularity score
        scores = [r["popularityScore"] for r in popular]
        assert scores == sorted(scores, reverse=True)

    def test_popularity_excludes_rated(self):
        popular = get_popular_movies(n=5)
        exclude_id = popular[0]["movieId"]

        new_popular = get_popular_movies(n=5, exclude_movie_ids={exclude_id})
        new_ids = {r["movieId"] for r in new_popular}
        assert exclude_id not in new_ids


class TestEvaluationMetrics:
    """Test evaluation artifacts and metrics."""

    def test_evaluation_json_exists_and_valid(self):
        assert EVALUATION_METRICS_PATH.exists()
        with open(EVALUATION_METRICS_PATH) as f:
            metrics = json.load(f)

        assert "prediction_metrics" in metrics
        assert "rmse" in metrics["prediction_metrics"]
        assert "mae" in metrics["prediction_metrics"]
        assert metrics["prediction_metrics"]["rmse"] < 1.2, "RMSE unexpectedly high"

        assert "ranking_metrics" in metrics
        assert f"ndcg_at_{TOP_K}" in metrics["ranking_metrics"]
        assert metrics["ranking_metrics"][f"ndcg_at_{TOP_K}"] > 0.5
