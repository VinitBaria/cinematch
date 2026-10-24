"""
CineMatch AI - ML Configuration
Centralized configuration for all ML pipeline parameters.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ML_DIR = PROJECT_ROOT / "ml"
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
ARTIFACTS_DIR = ML_DIR / "artifacts"

# Ensure directories exist
for d in [RAW_DATA_DIR, PROCESSED_DATA_DIR, ARTIFACTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ──────────────────────────────────────────────
# Dataset
# ──────────────────────────────────────────────
MOVIELENS_URL = "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip"
MOVIELENS_ZIP = RAW_DATA_DIR / "ml-latest-small.zip"
MOVIELENS_DIR = RAW_DATA_DIR / "ml-latest-small"

RATINGS_CSV = MOVIELENS_DIR / "ratings.csv"
MOVIES_CSV = MOVIELENS_DIR / "movies.csv"
LINKS_CSV = MOVIELENS_DIR / "links.csv"

# Required columns
RATINGS_REQUIRED_COLS = ["userId", "movieId", "rating", "timestamp"]
MOVIES_REQUIRED_COLS = ["movieId", "title", "genres"]
LINKS_REQUIRED_COLS = ["movieId", "imdbId", "tmdbId"]

# Rating constraints
MIN_RATING = 0.5
MAX_RATING = 5.0
RATING_STEP = 0.5

# ──────────────────────────────────────────────
# Data Splits (chronological)
# ──────────────────────────────────────────────
TRAIN_RATIO = 0.70
VALIDATION_RATIO = 0.15
TEST_RATIO = 0.15

# Processed file paths
TRAIN_DATA_PATH = PROCESSED_DATA_DIR / "train_ratings.csv"
VALIDATION_DATA_PATH = PROCESSED_DATA_DIR / "validation_ratings.csv"
TEST_DATA_PATH = PROCESSED_DATA_DIR / "test_ratings.csv"
MOVIES_PROCESSED_PATH = PROCESSED_DATA_DIR / "movies_processed.csv"
DATASET_STATS_PATH = PROCESSED_DATA_DIR / "dataset_stats.json"
ID_MAPPINGS_PATH = PROCESSED_DATA_DIR / "id_mappings.json"

# ──────────────────────────────────────────────
# SVD Model Defaults
# ──────────────────────────────────────────────
SVD_DEFAULT_PARAMS = {
    "n_factors": 100,
    "n_epochs": 20,
    "lr_all": 0.005,
    "reg_all": 0.02,
    "random_state": 42,
}

# ──────────────────────────────────────────────
# Tuning Search Space
# ──────────────────────────────────────────────
TUNING_PARAM_GRID = {
    "n_factors": [50, 100, 150],
    "n_epochs": [20, 30, 40],
    "lr_all": [0.002, 0.005, 0.01],
    "reg_all": [0.02, 0.05, 0.1],
}

# ──────────────────────────────────────────────
# Evaluation
# ──────────────────────────────────────────────
RELEVANCE_THRESHOLD = 4.0  # rating >= this is "relevant"
TOP_K = 10
RANDOM_SEED = 42

# ──────────────────────────────────────────────
# Model Artifacts
# ──────────────────────────────────────────────
MODEL_PATH = ARTIFACTS_DIR / "svd_model.joblib"
MODEL_METADATA_PATH = ARTIFACTS_DIR / "model_metadata.json"
EVALUATION_METRICS_PATH = ARTIFACTS_DIR / "evaluation_metrics.json"
TUNING_RESULTS_PATH = ARTIFACTS_DIR / "tuning_results.json"

# ──────────────────────────────────────────────
# Cold Start
# ──────────────────────────────────────────────
POPULARITY_MIN_RATINGS = 10  # min ratings for a movie to appear in popularity list
NEIGHBOR_MIN_OVERLAP = 3     # min shared rated movies for neighbor similarity
NEIGHBOR_TOP_K = 30          # number of similar users to consider
NEIGHBOR_MIN_SIMILARITY = 0.1

# ──────────────────────────────────────────────
# App User ID Offset
# Prevents collision between MovieLens userIds and
# application-generated userIds in MongoDB.
# App users start at this offset.
# ──────────────────────────────────────────────
APP_USER_ID_OFFSET = 1_000_000

# ──────────────────────────────────────────────
# TMDB
# ──────────────────────────────────────────────
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p"
TMDB_POSTER_SIZE = "w500"

# ──────────────────────────────────────────────
# MLflow Configuration
# ──────────────────────────────────────────────
MLFLOW_DB_PATH = (ML_DIR / "mlflow.db").resolve()
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", f"sqlite:///{MLFLOW_DB_PATH.as_posix()}")
MLFLOW_EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "cinematch-svd-recommender")
MLFLOW_MODEL_NAME = os.getenv("MLFLOW_MODEL_NAME", "CineMatch-SVD")


