"""
Pytest configuration for CineMatch AI
Ensures pure-Python fallback for surprise.similarities is registered before tests run.
"""
import sys
import types
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Ensure surprise.similarities is available without DLL dependency on Windows
if "surprise.similarities" not in sys.modules:
    try:
        from scripts.patch_surprise import SIM_CONTENT
        sim_mod = types.ModuleType("surprise.similarities")
        exec(SIM_CONTENT, sim_mod.__dict__)
        sys.modules["surprise.similarities"] = sim_mod
    except Exception as e:
        print(f"[conftest] Note: {e}")
