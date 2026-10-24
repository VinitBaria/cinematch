"""
CineMatch AI - Hyperparameter Tuning
Searches over SVD configurations, evaluates on validation set,
selects best by NDCG@10 (primary), with RMSE and training latency
as secondary constraints.

Does NOT touch the test set for selection — only for final evaluation
after the best config is chosen.
"""

import json
import sys
import time
import itertools
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
from surprise import SVD, Dataset, Reader
from sklearn.metrics import mean_squared_error

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml.config import (
    TRAIN_DATA_PATH,
    VALIDATION_DATA_PATH,
    MODEL_PATH,
    MODEL_METADATA_PATH,
    TUNING_RESULTS_PATH,
    TUNING_PARAM_GRID,
    MIN_RATING,
    MAX_RATING,
    RELEVANCE_THRESHOLD,
    TOP_K,
    RANDOM_SEED,
    ARTIFACTS_DIR,
    MLFLOW_TRACKING_URI,
    MLFLOW_EXPERIMENT_NAME,
    MLFLOW_MODEL_NAME,
)
from ml.model_wrapper import SVDModelWrapper



def compute_val_ndcg(
    model, val_df: pd.DataFrame, train_df: pd.DataFrame,
    k: int = TOP_K, threshold: float = RELEVANCE_THRESHOLD,
) -> float:
    """Compute NDCG@K on validation set (same logic as evaluate.py)."""
    train_user_items = defaultdict(set)
    for _, row in train_df.iterrows():
        train_user_items[int(row["userId"])].add(int(row["movieId"]))

    test_user_items = defaultdict(list)
    for _, row in val_df.iterrows():
        test_user_items[int(row["userId"])].append(
            (int(row["movieId"]), float(row["rating"]))
        )

    ndcgs = []
    for uid, items in test_user_items.items():
        items = [(iid, r) for iid, r in items if iid not in train_user_items.get(uid, set())]
        if not items:
            continue

        n_relevant = sum(1 for _, r in items if r >= threshold)
        if n_relevant == 0:
            continue

        preds = [(iid, model.predict(uid, iid).est, r) for iid, r in items]
        preds.sort(key=lambda x: x[1], reverse=True)
        top_k = preds[:k]

        dcg = sum(
            (1.0 if r >= threshold else 0.0) / np.log2(rank + 2)
            for rank, (_, _, r) in enumerate(top_k)
        )
        ideal = sorted(items, key=lambda x: x[1], reverse=True)[:k]
        idcg = sum(
            (1.0 if r >= threshold else 0.0) / np.log2(rank + 2)
            for rank, (_, r) in enumerate(ideal)
        )
        ndcgs.append(dcg / idcg if idcg > 0 else 0.0)

    return float(np.mean(ndcgs)) if ndcgs else 0.0


def compute_val_rmse(model, val_df: pd.DataFrame) -> float:
    """Compute RMSE on validation set."""
    preds = [model.predict(int(r["userId"]), int(r["movieId"])).est for _, r in val_df.iterrows()]
    actuals = val_df["rating"].values
    return float(np.sqrt(mean_squared_error(actuals, preds)))


def generate_param_combinations(grid: dict) -> list[dict]:
    """Generate all combinations from the parameter grid."""
    keys = list(grid.keys())
    values = list(grid.values())
    combos = []
    for vals in itertools.product(*values):
        combos.append(dict(zip(keys, vals)))
    return combos


