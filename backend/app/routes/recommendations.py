"""
CineMatch AI - Recommendation Routes
Handles SVD, neighbor-based, and popularity-based recommendations.
"""
import time
import sys
from pathlib import Path
from collections import defaultdict
from fastapi import APIRouter, Depends, Query
import numpy as np
from ..database import get_db
from ..security.auth import get_current_user, get_optional_current_user
from ..schemas.schemas import RecommendationItem, RecommendationResponse
from ..config import ARTIFACTS_DIR, PROCESSED_DIR
from ..metrics import (
    RECOMMENDATION_REQUESTS_TOTAL,
    MODEL_INFERENCE_SECONDS,
    RECOMMENDED_ITEMS_COUNT,
)


# Add ml directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

router = APIRouter(prefix="/api/recommendations", tags=["Recommendations"])

# Global recommender - loaded once
_recommender = None


def _get_recommender():
    global _recommender
    if _recommender is None:
        try:
            from ml.recommend import SVDRecommender
            model_path = ARTIFACTS_DIR / "svd_model.joblib"
            meta_path = ARTIFACTS_DIR / "model_metadata.json"
            if model_path.exists() and meta_path.exists():
                _recommender = SVDRecommender(model_path, meta_path)
        except Exception as e:
            print(f"[WARN] Could not load SVD model: {e}")
    return _recommender


def _get_movie_details_map(db) -> dict:
    movies = list(db.movies.find({}, {
        "movieId": 1, "title": 1, "cleanTitle": 1, "year": 1,
        "posterUrl": 1, "overview": 1, "genreList": 1, "avgRating": 1, "ratingCount": 1,
    }))
    result = {}
    for m in movies:
        genres = m.get("genreList", [])
        if isinstance(genres, str):
            genres = [g.strip() for g in genres.split("|") if g.strip()]
        result[m["movieId"]] = {
            "title": m.get("title", ""),
            "cleanTitle": m.get("cleanTitle", m.get("title", "")),
            "year": m.get("year"),
            "posterUrl": m.get("posterUrl"),
            "overview": m.get("overview"),
            "genres": genres,
            "avgRating": m.get("avgRating"),
            "ratingCount": m.get("ratingCount", 0),
        }
    return result


def _neighbor_recommendations(user_id: int, db, n: int = 10) -> list[dict]:
    """User-based collaborative filtering for cold-start users with a few ratings."""
    import pandas as pd

    user_ratings = list(db.ratings.find({"userId": user_id}))
    if not user_ratings:
        return []

    user_rated = {r["movieId"]: r["rating"] for r in user_ratings}

    # Find users who rated overlapping movies
    overlap_users = defaultdict(list)
    for movie_id in user_rated:
        others = db.ratings.find({"movieId": movie_id, "userId": {"$ne": user_id}})
        for o in others:
            overlap_users[o["userId"]].append((movie_id, o["rating"]))

    # Calculate similarity (cosine) with users who have >= 3 overlapping movies
    similarities = []
    for other_id, overlaps in overlap_users.items():
        if len(overlaps) < 3:
            continue
        a_vec = [user_rated[mid] for mid, _ in overlaps]
        b_vec = [r for _, r in overlaps]
        a = np.array(a_vec)
        b = np.array(b_vec)
        denom = np.linalg.norm(a) * np.linalg.norm(b)
        if denom > 0:
            sim = float(np.dot(a, b) / denom)
            if sim > 0.1:
                similarities.append((other_id, sim))

    if not similarities:
        return []

    # Sort by similarity, take top 30
    similarities.sort(key=lambda x: x[1], reverse=True)
    top_neighbors = similarities[:30]

    # Predict ratings for unseen movies
    movie_scores = defaultdict(lambda: {"weighted_sum": 0.0, "sim_sum": 0.0})
    for neighbor_id, sim in top_neighbors:
        neighbor_ratings = list(db.ratings.find({"userId": neighbor_id}))
        for nr in neighbor_ratings:
            if nr["movieId"] not in user_rated:
                movie_scores[nr["movieId"]]["weighted_sum"] += sim * nr["rating"]
                movie_scores[nr["movieId"]]["sim_sum"] += sim

    predictions = []
    for mid, scores in movie_scores.items():
        if scores["sim_sum"] > 0:
            pred = scores["weighted_sum"] / scores["sim_sum"]
            predictions.append((mid, pred))

    predictions.sort(key=lambda x: x[1], reverse=True)
    return predictions[:n]


