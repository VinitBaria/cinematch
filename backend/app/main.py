"""
CineMatch AI - FastAPI Application Entry Point
"""
import time
import json
from contextlib import asynccontextmanager
from pathlib import Path
import subprocess
import sys
from fastapi import FastAPI, Request, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings, ARTIFACTS_DIR
from .database import connect_db, close_db, get_db
from .routes.auth import router as auth_router
from .routes.movies import router as movies_router
from .routes.ratings import router as ratings_router
from .routes.recommendations import router as recommendations_router, _get_recommender
from .schemas.schemas import ModelInfoResponse
from .metrics import get_metrics_response, prometheus_metrics_middleware, ACTIVE_MODEL_INFO

START_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("[APP] Starting CineMatch AI backend...")
    try:
        connect_db()
    except Exception as e:
        print(f"[WARN] MongoDB connection failed at startup: {e}")

    try:
        # Pre-warm SVD recommender
        rec = _get_recommender()
        if rec and rec._loaded:
            print(f"[ML] SVD Model loaded successfully (version: {rec.model_version})")
            ACTIVE_MODEL_INFO.labels(model_version=str(rec.model_version), algorithm="SVD").set(1)
        else:
            print("[ML] SVD Model not yet loaded or not found")
    except Exception as e:
        print(f"[WARN] Error loading ML model at startup: {e}")

    try:
        # Pre-warm Data Drift status
        from .metrics import sync_drift_from_disk
        sync_drift_from_disk()
    except Exception as e:
        print(f"[WARN] Could not initialize drift metrics at startup: {e}")

    yield

    # Shutdown
    print("[APP] Shutting down CineMatch AI backend...")
    try:
        close_db()
    except Exception as e:
        print(f"[WARN] Error closing MongoDB connection: {e}")


app = FastAPI(
    title="CineMatch AI API",
    description="Full-Stack Movie Recommendation Engine with SVD Collaborative Filtering",
    version="1.0.0",
    lifespan=lifespan,
)

# Metrics Middleware
app.middleware("http")(prometheus_metrics_middleware)

# CORS configuration
origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
if "*" not in origins and "http://localhost:5173" not in origins:
    origins.append("http://localhost:5173")
if "http://localhost:3000" not in origins:
    origins.append("http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router)
app.include_router(movies_router)
app.include_router(ratings_router)
app.include_router(recommendations_router)


@app.get("/metrics", tags=["Monitoring"], include_in_schema=False)
def metrics_endpoint():
    """Prometheus metrics endpoint."""
    return get_metrics_response()


@app.get("/", tags=["System"])
def root():
    return {
        "name": "CineMatch AI API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "online",
    }


@app.get("/api/health", tags=["System"])
def health_check():
    db_healthy = False
    db_error = None
    try:
        db = get_db()
        db.command("ping")
        db_healthy = True
    except Exception as e:
        db_error = str(e)

    recommender = _get_recommender()
    model_loaded = recommender is not None and getattr(recommender, "_loaded", False)

    return {
        "status": "healthy" if db_healthy else "degraded",
        "database": {
            "status": "connected" if db_healthy else "disconnected",
            "name": settings.MONGODB_DB_NAME,
            "error": db_error,
        },
        "mlModel": {
            "loaded": model_loaded,
            "version": recommender.model_version if recommender else None,
            "knownUsers": len(recommender.known_user_ids) if recommender else 0,
            "knownMovies": len(recommender.known_movie_ids) if recommender else 0,
        },
        "uptimeSeconds": round(time.time() - START_TIME, 2),
    }


@app.get("/api/model/info", tags=["System"], response_model=ModelInfoResponse)
def get_model_info():
    meta_path = ARTIFACTS_DIR / "model_metadata.json"
    if not meta_path.exists():
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": "Model metadata not found. Train model first."},
        )

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    recommender = _get_recommender()

    return ModelInfoResponse(
        modelVersion=meta.get("model_version", "unknown"),
        algorithm=meta.get("algorithm", "SVD"),
        parameters=meta.get("parameters", {}),
        trainsetStats=meta.get("trainset_stats", {}),
        trainedAt=meta.get("trained_at", ""),
        knownUsers=len(recommender.known_user_ids) if recommender else meta.get("known_users_count", 0),
        knownMovies=len(recommender.known_movie_ids) if recommender else meta.get("known_movies_count", 0),
    )


@app.get("/api/model/drift-status", tags=["Model Governance"])
def get_drift_status():
    """Retrieve current data drift audit summary and statistics."""
    report_file = ARTIFACTS_DIR / "drift_report.json"
    if not report_file.exists():
        # Fallback to status file or run check
        status_file = ARTIFACTS_DIR / "drift_status.json"
        if status_file.exists():
            with open(status_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"status": "no_audit_recorded", "message": "Run drift check first."}

    with open(report_file, "r", encoding="utf-8") as f:
        return json.load(f)


@app.post("/api/model/check-drift", tags=["Model Governance"])
def trigger_drift_check(simulate: bool = False):
    """Trigger a live statistical data drift analysis against MongoDB ratings."""
    try:
        from ml.drift_detector import run_drift_analysis
        report = run_drift_analysis(simulate=simulate)
        return report
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e), "message": "Failed to run data drift audit."},
        )


def _run_background_retrain():
    """Background task to execute check_drift_and_retrain pipeline."""
    script_path = Path(__file__).resolve().parent.parent.parent / "scripts" / "check_drift_and_retrain.py"
    subprocess.run([sys.executable, str(script_path), "--force-retrain"])


@app.post("/api/model/retrain", tags=["Model Governance"])
def trigger_retraining_webhook(background_tasks: BackgroundTasks):
    """
    Webhook endpoint for Grafana, Jenkins, or Admin to trigger model retraining.
    Runs asynchronously in the background and returns HTTP 200 immediately.
    """
    background_tasks.add_task(_run_background_retrain)
    return {
        "status": "triggered",
        "timestamp": time.time(),
        "message": "Continuous Training pipeline initiated in background."
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