def main():
    print("=" * 60)
    print("  CineMatch AI - Hyperparameter Tuning")
    print("=" * 60)
    print()

    np.random.seed(RANDOM_SEED)

    # Load data
    if not TRAIN_DATA_PATH.exists() or not VALIDATION_DATA_PATH.exists():
        print("❌ Processed data not found! Run preprocess.py first.")
        sys.exit(1)

    train_df = pd.read_csv(TRAIN_DATA_PATH)
    val_df = pd.read_csv(VALIDATION_DATA_PATH)
    print(f"   Train: {len(train_df):,} ratings")
    print(f"   Validation: {len(val_df):,} ratings")

    reader = Reader(rating_scale=(MIN_RATING, MAX_RATING))
    train_dataset = Dataset.load_from_df(
        train_df[["userId", "movieId", "rating"]], reader
    )
    trainset = train_dataset.build_full_trainset()

    # Generate configurations
    combos = generate_param_combinations(TUNING_PARAM_GRID)
    print(f"\n🔍 Tuning {len(combos)} configurations...")
    print(f"   Primary metric: NDCG@{TOP_K}")
    print(f"   Secondary: RMSE, training time")
    print()

    # Initialize MLflow tracking
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)

    parent_run_name = f"tune_svd_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    with mlflow.start_run(run_name=parent_run_name) as parent_run:
        print(f"🔬 MLflow Parent Run: {parent_run.info.run_id}")
        mlflow.set_tag("pipeline_stage", "hyperparameter_tuning")
        mlflow.set_tag("selection_metric", f"NDCG@{TOP_K}")
        mlflow.log_params({
            "total_configurations": len(combos),
            "top_k": TOP_K,
            "relevance_threshold": RELEVANCE_THRESHOLD,
            "random_seed": RANDOM_SEED,
        })

        results = []

        for i, params in enumerate(combos, 1):
            print(f"--- Config {i}/{len(combos)}: {params}")

            child_run_name = f"trial_{i}_f{params['n_factors']}_e{params['n_epochs']}_lr{params['lr_all']}_reg{params['reg_all']}"
            with mlflow.start_run(run_name=child_run_name, nested=True) as child_run:
                # Log hyperparameters for this trial
                mlflow.log_params(params)

                model = SVD(
                    n_factors=params["n_factors"],
                    n_epochs=params["n_epochs"],
                    lr_all=params["lr_all"],
                    reg_all=params["reg_all"],
                    random_state=RANDOM_SEED,
                    verbose=False,
                )

                start = time.time()
                model.fit(trainset)
                train_time = time.time() - start

                # Evaluate on validation
                val_rmse = compute_val_rmse(model, val_df)
                val_ndcg = compute_val_ndcg(model, val_df, train_df)

                # Log metrics for this trial
                mlflow.log_metrics({
                    f"val_ndcg_at_{TOP_K}": float(val_ndcg),
                    "val_rmse": float(val_rmse),
                    "train_time_seconds": float(train_time),
                })

                result = {
                    "trial": i,
                    "params": params,
                    "val_rmse": round(val_rmse, 4),
                    "val_ndcg": round(val_ndcg, 4),
                    "train_time_seconds": round(train_time, 2),
                    "mlflow_trial_run_id": child_run.info.run_id,
                }
                results.append(result)

                print(f"    NDCG@{TOP_K}: {val_ndcg:.4f}  |  RMSE: {val_rmse:.4f}  |  Time: {train_time:.1f}s")

        # Select best by NDCG@K (primary)
        results.sort(key=lambda x: x["val_ndcg"], reverse=True)
        best = results[0]

        print(f"\n🏆 Best configuration:")
        print(f"   Params: {best['params']}")
        print(f"   NDCG@{TOP_K}: {best['val_ndcg']:.4f}")
        print(f"   RMSE: {best['val_rmse']:.4f}")
        print(f"   Time: {best['train_time_seconds']:.2f}s")
        print(f"   Trial Run ID: {best.get('mlflow_trial_run_id')}")

        # Log best configuration and metrics to parent run
        mlflow.log_metrics({
            f"best_val_ndcg_at_{TOP_K}": float(best["val_ndcg"]),
            "best_val_rmse": float(best["val_rmse"]),
            "best_train_time_seconds": float(best["train_time_seconds"]),
        })
        mlflow.set_tag("best_trial_run_id", str(best.get("mlflow_trial_run_id")))
        mlflow.log_params({f"best_{k}": v for k, v in best["params"].items()})

        # Refit best model on train data (NOT test)
        print(f"\n🔧 Refitting best model on training data...")
        best_model = SVD(
            n_factors=best["params"]["n_factors"],
            n_epochs=best["params"]["n_epochs"],
            lr_all=best["params"]["lr_all"],
            reg_all=best["params"]["reg_all"],
            random_state=RANDOM_SEED,
            verbose=True,
        )
        best_model.fit(trainset)

        # Save best model
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        model_version = datetime.now(timezone.utc).strftime("v%Y%m%d_%H%M%S_tuned")
        joblib.dump(best_model, MODEL_PATH)

        # Save metadata
        known_user_ids = sorted([trainset.to_raw_uid(i) for i in range(trainset.n_users)])
        known_movie_ids = sorted([trainset.to_raw_iid(i) for i in range(trainset.n_items)])

        metadata = {
            "model_version": model_version,
            "algorithm": "SVD",
            "library": "scikit-surprise",
            "parameters": best["params"],
            "tuned": True,
            "selection_metric": f"NDCG@{TOP_K}",
            "best_val_ndcg": best["val_ndcg"],
            "best_val_rmse": best["val_rmse"],
            "trainset_stats": {
                "n_users": trainset.n_users,
                "n_items": trainset.n_items,
                "n_ratings": trainset.n_ratings,
                "global_mean": round(trainset.global_mean, 6),
            },
            "known_user_ids": known_user_ids,
            "known_movie_ids": known_movie_ids,
            "rating_scale": [MIN_RATING, MAX_RATING],
            "random_seed": RANDOM_SEED,
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "artifact_path": str(MODEL_PATH),
            "mlflow_parent_run_id": parent_run.info.run_id,
            "mlflow_best_trial_run_id": best.get("mlflow_trial_run_id"),
        }

        with open(MODEL_METADATA_PATH, "w") as f:
            json.dump(metadata, f, indent=2, default=str)

        # Save all tuning results
        tuning_output = {
            "total_configurations": len(combos),
            "param_grid": TUNING_PARAM_GRID,
            "best_config": best,
            "all_results": results,
            "selection_criteria": {
                "primary": f"NDCG@{TOP_K} (highest)",
                "secondary": ["RMSE (lowest)", "training_time (lowest)"],
                "test_set_usage": "NOT used for selection. Test set reserved for final evaluation only.",
            },
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "mlflow_parent_run_id": parent_run.info.run_id,
        }
        with open(TUNING_RESULTS_PATH, "w") as f:
            json.dump(tuning_output, f, indent=2)

        # Log artifacts to MLflow parent run
        mlflow.log_artifact(str(MODEL_PATH), artifact_path="model")
        mlflow.log_artifact(str(MODEL_METADATA_PATH), artifact_path="metadata")
        mlflow.log_artifact(str(TUNING_RESULTS_PATH), artifact_path="tuning")

        # Register best tuned model to MLflow Model Registry
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
            print(f"   Registered best tuned model to Model Registry: '{MLFLOW_MODEL_NAME}'")
        except Exception as e:
            print(f"   [WARN] Could not register to Model Registry: {e}")

        print(f"\n💾 Saved locally and logged to MLflow:")
        print(f"   Model: {MODEL_PATH}")
        print(f"   Metadata: {MODEL_METADATA_PATH}")
        print(f"   Tuning results: {TUNING_RESULTS_PATH}")
        print(f"   MLflow Parent Run ID: {parent_run.info.run_id}")
        print(f"\n🎉 Tuning complete! Run evaluate.py to get final test metrics.")


if __name__ == "__main__":
    main()
