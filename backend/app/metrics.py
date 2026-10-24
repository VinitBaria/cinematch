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
# 3. User Feedback & Business Metrics
# ──────────────────────────────────────────────
RATINGS_SUBMITTED_TOTAL = Counter(
    "cinematch_ratings_submitted_total",
    "Total user ratings submitted through the platform",
    ["rating"],  # 0.5 to 5.0
)


def get_metrics_response() -> Response:
    """Generate Prometheus scrape response."""
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
