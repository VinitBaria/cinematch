"""
CineMatch AI - Movie Routes
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from ..database import get_db
from ..security.auth import get_current_user, get_optional_current_user
from ..schemas.schemas import MovieResponse, MovieListResponse

router = APIRouter(prefix="/api/movies", tags=["Movies"])


def _movie_doc_to_response(doc: dict, user_rating: float = None) -> MovieResponse:
    genres = doc.get("genreList") or doc.get("genres") or []
    if isinstance(genres, str):
        genres = [g.strip() for g in genres.split("|") if g.strip() and g != "(no genres listed)"]
    return MovieResponse(
        movieId=doc["movieId"],
        title=doc.get("title", ""),
        cleanTitle=doc.get("cleanTitle", doc.get("title", "")),
        year=doc.get("year"),
        genres=genres,
        posterUrl=doc.get("posterUrl"),
        overview=doc.get("overview"),
        tmdbId=doc.get("tmdbId"),
        avgRating=doc.get("avgRating"),
        ratingCount=doc.get("ratingCount", 0),
        userRating=user_rating,
    )


@router.get("", response_model=MovieListResponse)
def get_movies(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    sort: str = Query("ratingCount", pattern="^(avgRating|ratingCount|year|title)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    genre: Optional[str] = None,
    yearFrom: Optional[int] = None,
    yearTo: Optional[int] = None,
):
    db = get_db()
    query = {}
    if genre:
        query["genreList"] = genre
    if yearFrom:
        query["year"] = query.get("year", {})
        query["year"]["$gte"] = yearFrom
    if yearTo:
        query.setdefault("year", {})
        query["year"]["$lte"] = yearTo

    sort_dir = -1 if order == "desc" else 1
    total = db.movies.count_documents(query)
    skip = (page - 1) * pageSize

    docs = list(
        db.movies.find(query)
        .sort(sort, sort_dir)
        .skip(skip)
        .limit(pageSize)
    )

    return MovieListResponse(
        movies=[_movie_doc_to_response(d) for d in docs],
        total=total,
        page=page,
        pageSize=pageSize,
    )


@router.get("/search", response_model=MovieListResponse)
def search_movies(
    q: str = Query("", min_length=0),
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
):
    db = get_db()
    query = {}
    if q:
        query["title"] = {"$regex": q, "$options": "i"}

    total = db.movies.count_documents(query)
    skip = (page - 1) * pageSize
    docs = list(
        db.movies.find(query)
        .sort("ratingCount", -1)
        .skip(skip)
        .limit(pageSize)
    )

    return MovieListResponse(
        movies=[_movie_doc_to_response(d) for d in docs],
        total=total,
        page=page,
        pageSize=pageSize,
    )


@router.get("/trending", response_model=list[MovieResponse])
def get_trending():
    db = get_db()
    docs = list(
        db.movies.find({"ratingCount": {"$gte": 50}})
        .sort("ratingCount", -1)
        .limit(20)
    )
    return [_movie_doc_to_response(d) for d in docs]


@router.get("/popular", response_model=list[MovieResponse])
def get_popular():
    db = get_db()
    docs = list(
        db.movies.find({"ratingCount": {"$gte": 30}, "avgRating": {"$gte": 3.8}})
        .sort("avgRating", -1)
        .limit(20)
    )
    return [_movie_doc_to_response(d) for d in docs]


@router.get("/new", response_model=list[MovieResponse])
def get_new_movies():
    db = get_db()
    docs = list(
        db.movies.find({"year": {"$gte": 2010}})
        .sort("year", -1)
        .limit(20)
    )
    return [_movie_doc_to_response(d) for d in docs]


@router.get("/top-rated", response_model=list[MovieResponse])
def get_top_rated():
    db = get_db()
    docs = list(
        db.movies.find({"ratingCount": {"$gte": 20}, "avgRating": {"$gte": 4.0}})
        .sort("avgRating", -1)
        .limit(20)
    )
    return [_movie_doc_to_response(d) for d in docs]


@router.get("/onboarding-picks", response_model=list[MovieResponse])
@router.get("/onboarding", response_model=list[MovieResponse])
def get_onboarding_movies(limit: int = Query(30, ge=1, le=100)):
    """Movies for new user onboarding - popular ones users would recognize."""
    db = get_db()
    docs = list(
        db.movies.find({"ratingCount": {"$gte": 100}})
        .sort("ratingCount", -1)
        .limit(limit)
    )
    return [_movie_doc_to_response(d) for d in docs]


@router.get("/{movie_id}", response_model=MovieResponse)
def get_movie(movie_id: int, current_user=Depends(get_optional_current_user)):
    db = get_db()
    doc = db.movies.find_one({"movieId": movie_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Movie not found")

    # Get user's rating for this movie if user is authenticated
    user_rating = None
    if current_user:
        user_rating_doc = db.ratings.find_one(
            {"userId": current_user["userId"], "movieId": movie_id}
        )
        if user_rating_doc:
            user_rating = user_rating_doc["rating"]

    return _movie_doc_to_response(doc, user_rating=user_rating)
