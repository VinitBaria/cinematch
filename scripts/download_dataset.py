"""
CineMatch AI - Dataset Download Script
Downloads and extracts the MovieLens Latest Small dataset.
"""

import sys
import zipfile
import hashlib
from pathlib import Path

# Fix Windows console encoding
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import certifi
import urllib3
import requests
from tqdm import tqdm

# Add parent to path so we can import ml.config
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml.config import (
    MOVIELENS_URL,
    MOVIELENS_ZIP,
    MOVIELENS_DIR,
    RAW_DATA_DIR,
    RATINGS_CSV,
    MOVIES_CSV,
    LINKS_CSV,
)


def download_file(url: str, dest: Path, chunk_size: int = 8192) -> None:
    """Download a file with progress bar and robust SSL handling."""
    print(f"[DOWNLOAD] Downloading from {url}")
    try:
        response = requests.get(url, stream=True, timeout=60, verify=certifi.where())
        response.raise_for_status()
    except requests.exceptions.SSLError:
        print("[WARN] SSL verification failed with local certs, retrying without SSL verification...")
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        response = requests.get(url, stream=True, timeout=60, verify=False)
        response.raise_for_status()

    total = int(response.headers.get("content-length", 0))

    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as f, tqdm(
        total=total, unit="B", unit_scale=True, desc=dest.name
    ) as pbar:
        for chunk in response.iter_content(chunk_size=chunk_size):
            f.write(chunk)
            pbar.update(len(chunk))

    print(f"[OK] Downloaded to {dest}")


def extract_zip(zip_path: Path, extract_to: Path) -> None:
    """Extract a zip file."""
    print(f"[EXTRACT] Extracting {zip_path.name}...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_to)
    print(f"[OK] Extracted to {extract_to}")


def validate_dataset() -> bool:
    """Validate that all required CSV files exist and have content."""
    required_files = [RATINGS_CSV, MOVIES_CSV, LINKS_CSV]
    all_valid = True

    for f in required_files:
        if not f.exists():
            print(f"[FAIL] Missing: {f}")
            all_valid = False
        elif f.stat().st_size == 0:
            print(f"[FAIL] Empty file: {f}")
            all_valid = False
        else:
            # Quick line count
            with open(f, "r", encoding="utf-8") as fh:
                line_count = sum(1 for _ in fh) - 1  # exclude header
            print(f"[OK] {f.name}: {line_count:,} rows")

    return all_valid


def compute_checksum(file_path: Path) -> str:
    """Compute MD5 checksum for a file."""
    md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5.update(chunk)
    return md5.hexdigest()


def main():
    print("=" * 60)
    print("  CineMatch AI - Dataset Setup")
    print("=" * 60)
    print()

    # Check if dataset already exists and is valid
    if MOVIELENS_DIR.exists() and RATINGS_CSV.exists():
        print("[INFO] Dataset directory found. Validating...")
        if validate_dataset():
            print("\n[OK] Dataset is already downloaded and valid!")
            checksum = compute_checksum(RATINGS_CSV)
            print(f"   ratings.csv MD5: {checksum}")
            return
        else:
            print("\n[WARN] Dataset validation failed. Re-downloading...")

    # Download
    if not MOVIELENS_ZIP.exists():
        download_file(MOVIELENS_URL, MOVIELENS_ZIP)
    else:
        print(f"[INFO] Zip file already exists: {MOVIELENS_ZIP}")

    # Extract
    extract_zip(MOVIELENS_ZIP, RAW_DATA_DIR)

    # Validate
    print("\n[INFO] Validating extracted dataset...")
    if validate_dataset():
        print("\n[DONE] Dataset setup complete!")
        checksum = compute_checksum(RATINGS_CSV)
        print(f"   ratings.csv MD5: {checksum}")
    else:
        print("\n[FAIL] Dataset validation failed after extraction!")
        sys.exit(1)


if __name__ == "__main__":
    main()
