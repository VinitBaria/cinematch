"""
CineMatch AI - Movie Routes
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from datetime import datetime, timezone
from ..database import get_db
from ..security.auth import get_current_user, get_optional_current_user
from ..schemas.schemas import MovieResponse, MovieListResponse, MovieCreateRequest

router = APIRouter(prefix="/api/movies", tags=["Movies"])

# High-resolution verified fallback posters ensuring EVERY movie has a stunning poster
GENRE_FALLBACK_POSTERS = {
    "Action": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=800&auto=format&fit=crop&q=80",
    "Drama": "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=800&auto=format&fit=crop&q=80",
    "Comedy": "https://images.unsplash.com/photo-1514306191717-452ec28c7814?w=800&auto=format&fit=crop&q=80",
    "Romance": "https://images.unsplash.com/photo-1518199266791-5375a83190b7?w=800&auto=format&fit=crop&q=80",
    "Sci-Fi": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800&auto=format&fit=crop&q=80",
    "Thriller": "https://images.unsplash.com/photo-1478760329108-5c3ed9d495a0?w=800&auto=format&fit=crop&q=80",
    "Horror": "https://images.unsplash.com/photo-1509248961158-e54f6934749c?w=800&auto=format&fit=crop&q=80",
    "Adventure": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=800&auto=format&fit=crop&q=80",
    "Animation": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=800&auto=format&fit=crop&q=80",
    "Bollywood": "https://images.unsplash.com/photo-1518199266791-5375a83190b7?w=800&auto=format&fit=crop&q=80",
    "Hollywood": "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=800&auto=format&fit=crop&q=80",
    "Default": "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=800&auto=format&fit=crop&q=80",
}

KNOWN_POSTER_MAP = {
    "jawan": "/posters/jawan.jpg",
    "rrr": "/posters/rrr.jpg",
    "pathaan": "/posters/pathaan.jpg",
    "animal": "/posters/animal.jpg",
    "stree 2": "/posters/stree2.jpg",
    "12th fail": "/posters/12th_fail.jpg",
    "dangal": "/posters/dangal.jpg",
    "3 idiots": "/posters/3_idiots.jpg",
    "oppenheimer": "/posters/oppenheimer.jpg",
    "dune: part two": "/posters/dune2.jpg",
    "dune 2": "/posters/dune2.jpg",
    "interstellar": "/posters/interstellar.jpg",
    "the dark knight": "/posters/the_dark_knight.jpg",
    "deadpool & wolverine": "/posters/deadpool_wolverine.jpg",
    "avatar: the way of water": "/posters/avatar2.jpg",
}


def _movie_doc_to_response(doc: dict, user_rating: float = None) -> MovieResponse:
    genres = doc.get("genreList") or doc.get("genres") or []
    if isinstance(genres, str):
        genres = [g.strip() for g in genres.split("|") if g.strip() and g != "(no genres listed)"]
    
    # Ensure every single movie has a guaranteed valid working poster
    poster_url = doc.get("posterUrl")
    if not poster_url or not str(poster_url).strip():
        first_genre = genres[0] if genres else "Default"
        industry = doc.get("industry") or "Default"
        poster_url = GENRE_FALLBACK_POSTERS.get(first_genre) or GENRE_FALLBACK_POSTERS.get(industry) or GENRE_FALLBACK_POSTERS["Default"]

    return MovieResponse(
        movieId=doc["movieId"],
        title=doc.get("title", ""),
        cleanTitle=doc.get("cleanTitle", doc.get("title", "")),
        year=doc.get("year"),
        genres=genres,
        industry=doc.get("industry"),
        posterUrl=poster_url,
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


@router.post("", response_model=MovieResponse, status_code=201)
def create_movie(payload: MovieCreateRequest):
    """
    Admin endpoint to add a newly released Bollywood or Hollywood movie.
    Guarantees every film has a high-quality poster.
    """
    db = get_db()

    # Determine unique sequential movieId
    highest_movie = db.movies.find_one(sort=[("movieId", -1)])
    next_movie_id = (highest_movie["movieId"] + 1) if highest_movie and "movieId" in highest_movie else 200000

    clean_title = payload.title.strip()
    title_key = clean_title.lower()

    # Guaranteed Poster Selection
    poster_url = payload.posterUrl.strip() if payload.posterUrl and payload.posterUrl.strip() else None
    
    # 1. Match against verified known blockbuster posters
    if not poster_url and title_key in KNOWN_POSTER_MAP:
        poster_url = KNOWN_POSTER_MAP[title_key]
        
    # 2. Match against genre or industry fallbacks
    if not poster_url:
        first_genre = payload.genres[0] if payload.genres else "Default"
        poster_url = (
            GENRE_FALLBACK_POSTERS.get(first_genre)
            or GENRE_FALLBACK_POSTERS.get(payload.industry)
            or GENRE_FALLBACK_POSTERS["Default"]
        )

    # Clean display title with release year
    display_title = f"{clean_title} ({payload.year})" if not clean_title.endswith(f"({payload.year})") else clean_title

    doc = {
        "movieId": next_movie_id,
        "title": display_title,
        "cleanTitle": clean_title,
        "year": payload.year,
        "genres": payload.genres,
        "genreList": payload.genres,
        "industry": payload.industry,
        "posterUrl": poster_url,
        "overview": payload.overview or f"Exciting {payload.industry} {', '.join(payload.genres[:2]) if payload.genres else 'cinematic'} release from {payload.year}.",
        "avgRating": payload.avgRating or 4.5,
        "ratingCount": payload.ratingCount or 10,
        "isCustom": True,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }

    db.movies.insert_one(doc)
    return _movie_doc_to_response(doc)


@router.get("/custom/recent", response_model=list[MovieResponse])
def get_custom_movies():
    """Retrieve recently added custom/admin movies."""
    db = get_db()
    docs = list(db.movies.find({"isCustom": True}).sort("createdAt", -1).limit(50))
    return [_movie_doc_to_response(d) for d in docs]


@router.delete("/{movie_id}", status_code=200)
def delete_movie(movie_id: int):
    """Delete a movie by movieId."""
    db = get_db()
    res = db.movies.delete_one({"movieId": movie_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Movie not found")
    # Also delete associated user ratings for this movie
    db.ratings.delete_many({"movieId": movie_id})
    return {"message": f"Movie {movie_id} deleted successfully", "deleted": True}

