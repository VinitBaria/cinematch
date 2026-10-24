"""
CineMatch AI - Backend API Tests
Tests:
  - App root & health check
  - Model info endpoint
  - Password hashing & JWT generation/validation
  - Pydantic schema validation
"""
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.main import app
from backend.app.security.auth import hash_password, verify_password, create_access_token, decode_token
from backend.app.schemas.schemas import RegisterRequest, MovieResponse, RecommendationItem

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "CineMatch AI API"
    assert data["status"] == "online"


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "mlModel" in data
    assert data["mlModel"]["loaded"] is True
    assert data["mlModel"]["knownUsers"] > 0
    assert data["mlModel"]["knownMovies"] > 0


def test_model_info_endpoint():
    response = client.get("/api/model/info")
    assert response.status_code == 200
    data = response.json()
    assert data["algorithm"] == "SVD"
    assert "parameters" in data
    assert data["knownUsers"] > 0
    assert data["knownMovies"] > 0


def test_password_security():
    password = "SuperSecretPassword123!"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_token_flow():
    user_payload = {"sub": "1", "email": "test@cinematch.ai"}
    token = create_access_token(user_payload)
    assert isinstance(token, str)
    decoded = decode_token(token)
    assert decoded["sub"] == "1"
    assert decoded["email"] == "test@cinematch.ai"


def test_recommendations_endpoint():
    response = client.get("/api/recommendations?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data
    assert "strategy" in data


def test_onboarding_picks_endpoint():
    response = client.get("/api/movies/onboarding-picks?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_ratings_endpoint():
    token = create_access_token({"userId": 1, "email": "demo@cinematch.ai"})
    response = client.get("/api/ratings?limit=200&skip=0", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)



def test_schema_serialization():
    movie = MovieResponse(
        movieId=1,
        title="Toy Story (1995)",
        cleanTitle="Toy Story",
        year=1995,
        genres=["Animation", "Adventure", "Comedy"],
        avgRating=4.5,
        ratingCount=120,
    )
    assert movie.movieId == 1
    assert movie.cleanTitle == "Toy Story"
    assert len(movie.genres) == 3
