"""
CineMatch AI - Project Setup Script
Runs the full Phase 1 pipeline:
  1. Download MovieLens dataset
  2. Preprocess and split data
  3. Train SVD model
  4. Evaluate model
  5. Generate demo recommendations
"""

import subprocess
import sys
from pathlib import Path

# Fix Windows console encoding
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def run_step(description: str, script: str):
    """Run a Python script and handle errors."""
    print(f"\n{'=' * 60}")
    print(f"  STEP: {description}")
    print(f"{'=' * 60}")

    result = subprocess.run(
        [sys.executable, script],
        cwd=str(PROJECT_ROOT),
        capture_output=False,
    )

    if result.returncode != 0:
        print(f"\n❌ Failed: {description}")
        print(f"   Script: {script}")
        sys.exit(result.returncode)

    print(f"\n✅ Completed: {description}")


def main():
    print("🎬" * 30)
    print()
    print("  CineMatch AI - Full Setup")
    print("  Phase 1: ML Pipeline")
    print()
    print("🎬" * 30)

    steps = [
        ("Download MovieLens Dataset", str(PROJECT_ROOT / "scripts" / "download_dataset.py")),
        ("Preprocess & Split Data", str(PROJECT_ROOT / "ml" / "preprocess.py")),
        ("Train SVD Model", str(PROJECT_ROOT / "ml" / "train.py")),
        ("Evaluate Model", str(PROJECT_ROOT / "ml" / "evaluate.py")),
        ("Generate Demo Recommendations", str(PROJECT_ROOT / "ml" / "recommend.py")),
    ]

    for desc, script in steps:
        run_step(desc, script)

    print("\n" + "🎉" * 30)
    print()
    print("  ✅ CineMatch AI Phase 1 Setup Complete!")
    print()
    print("  Artifacts saved in: ml/artifacts/")
    print("  Processed data in: data/processed/")
    print()
    print("  Next steps:")
    print("    • Run ml/tune.py for hyperparameter tuning (optional, takes ~10-30 min)")
    print("    • Proceed to Phase 2: FastAPI Backend")
    print()
    print("🎉" * 30)


if __name__ == "__main__":
    main()