def _get_user_preferred_genres(user_ratings, movie_details):
    genre_weights = defaultdict(float)
    # Sort with most recent ratings first
    sorted_ratings = sorted(user_ratings, key=lambda x: str(x.get("updatedAt", "")), reverse=True)

    # Actively rated genres in the recent session get direct priority
    recent_genres = []
    for r in sorted_ratings[:5]:
        if float(r.get("rating", 0)) >= 3.0:
            genres = movie_details.get(r.get("movieId"), {}).get("genres", [])
            for g in genres:
                if g and g not in recent_genres and g != "(no genres listed)":
                    recent_genres.append(g)

    for idx, r in enumerate(sorted_ratings):
        rating = float(r.get("rating", 0))
        if rating >= 3.0:
            mid = r.get("movieId")
            details = movie_details.get(mid, {})
            genres = details.get("genres", [])
            mult = 5.0 if idx < 5 else 1.0
            for g in genres:
                if g and g != "(no genres listed)":
                    genre_weights[g] += (rating - 2.0) * mult

    overall_top = [g for g, _ in sorted(genre_weights.items(), key=lambda x: x[1], reverse=True)]

    # Put recently active genres right at the front
    result = []
    for g in recent_genres:
        if g not in result:
            result.append(g)
    for g in overall_top:
        if g not in result:
            result.append(g)
    return result


