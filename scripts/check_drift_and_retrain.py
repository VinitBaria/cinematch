"""
CineMatch AI - Continuous Training (CT) & Automated Retraining Pipeline
Workflow:
1. Runs Data Drift Analysis (KS-test, PSI, vocabulary drift)
2. If Drift is Detected:
   a. Extracts fresh production ratings from MongoDB
   b. Merges fresh ratings into train_ratings.csv
   c. Retrains SVD model via ml/train.py
   d. Registers new version in MLflow Model Registry
   e. Updates Prometheus metrics and triggers deployment notification
3. If No Drift:
   - Logs that model is performing optimally and exits cleanly.
"""

import sys
import os
import json
import time
import argparse
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd

# Fix Windows console encoding
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ml.config import (
    TRAIN_DATA_PATH,
    MODEL_METADATA_PATH,
    ARTIFACTS_DIR,
    MLFLOW_TRACKING_URI,
    MLFLOW_MODEL_NAME,
)
from ml.drift_detector import run_drift_analysis, DRIFT_STATUS_FILE


def export_and_merge_production_ratings(db_client=None) -> int:
    """
    Exports all ratings from MongoDB and merges with train_ratings.csv.
    Ensures new user ratings are incorporated into future model training.
    """
    print("\n📥 Merging production ratings from MongoDB into training dataset...")
    try:
        from backend.app.database import connect_db, get_db
        connect_db()
        db = get_db()
        mongo_ratings = list(db.ratings.find({}, {"_id": 0, "userId": 1, "movieId": 1, "rating": 1, "createdAt": 1, "timestamp": 1}))

        if not mongo_ratings:
            print("ℹ️ No new ratings found in MongoDB.")
            return 0

        new_df = pd.DataFrame(mongo_ratings)
        # Ensure correct column types
        new_df["userId"] = new_df["userId"].astype(int)
        new_df["movieId"] = new_df["movieId"].astype(int)
        new_df["rating"] = new_df["rating"].astype(float)
        if "timestamp" not in new_df.columns or new_df["timestamp"].isnull().all():
            new_df["timestamp"] = int(time.time())
        else:
            new_df["timestamp"] = new_df["timestamp"].fillna(int(time.time())).astype(int)

        existing_df = pd.read_csv(TRAIN_DATA_PATH)
        print(f"  Existing training dataset size: {len(existing_df):,} rows")

        # Combine and drop duplicates (keep latest rating for a user-movie pair)
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        combined_df = combined_df.drop_duplicates(subset=["userId", "movieId"], keep="last")

        # Save back to train_ratings.csv
        combined_df.to_csv(TRAIN_DATA_PATH, index=False)
        added_count = len(combined_df) - len(existing_df)
        print(f"  Updated training dataset size:  {len(combined_df):,} rows (+{added_count:,} new/updated)")
        return added_count
    except Exception as e:
        print(f"[WARN] Error merging ratings from MongoDB: {e}")
        return 0


def trigger_retraining(reason: str = "data_drift"):
    """
    Triggers model training by running train.py with MLflow registration.
    """
    print("\n🚀 Executing Model Retraining Pipeline...")
    import subprocess
    cmd = [sys.executable, str(PROJECT_ROOT / "ml" / "train.py")]
    env = os.environ.copy()
    env["MLFLOW_TRIGGER_REASON"] = reason

    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(result.stdout)
    if result.returncode != 0:
        print(f"❌ Retraining failed with error:\n{result.stderr}")
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Continuous Training (CT) Orchestrator")
    parser.add_argument("--force-retrain", action="store_true", help="Force retraining regardless of drift status")
    parser.add_argument("--simulate-drift", action="store_true", help="Simulate drift to test automated retraining")
    args = parser.parse_args()

    print("=" * 65)
    print(" CineMatch AI - Continuous Training (CT) Orchestrator")
    print("=" * 65)

    # 1. Evaluate Data Drift
    drift_report = run_drift_analysis(simulate=args.simulate_drift)
    drift_detected = drift_report.get("drift_detected", False)

    if not drift_detected and not args.force_retrain:
        print("\n✅ DATA IS STABLE: No drift detected.")
        print("   Current model version remains optimal in production.")
        print("   Retraining skipped.\n")
        sys.exit(0)

    # 2. Drift Detected or Force Retrain
    reasons = ", ".join(drift_report.get("primary_reasons", ["Manual trigger"]))
    print("\n" + "!" * 65)
    print(f"🚨 RETRAINING TRIGGERED: {reasons}")
    print("!" * 65)

    # 3. Ingest fresh ratings
    export_and_merge_production_ratings()

    # 4. Retrain SVD model and register new version to MLflow
    success = trigger_retraining(reason=f"data_drift: {reasons}")

    if success:
        print("\n🎉 Model retraining and MLflow registration completed successfully!")
        # Complete simulation test cycle by cleaning up injected simulation records from MongoDB
        try:
            from backend.app.database import connect_db, get_db
            connect_db()
            db = get_db()
            sim_deleted = db.ratings.delete_many({"is_drift_simulation": True})
            if sim_deleted.deleted_count > 0:
                print(f"🧹 Cleaned up {sim_deleted.deleted_count} simulated drift ratings from MongoDB.")
        except Exception as e:
            print(f"[NOTE] Post-retrain simulation cleanup: {e}")

        # Re-check drift to log baseline update and restore healthy status
        print("🔄 Updating post-retrain drift status in Prometheus...")
        run_drift_analysis(simulate=False)
        sys.exit(0)
    else:
        print("\n❌ Pipeline failed during model retraining.")
        sys.exit(1)


if __name__ == "__main__":
    main()
