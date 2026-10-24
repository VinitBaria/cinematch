"""
CineMatch AI - Pydantic Schemas
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ── Auth ──
class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    userId: int
    name: str
    email: str
    token: str

class UserProfile(BaseModel):
    userId: int
    name: str
    email: str
    ratingCount: int = 0
    createdAt: Optional[str] = None


# ── Movies ──
class MovieResponse(BaseModel):
    movieId: int
    title: str
    cleanTitle: Optional[str] = None
    year: Optional[float] = None
    genres: Optional[List[str]] = []
    industry: Optional[str] = None
    posterUrl: Optional[str] = None
    overview: Optional[str] = None
    tmdbId: Optional[float] = None
    avgRating: Optional[float] = None
    ratingCount: Optional[int] = 0
    userRating: Optional[float] = None

class MovieCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    year: int = Field(default=2024, ge=1900, le=2035)
    genres: List[str] = Field(default_factory=list)
    industry: str = Field(default="Bollywood")
    overview: Optional[str] = None
    posterUrl: Optional[str] = None
    avgRating: Optional[float] = Field(default=4.5, ge=0.5, le=5.0)
    ratingCount: Optional[int] = Field(default=10, ge=0)

class MovieListResponse(BaseModel):
    movies: List[MovieResponse]
    total: int
    page: int
    pageSize: int


# ── Ratings ──
class RatingRequest(BaseModel):
    movieId: int
    rating: float = Field(..., ge=0.5, le=5.0)

class RatingResponse(BaseModel):
    userId: int
    movieId: int
    rating: float
    title: Optional[str] = None
    posterUrl: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None


# ── Recommendations ──
class RecommendationItem(BaseModel):
    movieId: int
    title: Optional[str] = None
    cleanTitle: Optional[str] = None
    year: Optional[float] = None
    genres: Optional[List[str]] = []
    posterUrl: Optional[str] = None
    overview: Optional[str] = None
    predictedRating: Optional[float] = None
    popularityScore: Optional[float] = None
    avgRating: Optional[float] = None
    ratingCount: Optional[int] = None
    recommendationStrategy: str
    modelVersion: Optional[str] = None

class RecommendationResponse(BaseModel):
    recommendations: List[RecommendationItem]
    strategy: str
    modelVersion: Optional[str] = None
    userId: int


# ── Model ──
class ModelInfoResponse(BaseModel):
    modelVersion: str
    algorithm: str
    parameters: dict
    trainsetStats: dict
    trainedAt: str
    knownUsers: int
    knownMovies: int
