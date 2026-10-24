"""
CineMatch AI - SVD Model Training
Trains an SVD collaborative filtering model using scikit-surprise.
Saves the trained model and metadata for deployment.
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

# Fix Windows console encoding
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import types
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Python 3.13 / Windows similarities patch
if "surprise.similarities" not in sys.modules:
    try:
        from scripts.patch_surprise import SIM_CONTENT
        _sim_mod = types.ModuleType("surprise.similarities")
        exec(SIM_CONTENT, _sim_mod.__dict__)
        sys.modules["surprise.similarities"] = _sim_mod
    except Exception:
        pass

import joblib
import mlflow
import pandas as pd
from surprise import SVD, Dataset, Reader

from ml.config import (
    TRAIN_DATA_PATH,
    VALIDATION_DATA_PATH,
    MODEL_PATH,
    MODEL_METADATA_PATH,
    DATASET_STATS_PATH,
    MIN_RATING,
    MAX_RATING,
    SVD_DEFAULT_PARAMS,
    RANDOM_SEED,
    ARTIFACTS_DIR,
    MLFLOW_TRACKING_URI,
    MLFLOW_EXPERIMENT_NAME,
    MLFLOW_MODEL_NAME,
)
from ml.model_wrapper import SVDModelWrapper



def load_training_data(
    train_path: Path, val_path: Path = None, include_val: bool = False
) -> tuple[pd.DataFrame, Dataset]:
    """
    Load training data and optionally merge with validation data.
    For final training before deployment, include_val=True uses
    both train and validation data.
    """
    print("📂 Loading training data...")
    train_df = pd.read_csv(train_path)
    print(f"   Train: {len(train_df):,} ratings")

    if include_val and val_path and val_path.exists():
        val_df = pd.read_csv(val_path)
        train_df = pd.concat([train_df, val_df], ignore_index=True)
        print(f"   + Validation: {len(val_df):,} ratings")
        print(f"   = Combined: {len(train_df):,} ratings")

    reader = Reader(rating_scale=(MIN_RATING, MAX_RATING))
    dataset = Dataset.load_from_df(
        train_df[["userId", "movieId", "rating"]], reader
    )

    return train_df, dataset


def train_svd(
    dataset: Dataset,
    params: dict = None,
    random_state: int = RANDOM_SEED,
) -> SVD:
    """Train an SVD model with the given parameters."""
    if params is None:
        params = SVD_DEFAULT_PARAMS.copy()

    print(f"\n🔧 Training SVD model...")
    print(f"   Parameters: {json.dumps(params, indent=2)}")

    model = SVD(
        n_factors=params.get("n_factors", 100),
        n_epochs=params.get("n_epochs", 20),
        lr_all=params.get("lr_all", 0.005),
        reg_all=params.get("reg_all", 0.02),
        random_state=random_state,
        verbose=True,
    )

    # Build full trainset from the dataset
    trainset = dataset.build_full_trainset()

    start_time = time.time()
    model.fit(trainset)
    training_time = time.time() - start_time

    print(f"\n   ✅ Training complete in {training_time:.2f}s")
    print(f"   Users: {trainset.n_users:,}")
    print(f"   Items: {trainset.n_items:,}")
    print(f"   Ratings: {trainset.n_ratings:,}")
    print(f"   Global mean: {trainset.global_mean:.4f}")

    return model, trainset, training_time


def save_model(
    model: SVD,
    trainset,
    training_time: float,
    params: dict,
    train_df: pd.DataFrame,
    model_path: Path = MODEL_PATH,
    metadata_path: Path = MODEL_METADATA_PATH,
    model_version: str = None,
    mlflow_run_id: str = None,
) -> dict:
    """Save trained model and metadata."""
    if model_version is None:
        model_version = datetime.now(timezone.utc).strftime("v%Y%m%d_%H%M%S")

    print(f"\n💾 Saving model artifacts...")

    # Save model
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    print(f"   ✅ Model: {model_path}")

    # Collect known IDs
    known_user_ids = sorted(
        [trainset.to_raw_uid(i) for i in range(trainset.n_users)]
    )
    known_movie_ids = sorted(
        [trainset.to_raw_iid(i) for i in range(trainset.n_items)]
    )

    # Load dataset stats if available
    dataset_version = "unknown"
    if DATASET_STATS_PATH.exists():
        with open(DATASET_STATS_PATH) as f:
            ds_stats = json.load(f)
            dataset_version = ds_stats.get("processed_at", "unknown")

    # Build metadata
    metadata = {
        "model_version": model_version,
        "algorithm": "SVD",
        "library": "scikit-surprise",
        "parameters": params,
        "training_time_seconds": round(training_time, 2),
        "trainset_stats": {
            "n_users": trainset.n_users,
            "n_items": trainset.n_items,
            "n_ratings": trainset.n_ratings,
            "global_mean": round(trainset.global_mean, 6),
        },
        "known_user_ids": known_user_ids,
        "known_movie_ids": known_movie_ids,
        "dataset_version": dataset_version,
        "rating_scale": [MIN_RATING, MAX_RATING],
        "random_seed": RANDOM_SEED,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "artifact_path": str(model_path),
        "mlflow_run_id": mlflow_run_id,
    }

    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2, default=str)
    print(f"   ✅ Metadata: {metadata_path}")

    return metadata


def main():
    print("=" * 60)
    print("  CineMatch AI - SVD Model Training (with MLflow)")
    print("=" * 60)
    print()

    # Check preprocessed data exists
    if not TRAIN_DATA_PATH.exists():
        print("❌ Training data not found! Run preprocess.py first.")
        sys.exit(1)

    # Initialize MLflow tracking
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)

    run_name = f"train_svd_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    with mlflow.start_run(run_name=run_name) as run:
        print(f"🔬 MLflow Tracking URI: {MLFLOW_TRACKING_URI}")
        print(f"🔬 MLflow Experiment:   {MLFLOW_EXPERIMENT_NAME}")
        print(f"🔬 MLflow Run ID:       {run.info.run_id}")

        mlflow.set_tag("pipeline_stage", "training")
        mlflow.set_tag("model_type", "SVD")
        mlflow.set_tag("library", "scikit-surprise")

        # Load data (train only — validation reserved for tuning/eval)
        train_df, dataset = load_training_data(TRAIN_DATA_PATH)

        # Train with default parameters
        params = SVD_DEFAULT_PARAMS.copy()
        mlflow.log_params(params)

        model, trainset, training_time = train_svd(dataset, params)

        # Log training metrics to MLflow
        mlflow.log_metrics({
            "train_ratings_count": float(trainset.n_ratings),
            "train_users_count": float(trainset.n_users),
            "train_items_count": float(trainset.n_items),
            "train_global_mean": float(trainset.global_mean),
            "training_time_seconds": float(training_time),
        })

        # Save local artifacts
        metadata = save_model(
            model=model,
            trainset=trainset,
            training_time=training_time,
            params=params,
            train_df=train_df,
            mlflow_run_id=run.info.run_id,
        )

        # Log artifacts to MLflow
        mlflow.log_artifact(str(MODEL_PATH), artifact_path="model")
        mlflow.log_artifact(str(MODEL_METADATA_PATH), artifact_path="metadata")
        if DATASET_STATS_PATH.exists():
            mlflow.log_artifact(str(DATASET_STATS_PATH), artifact_path="metadata")

        # Register model to MLflow Model Registry
        try:
            mlflow.pyfunc.log_model(
                artifact_path="svd_model",
                python_model=SVDModelWrapper(),
                artifacts={
                    "model_file": str(MODEL_PATH),
                    "metadata_file": str(MODEL_METADATA_PATH),
                },
                registered_model_name=MLFLOW_MODEL_NAME,
            )
            print(f"   Registered to MLflow Model Registry: '{MLFLOW_MODEL_NAME}'")
        except Exception as e:
            print(f"   [WARN] Could not register to Model Registry: {e}")

        print(f"\n🎉 Model training complete and logged to MLflow!")
        print(f"   Run ID: {run.info.run_id}")
        print(f"   Version: {metadata['model_version']}")
        print(f"   Known users: {len(metadata['known_user_ids']):,}")
        print(f"   Known movies: {len(metadata['known_movie_ids']):,}")



if __name__ == "__main__":
    main()
