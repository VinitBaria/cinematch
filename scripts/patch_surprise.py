"""
Patch utility to ensure scikit-surprise similarities module is present
even if Windows Defender or third-party antivirus blocks the .pyd binary.
"""

import sys
import site
from pathlib import Path

SIM_CONTENT = '''"""Fallback similarities module."""
import math
import numpy as np

def cosine(n_x, yr, min_support):
    prods = np.zeros((n_x, n_x), dtype=np.double)
    freq = np.zeros((n_x, n_x), dtype=np.intp)
    sqi = np.zeros((n_x, n_x), dtype=np.double)
    sqj = np.zeros((n_x, n_x), dtype=np.double)
    sim = np.zeros((n_x, n_x), dtype=np.double)
    for y, y_ratings in yr.items():
        for xi, ri in y_ratings:
            for xj, rj in y_ratings:
                freq[xi, xj] += 1
                prods[xi, xj] += ri * rj
                sqi[xi, xj] += ri**2
                sqj[xi, xj] += rj**2
    for xi in range(n_x):
        sim[xi, xi] = 1.0
        for xj in range(xi + 1, n_x):
            if freq[xi, xj] < min_support:
                sim[xi, xj] = 0.0
            else:
                denum = math.sqrt(sqi[xi, xj] * sqj[xi, xj])
                sim[xi, xj] = prods[xi, xj] / denum if denum > 0 else 0.0
            sim[xj, xi] = sim[xi, xj]
    return np.asarray(sim)

def msd(n_x, yr, min_support):
    sq_diff = np.zeros((n_x, n_x), dtype=np.double)
    freq = np.zeros((n_x, n_x), dtype=np.intp)
    sim = np.zeros((n_x, n_x), dtype=np.double)
    for y, y_ratings in yr.items():
        for xi, ri in y_ratings:
            for xj, rj in y_ratings:
                sq_diff[xi, xj] += (ri - rj) ** 2
                freq[xi, xj] += 1
    for xi in range(n_x):
        sim[xi, xi] = 1.0
        for xj in range(xi + 1, n_x):
            if freq[xi, xj] < min_support:
                sim[xi, xj] = 0.0
            else:
                sim[xi, xj] = 1.0 / (sq_diff[xi, xj] / freq[xi, xj] + 1.0)
            sim[xj, xi] = sim[xi, xj]
    return np.asarray(sim)

def pearson(n_x, yr, min_support):
    freq = np.zeros((n_x, n_x), dtype=np.intp)
    prods = np.zeros((n_x, n_x), dtype=np.double)
    sqi = np.zeros((n_x, n_x), dtype=np.double)
    sqj = np.zeros((n_x, n_x), dtype=np.double)
    si = np.zeros((n_x, n_x), dtype=np.double)
    sj = np.zeros((n_x, n_x), dtype=np.double)
    sim = np.zeros((n_x, n_x), dtype=np.double)
    for y, y_ratings in yr.items():
        for xi, ri in y_ratings:
            for xj, rj in y_ratings:
                prods[xi, xj] += ri * rj
                freq[xi, xj] += 1
                sqi[xi, xj] += ri**2
                sqj[xi, xj] += rj**2
                si[xi, xj] += ri
                sj[xi, xj] += rj
    for xi in range(n_x):
        sim[xi, xi] = 1.0
        for xj in range(xi + 1, n_x):
            if freq[xi, xj] < min_support:
                sim[xi, xj] = 0.0
            else:
                n = freq[xi, xj]
                num = n * prods[xi, xj] - si[xi, xj] * sj[xi, xj]
                val = (n * sqi[xi, xj] - si[xi, xj] ** 2) * (n * sqj[xi, xj] - sj[xi, xj] ** 2)
                denum = math.sqrt(max(0.0, val))
                sim[xi, xj] = num / denum if denum > 0 else 0.0
            sim[xj, xi] = sim[xi, xj]
    return np.asarray(sim)

def pearson_baseline(n_x, yr, min_support, global_mean, x_biases, y_biases, shrinkage=100):
    freq = np.zeros((n_x, n_x), dtype=np.intp)
    prods = np.zeros((n_x, n_x), dtype=np.double)
    sq_diff_i = np.zeros((n_x, n_x), dtype=np.double)
    sq_diff_j = np.zeros((n_x, n_x), dtype=np.double)
    sim = np.zeros((n_x, n_x), dtype=np.double)
    min_sprt = max(2, min_support)
    for y, y_ratings in yr.items():
        partial_bias = global_mean + y_biases[y]
        for xi, ri in y_ratings:
            for xj, rj in y_ratings:
                freq[xi, xj] += 1
                diff_i = ri - (partial_bias + x_biases[xi])
                diff_j = rj - (partial_bias + x_biases[xj])
                prods[xi, xj] += diff_i * diff_j
                sq_diff_i[xi, xj] += diff_i**2
                sq_diff_j[xi, xj] += diff_j**2
    for xi in range(n_x):
        sim[xi, xi] = 1.0
        for xj in range(xi + 1, n_x):
            if freq[xi, xj] < min_sprt:
                sim[xi, xj] = 0.0
            else:
                denom = math.sqrt(sq_diff_i[xi, xj] * sq_diff_j[xi, xj])
                if denom > 0:
                    val = prods[xi, xj] / denom
                    val *= (freq[xi, xj] - 1) / (freq[xi, xj] - 1 + shrinkage)
                    sim[xi, xj] = val
                else:
                    sim[xi, xj] = 0.0
            sim[xj, xi] = sim[xi, xj]
    return np.asarray(sim)
'''

def patch():
    try:
        surprise_dirs = []
        search_paths = list(sys.path)
        try:
            search_paths.extend(site.getsitepackages())
        except Exception:
            pass

        for p in search_paths:
            s_dir = Path(p) / "surprise"
            if s_dir.exists() and s_dir.is_dir() and s_dir not in surprise_dirs:
                surprise_dirs.append(s_dir)

        if not surprise_dirs:
            print("[PATCH] Surprise directory not found.")
            return

        for surprise_dir in surprise_dirs:
            sim_py = surprise_dir / "similarities.py"
            # Always ensure similarities.py exists
            if not sim_py.exists():
                with open(sim_py, "w", encoding="utf-8") as f:
                    f.write(SIM_CONTENT)
                print(f"[PATCH] Applied pure-python surprise.similarities fallback to {sim_py}")
            else:
                print(f"[PATCH] similarities.py already present in {surprise_dir}")
    except Exception as e:
        print(f"[PATCH] Notice: {e}")

if __name__ == "__main__":
    patch()
