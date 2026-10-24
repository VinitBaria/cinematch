"""
CineMatch AI - Rating Routes
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from ..database import get_db
from ..security.auth import get_current_user
from ..schemas.schemas import RatingRequest, RatingResponse
from ..metrics import RATINGS_SUBMITTED_TOTAL

router = APIRouter(prefix="/api/ratings", tags=["Ratings"])



def _update_movie_stats(db, movie_id: int):
    """Recalculate movie avg rating and count after a rating change."""
    pipeline = [
        {"$match": {"movieId": movie_id}},
        {"$group": {"_id": None, "avg": {"$avg": "$rating"}, "count": {"$sum": 1}}},
    ]
    result = list(db.ratings.aggregate(pipeline))
    if result:
        db.movies.update_one(
            {"movieId": movie_id},
            {"$set": {"avgRating": round(result[0]["avg"], 2), "ratingCount": result[0]["count"]}},
        )
    else:
        db.movies.update_one(
            {"movieId": movie_id},
            {"$set": {"avgRating": None, "ratingCount": 0}},
        )


@router.post("", response_model=RatingResponse)
def create_rating(req: RatingRequest, current_user=Depends(get_current_user)):
    db = get_db()
    user_id = current_user["userId"]
    now = datetime.now(timezone.utc).isoformat()

    # Validate rating step
    if (req.rating * 2) % 1 != 0:
        raise HTTPException(status_code=400, detail="Rating must be in 0.5 increments")

    # Check movie exists
    movie = db.movies.find_one({"movieId": req.movieId})
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    # Upsert rating
    existing = db.ratings.find_one({"userId": user_id, "movieId": req.movieId})
    if existing:
        db.ratings.update_one(
            {"userId": user_id, "movieId": req.movieId},
            {"$set": {"rating": req.rating, "updatedAt": now}},
        )
    else:
        db.ratings.insert_one({
            "userId": user_id,
            "movieId": req.movieId,
            "rating": req.rating,
            "createdAt": now,
            "updatedAt": now,
        })

    _update_movie_stats(db, req.movieId)
    RATINGS_SUBMITTED_TOTAL.labels(rating=str(req.rating)).inc()

    return RatingResponse(
        userId=user_id,
        movieId=req.movieId,
        rating=req.rating,
        title=movie.get("title"),
        posterUrl=movie.get("posterUrl"),
        createdAt=existing["createdAt"] if existing else now,
        updatedAt=now,
    )


@router.put("/{movie_id}", response_model=RatingResponse)
def update_rating(movie_id: int, req: RatingRequest, current_user=Depends(get_current_user)):
    req.movieId = movie_id
    return create_rating(req, current_user)


@router.delete("/{movie_id}")
def delete_rating(movie_id: int, current_user=Depends(get_current_user)):
    db = get_db()
    user_id = current_user["userId"]

    result = db.ratings.delete_one({"userId": user_id, "movieId": movie_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Rating not found")

    _update_movie_stats(db, movie_id)
    return {"message": "Rating deleted"}


@router.get("", response_model=list[RatingResponse])
@router.get("/", response_model=list[RatingResponse])
@router.get("/me", response_model=list[RatingResponse])
def get_my_ratings(
    limit: int = 100,
    skip: int = 0,
    current_user=Depends(get_current_user),
):
    db = get_db()
    user_id = current_user["userId"]

    ratings = list(
        db.ratings.find({"userId": user_id})
        .sort("updatedAt", -1)
        .skip(skip)
        .limit(limit)
    )

    results = []
    for r in ratings:
        movie = db.movies.find_one({"movieId": r["movieId"]})
        results.append(RatingResponse(
            userId=user_id,
            movieId=r["movieId"],
            rating=r["rating"],
            title=movie.get("title") if movie else None,
            posterUrl=movie.get("posterUrl") if movie else None,
            createdAt=r.get("createdAt"),
            updatedAt=r.get("updatedAt"),
        ))

    return results
