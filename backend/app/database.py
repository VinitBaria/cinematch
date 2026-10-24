"""
CineMatch AI - MongoDB Database Connection & Index Setup
"""
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.database import Database
from .config import settings

client: MongoClient = None
db: Database = None


def connect_db():
    global client, db
    client = MongoClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB_NAME]
    _ensure_indexes()
    print(f"[DB] Connected to MongoDB: {settings.MONGODB_DB_NAME}")
    return db


def get_db() -> Database:
    global db
    if db is None:
        connect_db()
    return db


def close_db():
    global client
    if client:
        client.close()


def _ensure_indexes():
    """Create required indexes."""
    global db
    # Users
    db.users.create_index("email", unique=True)
    db.users.create_index("userId", unique=True)

    # Movies
    db.movies.create_index("movieId", unique=True)
    db.movies.create_index("title")
    db.movies.create_index("year")
    db.movies.create_index([("avgRating", DESCENDING)])
    db.movies.create_index([("ratingCount", DESCENDING)])

    # Ratings - compound unique index
    db.ratings.create_index(
        [("userId", ASCENDING), ("movieId", ASCENDING)], unique=True
    )
    db.ratings.create_index("userId")
    db.ratings.create_index("movieId")

    # Recommendation events
    db.recommendation_events.create_index("userId")
    db.recommendation_events.create_index("timestamp")

    # Model deployments
    db.model_deployments.create_index("modelVersion", unique=True)
    db.model_deployments.create_index([("deployedAt", DESCENDING)])