@router.get("", response_model=RecommendationResponse)
@router.get("/", response_model=RecommendationResponse)
@router.get("/me", response_model=RecommendationResponse)
def get_my_recommendations(
    limit: int = Query(10, ge=1, le=50),
    current_user=Depends(get_optional_current_user),
):
    db = get_db()
    user_id = current_user["userId"] if current_user else 0

    # Get all user's ratings (training + live)
    user_ratings = list(db.ratings.find({"userId": user_id})) if user_id else []
    rated_movie_ids = {r["movieId"] for r in user_ratings}
    rating_count = len(rated_movie_ids)

    movie_details = _get_movie_details_map(db)
    recommender = _get_recommender()

    # Dynamic genre profiling from live positive ratings
    preferred_genres = _get_user_preferred_genres(user_ratings, movie_details)
    top_preferred = preferred_genres[:3] if preferred_genres else []

    # Pre-fetch top genre matches if user has rated films
    genre_matches = []
    if top_preferred:
        matched_docs = list(
            db.movies.find({
                "genres": {"$in": top_preferred},
                "movieId": {"$nin": list(rated_movie_ids)},
                "avgRating": {"$ne": None},
            })
            .sort([("avgRating", -1), ("ratingCount", -1)])
            .limit(limit)
        )
        for m in matched_docs:
            genres = m.get("genreList") or m.get("genres") or []
            if isinstance(genres, str):
                genres = [g.strip() for g in genres.split("|")]
            genre_matches.append(RecommendationItem(
                movieId=m["movieId"],
                title=m.get("title", ""),
                cleanTitle=m.get("cleanTitle"),
                year=m.get("year"),
                genres=genres,
                posterUrl=m.get("posterUrl"),
                overview=m.get("overview"),
                predictedRating=m.get("avgRating"),
                popularityScore=m.get("avgRating"),
                avgRating=m.get("avgRating"),
                ratingCount=m.get("ratingCount"),
                recommendationStrategy="genre_personalized_hybrid",
                modelVersion=recommender.model_version if recommender else None,
            ))

    items = []
    strategy = "popularity_bayesian_weighted"

    # Case C: Known SVD user
    if recommender and recommender.is_known_user(user_id):
        try:
            t0 = time.time()
            recs = recommender.recommend(
                user_id=user_id,
                rated_movie_ids=rated_movie_ids,
                n=max(limit * 2, 40),
                movie_details=movie_details,
            )
            infer_duration = time.time() - t0
            MODEL_INFERENCE_SECONDS.labels(
                model_version=str(recommender.model_version or "unknown"),
                user_type="known",
            ).observe(infer_duration)

            # Re-rank SVD picks with genre affinity boost
            scored_recs = []
            for r in recs:
                mid = r["movieId"]
                details = movie_details.get(mid, {})
                genres = details.get("genres", [])
                if isinstance(genres, str):
                    genres = [g.strip() for g in genres.split("|")]
                
                # Check genre alignment
                genre_match = any(g in top_preferred for g in genres) if top_preferred else False
                boosted_rating = (r.get("predictedRating") or 3.5) + (0.6 if genre_match else 0.0)
                scored_recs.append((boosted_rating, r, details, genres, genre_match))

            scored_recs.sort(key=lambda x: x[0], reverse=True)

            svd_items = []
            for boosted_rating, r, details, genres, genre_match in scored_recs:
                mid = r["movieId"]
                svd_items.append(RecommendationItem(
                    movieId=mid,
                    title=details.get("title", r.get("title", "")),
                    cleanTitle=details.get("cleanTitle"),
                    year=details.get("year"),
                    genres=genres,
                    posterUrl=details.get("posterUrl"),
                    overview=details.get("overview"),
                    predictedRating=round(boosted_rating, 2),
                    avgRating=details.get("avgRating"),
                    ratingCount=details.get("ratingCount"),
                    recommendationStrategy="svd_collaborative_filtering",
                    modelVersion=recommender.model_version,
                ))

            # Interleave top genre matches and top SVD picks
            seen_ids = set()
            g_idx, s_idx = 0, 0
            while len(items) < limit and (g_idx < len(genre_matches) or s_idx < len(svd_items)):
                if top_preferred and g_idx < len(genre_matches):
                    gm = genre_matches[g_idx]
                    g_idx += 1
                    if gm.movieId not in seen_ids:
                        seen_ids.add(gm.movieId)
                        items.append(gm)
                if len(items) < limit and s_idx < len(svd_items):
                    sm = svd_items[s_idx]
                    s_idx += 1
                    if sm.movieId not in seen_ids:
                        seen_ids.add(sm.movieId)
                        items.append(sm)

            strategy = "genre_personalized_hybrid" if top_preferred else "svd_collaborative_filtering"
        except Exception as e:
            print(f"[WARN] SVD recommendation error: {e}")

    # Case B: User with some ratings (or fresh user who rated movies)
    if not items and rating_count > 0:
        seen_ids = set()
        # Primary: genre matches from user's positive ratings
        for gm in genre_matches:
            if gm.movieId not in seen_ids and len(items) < limit:
                seen_ids.add(gm.movieId)
                items.append(gm)

        # Supplement with neighbor collaborative filtering if needed
        if len(items) < limit:
            neighbor_preds = _neighbor_recommendations(user_id, db, n=limit)
            for mid, pred in neighbor_preds:
                if mid not in seen_ids and len(items) < limit:
                    seen_ids.add(mid)
                    details = movie_details.get(mid, {})
                    genres = details.get("genres", [])
                    if isinstance(genres, str):
                        genres = [g.strip() for g in genres.split("|")]
                    items.append(RecommendationItem(
                        movieId=mid,
                        title=details.get("title", ""),
                        cleanTitle=details.get("cleanTitle"),
                        year=details.get("year"),
                        genres=genres,
                        posterUrl=details.get("posterUrl"),
                        overview=details.get("overview"),
                        predictedRating=round(pred, 2),
                        avgRating=details.get("avgRating"),
                        ratingCount=details.get("ratingCount"),
                        recommendationStrategy="neighbor_collaborative_filtering",
                        modelVersion=None,
                    ))
        strategy = "genre_personalized_hybrid"

    # Case A: Popularity fallback for brand new unrated users
    if not items:
        popular = list(
            db.movies.find({"movieId": {"$nin": list(rated_movie_ids)}, "avgRating": {"$ne": None}})
            .sort([("avgRating", -1), ("ratingCount", -1)])
            .limit(limit)
        )
        for m in popular:
            genres = m.get("genreList", [])
            if isinstance(genres, str):
                genres = [g.strip() for g in genres.split("|")]
            items.append(RecommendationItem(
                movieId=m["movieId"],
                title=m.get("title", ""),
                cleanTitle=m.get("cleanTitle"),
                year=m.get("year"),
                genres=genres,
                posterUrl=m.get("posterUrl"),
                overview=m.get("overview"),
                predictedRating=None,
                popularityScore=m.get("avgRating"),
                avgRating=m.get("avgRating"),
                ratingCount=m.get("ratingCount"),
                recommendationStrategy="popularity_bayesian_weighted",
                modelVersion=None,
            ))
        strategy = "popularity_bayesian_weighted"

    # Record Prometheus metrics
    RECOMMENDATION_REQUESTS_TOTAL.labels(strategy=strategy, status="success").inc()
    RECOMMENDED_ITEMS_COUNT.labels(strategy=strategy).observe(len(items))

    return RecommendationResponse(
        recommendations=items,
        strategy=strategy,
        modelVersion=recommender.model_version if recommender else None,
        userId=user_id,
    )


@router.get("/cold-start", response_model=RecommendationResponse)
def get_cold_start_recommendations(limit: int = Query(15, ge=1, le=50)):
    db = get_db()
    popular = list(
        db.movies.find({"ratingCount": {"$gte": 20}})
        .sort("avgRating", -1)
        .limit(limit)
    )
    items = []
    for m in popular:
        genres = m.get("genreList", [])
        if isinstance(genres, str):
            genres = [g.strip() for g in genres.split("|")]
        items.append(RecommendationItem(
            movieId=m["movieId"],
            title=m.get("title", ""),
            cleanTitle=m.get("cleanTitle"),
            year=m.get("year"),
            genres=genres,
            posterUrl=m.get("posterUrl"),
            overview=m.get("overview"),
            predictedRating=None,
            popularityScore=m.get("avgRating"),
            avgRating=m.get("avgRating"),
            ratingCount=m.get("ratingCount"),
            recommendationStrategy="popularity_bayesian_weighted",
            modelVersion=None,
        ))

    return RecommendationResponse(
        recommendations=items,
        strategy="popularity_bayesian_weighted",
        modelVersion=None,
        userId=0,
    )

