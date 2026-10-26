"""
CineMatch AI - Data Drift Injection & Simulation Tool
Injects real production drift into MongoDB to test the automated MLOps alerting & retraining loop.

Usage:
    # Inject 100 drifted ratings from new unseen users (low ratings):
    python scripts/inject_data_drift.py

    # Inject high ratings drift:
    python scripts/inject_data_drift.py --type high --count 150

    # Clean up all injected drift ratings from MongoDB:
    python scripts/inject_data_drift.py --cleanup
"""
import sys
import os
import time
import argparse
import random
from datetime import datetime, timezone
from pathlib import Path

# Fix Windows console encoding
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.database import connect_db, get_db
from ml.drift_detector import run_drift_analysis, DRIFT_STATUS_FILE, DRIFT_REPORT_FILE


def inject_drift(count: int = 100, drift_type: str = "low"):
    """
    Inserts skewed ratings from brand new, unseen users directly into MongoDB.
    This creates authentic data drift in the production database.
    """
    print("=" * 60)
    print(" 🚨 CineMatch AI - Injecting Data Drift into MongoDB")
    print("=" * 60)

    connect_db()
    db = get_db()

    initial_count = db.ratings.count_documents({})
    print(f"📊 Current live MongoDB ratings: {initial_count:,}")

    # Fetch valid movie IDs to rate
    sample_movies = list(db.movies.find({}, {"movieId": 1}).limit(50))
    if sample_movies:
        valid_movie_ids = [m["movieId"] for m in sample_movies]
    else:
        valid_movie_ids = list(range(1, 101))

    # Generate new unseen users (strictly higher than any existing user)
    num_users = max(30, count // 2)
    max_existing = max(db.ratings.distinct("userId") or [9000])
    base_user = max(max_existing + 10, 10000)
    drift_users = [base_user + i for i in range(1, num_users + 1)]

    injected_docs = []
    used_pairs = set()
    now = datetime.now(timezone.utc)

    # Pre-populate already existing (userId, movieId) pairs from MongoDB
    for r in db.ratings.find({}, {"userId": 1, "movieId": 1}):
        used_pairs.add((r["userId"], r["movieId"]))

    inserted = 0
    attempts = 0
    while inserted < count and attempts < count * 10:
        attempts += 1
        uid = random.choice(drift_users)
        mid = random.choice(valid_movie_ids)

        if (uid, mid) in used_pairs:
            continue
        used_pairs.add((uid, mid))

        if drift_type == "low":
            # Skew ratings downward (0.5 - 2.0)
            rating = float(random.choice([0.5, 1.0, 1.0, 1.5, 2.0]))
        elif drift_type == "high":
            # Skew ratings upward (4.5 - 5.0)
            rating = float(random.choice([4.5, 5.0, 5.0, 5.0]))
        else:
            # Unseen users with varied ratings
            rating = float(random.choice([1.0, 2.0, 4.0, 5.0]))

        doc = {
            "userId": uid,
            "movieId": mid,
            "rating": rating,
            "review": f"Automated drift simulation rating #{inserted+1}",
            "createdAt": now,
            "updatedAt": now,
            "timestamp": int(time.time()),
            "is_drift_simulation": True,  # Tagged for easy cleanup
        }
        injected_docs.append(doc)
        inserted += 1

    # Insert into MongoDB
    if injected_docs:
        res = db.ratings.insert_many(injected_docs)
    total_count = db.ratings.count_documents({})
    print(f"✅ Injected {len(res.inserted_ids)} drifted ratings into MongoDB collection 'ratings'.")
    print(f"📈 Total ratings now in MongoDB: {total_count:,}")
    print(f"👥 Injected {len(drift_users)} new unseen users (IDs {drift_users[0]} - {drift_users[-1]}).")

    # Run drift detector to evaluate live MongoDB ratings
    print("\n🔍 Evaluating production data drift against baseline...")
    report = run_drift_analysis(simulate=False)

    # Sync drift status into backend container for instant Prometheus scrape
    _sync_to_docker()

    print("\n" + "=" * 60)
    if report.get("drift_detected"):
        print("🚨 SUCCESS: DATA DRIFT IS NOW DETECTED & ACTIVE!")
        print("   • Grafana Dashboard: http://localhost:3001/d/cinematch-ai-mlops (Turned RED)")
        print("   • Alert Rule:       Firing alert to webhook")
        print("   • Next Step:        Trigger retraining or watch automated continuous training")
    else:
        print("ℹ️ Shift not large enough yet. Try injecting more ratings.")
    print("=" * 60)


def cleanup_drift():
    """
    Removes all simulated drift ratings from MongoDB and restores stable status.
    """
    print("=" * 60)
    print(" 🧹 CineMatch AI - Cleaning Up Simulated Drift Data")
    print("=" * 60)

    connect_db()
    db = get_db()

    del_res = db.ratings.delete_many({"is_drift_simulation": True})
    remaining = db.ratings.count_documents({})
    print(f"✅ Deleted {del_res.deleted_count} simulated drift records from MongoDB.")
    print(f"📊 Remaining clean production ratings: {remaining:,}")

    # Re-evaluate drift status
    print("\n🔍 Re-evaluating drift status on clean database...")
    run_drift_analysis(simulate=False)
    _sync_to_docker()

    print("\n🎉 Database restored to clean state.")


def _sync_to_docker():
    """Copy updated drift status into Docker container if running."""
    import subprocess
    try:
        if DRIFT_STATUS_FILE.exists():
            subprocess.run(
                ["docker", "cp", str(DRIFT_STATUS_FILE), "cinematch_backend:/app/ml/artifacts/drift_status.json"],
                capture_output=True,
                check=False,
            )
        if DRIFT_REPORT_FILE.exists():
            subprocess.run(
                ["docker", "cp", str(DRIFT_REPORT_FILE), "cinematch_backend:/app/ml/artifacts/drift_report.json"],
                capture_output=True,
                check=False,
            )
    except Exception:
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CineMatch AI - Inject Data Drift into MongoDB")
    parser.add_argument("--count", type=int, default=120, help="Number of drifted ratings to inject (default: 120)")
    parser.add_argument("--type", choices=["low", "high", "unseen"], default="low", help="Type of drift to simulate (default: low)")
    parser.add_argument("--cleanup", action="store_true", help="Remove all simulated drift ratings from MongoDB")
    args = parser.parse_args()

    if args.cleanup:
        cleanup_drift()
    else:
        inject_drift(count=args.count, drift_type=args.type)
