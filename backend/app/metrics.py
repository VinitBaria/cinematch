"""
CineMatch AI - Prometheus Metrics Registry & Definitions
"""
import time
from fastapi import Request, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# ──────────────────────────────────────────────
# 1. HTTP API Performance Metrics (RED Method)
# ──────────────────────────────────────────────
HTTP_REQUESTS_TOTAL = Counter(
    "cinematch_http_requests_total",
    "Total HTTP requests received by the API",
    ["method", "endpoint", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "cinematch_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "cinematch_http_requests_in_progress",
    "Number of HTTP requests currently being handled",
    ["endpoint"],
)

# ──────────────────────────────────────────────
# 2. ML Recommendation Engine Metrics
# ──────────────────────────────────────────────
RECOMMENDATION_REQUESTS_TOTAL = Counter(
    "cinematch_recommendation_requests_total",
    "Total recommendation requests processed",
    ["strategy", "status"],  # strategy: svd, popular, genre; status: success, error
)

MODEL_INFERENCE_SECONDS = Histogram(
    "cinematch_model_inference_seconds",
    "Time taken by SVD model to generate and score recommendations",
    ["model_version", "user_type"],  # user_type: known, cold_start
    buckets=(0.002, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)

RECOMMENDED_ITEMS_COUNT = Histogram(
    "cinematch_recommended_items_count",
    "Number of recommendations returned to user",
    ["strategy"],
    buckets=(5, 10, 15, 20, 25, 30),
)

ACTIVE_MODEL_INFO = Gauge(
    "cinematch_active_model_info",
    "Information about currently active ML model",
    ["model_version", "algorithm"],
)

# ──────────────────────────────────────────────
# ──────────────────────────────────────────────
# 3. User Feedback & Business Metrics
# ──────────────────────────────────────────────
RATINGS_SUBMITTED_TOTAL = Counter(
    "cinematch_ratings_submitted_total",
    "Total user ratings submitted through the platform",
    ["rating"],  # 0.5 to 5.0
)

# ──────────────────────────────────────────────
# 4. Data Drift & Model Governance Metrics
# ──────────────────────────────────────────────
DATA_DRIFT_DETECTED = Gauge(
    "cinematch_data_drift_detected",
    "Whether data drift is detected (0 = Stable, 1 = Drift Alert - Retrain Needed)",
)

DATA_DRIFT_KS_P_VALUE = Gauge(
    "cinematch_drift_ks_p_value",
    "Kolmogorov-Smirnov test p-value between training and live ratings (<0.05 indicates drift)",
)

DATA_DRIFT_KS_STATISTIC = Gauge(
    "cinematch_drift_ks_statistic",
    "Kolmogorov-Smirnov test maximum distance D-statistic",
)

DATA_DRIFT_PSI_SCORE = Gauge(
    "cinematch_drift_psi_score",
    "Population Stability Index for rating distribution shift (>0.20 indicates drift)",
)

DATA_DRIFT_UNSEEN_USERS_PCT = Gauge(
    "cinematch_drift_unseen_users_pct",
    "Percentage of live ratings from users not in the trained SVD matrix",
)

DATA_DRIFT_BASELINE_MEAN_RATING = Gauge(
    "cinematch_drift_baseline_mean_rating",
    "Mean rating in the baseline training dataset",
)

DATA_DRIFT_PRODUCTION_MEAN_RATING = Gauge(
    "cinematch_drift_production_mean_rating",
    "Mean rating in the live production database",
)

DATA_DRIFT_RATING_DISTRIBUTION = Gauge(
    "cinematch_drift_rating_distribution",
    "Proportion of ratings for each star score across datasets",
    ["dataset", "rating"],  # dataset: baseline, production; rating: 0.5 to 5.0
)

LAST_DRIFT_CHECK_TIMESTAMP = Gauge(
    "cinematch_last_drift_check_timestamp",
    "Unix timestamp of the most recent data drift evaluation",
)

# Pre-initialize labeled metrics so Prometheus scrapers immediately see valid series with zero defaults
ACTIVE_MODEL_INFO.labels(model_version="v1.0.0", algorithm="SVD").set(1)
MODEL_INFERENCE_SECONDS.labels(model_version="v1.0.0", user_type="known")
MODEL_INFERENCE_SECONDS.labels(model_version="v1.0.0", user_type="cold_start")
RECOMMENDATION_REQUESTS_TOTAL.labels(strategy="svd_collaborative_filtering", status="success")
RECOMMENDATION_REQUESTS_TOTAL.labels(strategy="popularity_bayesian_weighted", status="success")
RECOMMENDATION_REQUESTS_TOTAL.labels(strategy="genre_personalized_hybrid", status="success")
for _r in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]:
    RATINGS_SUBMITTED_TOTAL.labels(rating=str(_r))
    DATA_DRIFT_RATING_DISTRIBUTION.labels(dataset="baseline", rating=str(_r)).set(0.1)
    DATA_DRIFT_RATING_DISTRIBUTION.labels(dataset="production", rating=str(_r)).set(0.1)

DATA_DRIFT_DETECTED.set(0)
DATA_DRIFT_KS_P_VALUE.set(1.0)
DATA_DRIFT_KS_STATISTIC.set(0.0)
DATA_DRIFT_PSI_SCORE.set(0.0)
DATA_DRIFT_UNSEEN_USERS_PCT.set(0.0)
DATA_DRIFT_BASELINE_MEAN_RATING.set(3.53)
DATA_DRIFT_PRODUCTION_MEAN_RATING.set(3.53)
LAST_DRIFT_CHECK_TIMESTAMP.set(time.time())


def update_drift_metrics(
    drift_detected: bool,
    ks_p_value: float,
    ks_statistic: float,
    psi_score: float,
    unseen_users_pct: float,
    baseline_mean: float,
    production_mean: float,
    baseline_dist: dict = None,
    production_dist: dict = None,
):
    """Update all Prometheus drift metrics with the latest calculation results."""
    DATA_DRIFT_DETECTED.set(1 if drift_detected else 0)
    DATA_DRIFT_KS_P_VALUE.set(float(ks_p_value))
    DATA_DRIFT_KS_STATISTIC.set(float(ks_statistic))
    DATA_DRIFT_PSI_SCORE.set(float(psi_score))
    DATA_DRIFT_UNSEEN_USERS_PCT.set(float(unseen_users_pct))
    DATA_DRIFT_BASELINE_MEAN_RATING.set(float(baseline_mean))
    DATA_DRIFT_PRODUCTION_MEAN_RATING.set(float(production_mean))
    LAST_DRIFT_CHECK_TIMESTAMP.set(time.time())

    if baseline_dist:
        for r, val in baseline_dist.items():
            DATA_DRIFT_RATING_DISTRIBUTION.labels(dataset="baseline", rating=str(r)).set(float(val))
    if production_dist:
        for r, val in production_dist.items():
            DATA_DRIFT_RATING_DISTRIBUTION.labels(dataset="production", rating=str(r)).set(float(val))


_last_disk_sync = 0.0


def sync_drift_from_disk():
    """Fallback: Sync latest drift report from ml/artifacts/drift_report.json if present."""
    from .config import ARTIFACTS_DIR
    report_file = ARTIFACTS_DIR / "drift_report.json"
    if report_file.exists():
        try:
            import json
            with open(report_file, "r") as f:
                data = json.load(f)
            stats_data = data.get("statistics", {})
            dists = data.get("distributions", {})
            update_drift_metrics(
                drift_detected=data.get("drift_detected", False),
                ks_p_value=stats_data.get("ks_p_value", 1.0),
                ks_statistic=stats_data.get("ks_statistic", 0.0),
                psi_score=stats_data.get("psi_score", 0.0),
                unseen_users_pct=stats_data.get("unseen_users_pct", 0.0),
                baseline_mean=stats_data.get("baseline_mean", 3.53),
                production_mean=stats_data.get("production_mean", 3.53),
                baseline_dist=dists.get("baseline"),
                production_dist=dists.get("production"),
            )
        except Exception:
            pass


def sync_drift_live():
    """
    Computes real-time data drift metrics dynamically from MongoDB.
    Compares live production ratings directly against active model metadata.
    """
    global _last_disk_sync
    now = time.time()
    if now - _last_disk_sync < 4.0:
        return
    _last_disk_sync = now

    try:
        from .database import get_db
        from .config import ARTIFACTS_DIR
        import json

        # 1. Load active model metadata (baseline & known users)
        baseline_mean = 3.52
        known_users = set()
        model_ver = "unknown"
        meta_file = ARTIFACTS_DIR / "model_metadata.json"
        if meta_file.exists():
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
                baseline_mean = float(meta.get("trainset_stats", {}).get("mean_rating", 3.52))
                known_users = set(meta.get("known_user_ids", []))
                model_ver = meta.get("model_version", "unknown")

        # 2. Query MongoDB live ratings
        db = get_db()
        ratings = list(db.ratings.find({}, {"_id": 0, "userId": 1, "rating": 1}))
        if ratings:
            total = len(ratings)
            mean_prod = sum(r["rating"] for r in ratings) / total

            if known_users:
                unseen_count = sum(1 for r in ratings if r.get("userId") not in known_users)
                unseen_pct = round((unseen_count / total) * 100, 2)
            else:
                unseen_pct = 0.0

            # If all live users are already calibrated into the trained model:
            if unseen_pct == 0.0:
                drift_detected = False
            else:
                mean_shift = abs(mean_prod - baseline_mean)
                drift_detected = bool(mean_shift >= 0.50 or unseen_pct >= 25.0)

            # Update Gauges dynamically
            DATA_DRIFT_DETECTED.set(1 if drift_detected else 0)
            DATA_DRIFT_UNSEEN_USERS_PCT.set(float(unseen_pct))
            DATA_DRIFT_BASELINE_MEAN_RATING.set(round(float(baseline_mean), 2))
            DATA_DRIFT_PRODUCTION_MEAN_RATING.set(round(float(mean_prod), 2))
            LAST_DRIFT_CHECK_TIMESTAMP.set(now)
            ACTIVE_MODEL_INFO.labels(model_version=model_ver, algorithm="SVD").set(1)
            return
    except Exception:
        pass

    # Fallback to disk report if available
    sync_drift_from_disk()


def get_metrics_response() -> Response:
    """Generate Prometheus scrape response with live real-time metrics."""
    sync_drift_live()
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


async def prometheus_metrics_middleware(request: Request, call_next):
    """
    Middleware to record request duration, status code, and throughput.
    Normalizes endpoints to avoid high-cardinality paths.
    """
    endpoint = request.url.path

    # Normalize IDs to avoid label explosion
    if endpoint.startswith("/api/movies/") and len(endpoint.split("/")) > 3:
        endpoint = "/api/movies/{id}"
    elif endpoint.startswith("/api/ratings/user/"):
        endpoint = "/api/ratings/user/{id}"

    # Skip prometheus endpoint itself from duration histogram
    if endpoint == "/metrics":
        return await call_next(request)

    HTTP_REQUESTS_IN_PROGRESS.labels(endpoint=endpoint).inc()
    start_time = time.time()

    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        duration = time.time() - start_time
        HTTP_REQUESTS_IN_PROGRESS.labels(endpoint=endpoint).dec()
        HTTP_REQUESTS_TOTAL.labels(
            method=request.method,
            endpoint=endpoint,
            status=str(status_code),
        ).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=request.method,
            endpoint=endpoint,
        ).observe(duration)
