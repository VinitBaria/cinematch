"""
CineMatch AI - Model Evaluation
Evaluates the trained SVD model on the test set using:
  - RMSE, MAE (prediction accuracy)
  - Precision@K, Recall@K, NDCG@K (ranking quality)

Methodology notes:
- Ranking metrics are computed per-user over the *test set items* only.
  We do NOT sample random negatives (no all-item candidate pool).
  This means metrics reflect how well the model ranks items the user
  actually rated in the test period, not all catalog items.
- A "relevant" item is one rated >= RELEVANCE_THRESHOLD.
- Train interactions are excluded from candidate sets automatically
  because train/val/test are disjoint by construction.
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

# Fix Windows console encoding
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import joblib
import mlflow
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml.config import (
    TRAIN_DATA_PATH,
    TEST_DATA_PATH,
    MODEL_PATH,
    MODEL_METADATA_PATH,
    EVALUATION_METRICS_PATH,
    RELEVANCE_THRESHOLD,
    TOP_K,
    RANDOM_SEED,
    ARTIFACTS_DIR,
    MLFLOW_TRACKING_URI,
    MLFLOW_EXPERIMENT_NAME,
)


def load_model(model_path: Path):
    """Load trained SVD model."""
    print("📂 Loading trained model...")
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found at {model_path}. Run train.py first.")
    model = joblib.load(model_path)
    print("   ✅ Model loaded")
    return model


def load_metadata(metadata_path: Path) -> dict:
    """Load model metadata."""
    if not metadata_path.exists():
        return {}
    with open(metadata_path) as f:
        return json.load(f)


def compute_prediction_metrics(
    model, test_df: pd.DataFrame
) -> tuple[float, float, list]:
    """Compute RMSE and MAE on test set predictions."""
    print("\n📊 Computing prediction metrics (RMSE, MAE)...")

    predictions = []
    actuals = []
    pred_details = []

    for _, row in test_df.iterrows():
        uid = int(row["userId"])
        iid = int(row["movieId"])
        true_r = float(row["rating"])

        pred = model.predict(uid, iid)
        predictions.append(pred.est)
        actuals.append(true_r)
        pred_details.append({
            "userId": uid,
            "movieId": iid,
            "true_rating": true_r,
            "predicted_rating": pred.est,
        })

    rmse = float(np.sqrt(mean_squared_error(actuals, predictions)))
    mae = float(mean_absolute_error(actuals, predictions))

    print(f"   RMSE: {rmse:.4f}")
    print(f"   MAE:  {mae:.4f}")

    return rmse, mae, pred_details


def compute_ranking_metrics(
    model,
    test_df: pd.DataFrame,
    train_df: pd.DataFrame,
    k: int = TOP_K,
    threshold: float = RELEVANCE_THRESHOLD,
) -> dict:
    """
    Compute Precision@K, Recall@K, and NDCG@K per user,
    then average across users.

    For each user:
    1. Gather their test-set (movieId, true_rating) pairs.
    2. Predict ratings for those test-set movies.
    3. Rank by predicted rating, take top K.
    4. Compute precision, recall, NDCG using the relevance threshold.
    """
    print(f"\n📊 Computing ranking metrics (K={k}, threshold={threshold})...")

    # Build set of train interactions per user to verify exclusion
    train_user_items = defaultdict(set)
    for _, row in train_df.iterrows():
        train_user_items[int(row["userId"])].add(int(row["movieId"]))

    # Group test ratings by user
    test_user_items = defaultdict(list)
    for _, row in test_df.iterrows():
        test_user_items[int(row["userId"])].append(
            (int(row["movieId"]), float(row["rating"]))
        )

    precisions = []
    recalls = []
    ndcgs = []
    user_count = 0

    for uid, items in test_user_items.items():
        # Filter out any items that were somehow in train (shouldn't happen, but safety)
        items = [(iid, r) for iid, r in items if iid not in train_user_items.get(uid, set())]

        if len(items) == 0:
            continue

        # Predict ratings for test items
        preds = []
        for iid, true_r in items:
            est = model.predict(uid, iid).est
            preds.append((iid, est, true_r))

        # Sort by predicted rating descending
        preds.sort(key=lambda x: x[1], reverse=True)
        top_k_preds = preds[:k]

        # Relevant items in the full test set for this user
        n_relevant = sum(1 for _, r in items if r >= threshold)

        if n_relevant == 0:
            # Skip users with no relevant items in test set for ranking metrics
            continue

        # Precision@K: fraction of top-K that are relevant
        n_relevant_in_topk = sum(1 for _, _, r in top_k_preds if r >= threshold)
        precision = n_relevant_in_topk / k
        precisions.append(precision)

        # Recall@K: fraction of all relevant items found in top-K
        recall = n_relevant_in_topk / n_relevant
        recalls.append(recall)

        # NDCG@K
        dcg = 0.0
        for rank, (_, _, true_r) in enumerate(top_k_preds, 1):
            rel = 1.0 if true_r >= threshold else 0.0
            dcg += rel / np.log2(rank + 1)

        # Ideal DCG: sort all test items by true rating, take top K
        ideal_items = sorted(items, key=lambda x: x[1], reverse=True)[:k]
        idcg = 0.0
        for rank, (_, true_r) in enumerate(ideal_items, 1):
            rel = 1.0 if true_r >= threshold else 0.0
            idcg += rel / np.log2(rank + 1)

        ndcg = dcg / idcg if idcg > 0 else 0.0
        ndcgs.append(ndcg)
        user_count += 1

    avg_precision = float(np.mean(precisions)) if precisions else 0.0
    avg_recall = float(np.mean(recalls)) if recalls else 0.0
    avg_ndcg = float(np.mean(ndcgs)) if ndcgs else 0.0

    print(f"   Precision@{k}: {avg_precision:.4f}")
    print(f"   Recall@{k}:    {avg_recall:.4f}")
    print(f"   NDCG@{k}:      {avg_ndcg:.4f}")
    print(f"   Users evaluated: {user_count:,}")

    return {
        f"precision_at_{k}": avg_precision,
        f"recall_at_{k}": avg_recall,
        f"ndcg_at_{k}": avg_ndcg,
        "users_evaluated": user_count,
        "relevance_threshold": threshold,
        "k": k,
        "note": (
            "Ranking metrics are computed over each user's test-set items only, "
            "not over all catalog items. No negative sampling is used. "
            "This means Precision@K and Recall@K reflect the model's ability "
            "to rank truly-relevant test items higher, among a typically small "
            "candidate set. Values are not directly comparable to full-catalog metrics."
        ),
    }


def main():
    print("=" * 60)
    print("  CineMatch AI - Model Evaluation")
    print("=" * 60)
    print()

    np.random.seed(RANDOM_SEED)

    # Load model
    model = load_model(MODEL_PATH)
    metadata = load_metadata(MODEL_METADATA_PATH)

    # Load data
    if not TEST_DATA_PATH.exists():
        print("❌ Test data not found! Run preprocess.py first.")
        sys.exit(1)

    test_df = pd.read_csv(TEST_DATA_PATH)
    train_df = pd.read_csv(TRAIN_DATA_PATH)
    print(f"   Test ratings: {len(test_df):,}")
    print(f"   Train ratings: {len(train_df):,}")

    start_time = time.time()

    # Prediction metrics
    rmse, mae, _ = compute_prediction_metrics(model, test_df)

    # Ranking metrics
    ranking = compute_ranking_metrics(model, test_df, train_df)

    eval_time = time.time() - start_time

    # Compile results
    results = {
        "model_version": metadata.get("model_version", "unknown"),
        "evaluation_set": "test",
        "prediction_metrics": {
            "rmse": rmse,
            "mae": mae,
            "n_predictions": len(test_df),
        },
        "ranking_metrics": ranking,
        "evaluation_time_seconds": round(eval_time, 2),
        "random_seed": RANDOM_SEED,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }

    # Save
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(EVALUATION_METRICS_PATH, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Saved evaluation metrics: {EVALUATION_METRICS_PATH}")

    # Log to MLflow
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)

    train_run_id = metadata.get("mlflow_run_id") or metadata.get("mlflow_parent_run_id")
    eval_run_name = f"eval_{metadata.get('model_version', 'model')}"

    with mlflow.start_run(run_name=eval_run_name) as run:
        mlflow.set_tag("pipeline_stage", "evaluation")
        mlflow.set_tag("evaluation_set", "test")
        mlflow.set_tag("model_version", str(metadata.get("model_version", "unknown")))
        if train_run_id:
            mlflow.set_tag("trained_model_run_id", str(train_run_id))

        k = ranking["k"]
        mlflow.log_metrics({
            "test_rmse": float(rmse),
            "test_mae": float(mae),
            f"test_precision_at_{k}": float(ranking[f"precision_at_{k}"]),
            f"test_recall_at_{k}": float(ranking[f"recall_at_{k}"]),
            f"test_ndcg_at_{k}": float(ranking[f"ndcg_at_{k}"]),
            "test_users_evaluated": float(ranking.get("users_evaluated", 0)),
            "evaluation_time_seconds": float(eval_time),
        })

        mlflow.log_artifact(str(EVALUATION_METRICS_PATH), artifact_path="evaluation")
        print(f"🔬 Evaluation logged to MLflow Run: {run.info.run_id}")

    print(f"\n🎉 Evaluation complete in {eval_time:.1f}s")


if __name__ == "__main__":
    main()
