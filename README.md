# CineMatch AI 🎬

A Production-Structured Full-Stack Movie Recommendation Web Application inspired by Netflix and Amazon Prime Video, powered by **SVD Collaborative Filtering** on the MovieLens dataset.

---

## 🚀 Architecture Overview

- **Frontend**: React + TypeScript + Vite + Tailwind CSS (Netflix dark UI, glassmorphic navbar, responsive carousels, instant live rating, and AI recommendation breakdown)
- **Backend**: Python + FastAPI + Uvicorn + MongoDB (JWT authentication, bcrypt security & RESTful APIs)
- **ML Pipeline**: SVD Matrix Factorization Collaborative Filtering (`scikit-surprise`, 100 latent factors, validation RMSE 0.867)
- **Metadata**: TMDB integration & high-resolution cinematic backdrop fallbacks

---

## 📁 Project Structure

```text
cinematch-ai/
├── ml/                         # ML Engine & Training Pipeline
│   ├── config.py               # Central ML configuration & paths
│   ├── preprocess.py           # Dataset cleaning & chronological splitting
│   ├── train.py                # SVD model training & artifact generation
│   ├── evaluate.py             # Evaluation (RMSE, MAE, Precision@10, Recall@10, NDCG@10)
│   ├── tune.py                 # Hyperparameter tuning on validation set
│   ├── recommend.py            # SVDRecommender & Bayesian popularity cold-start
│   ├── requirements.txt        # Python ML dependencies
│   └── artifacts/              # Trained models, metadata & metrics
│       ├── svd_model.joblib
│       ├── model_metadata.json
│       └── evaluation_metrics.json
├── backend/                    # FastAPI Backend Service
│   ├── app/
│   │   ├── config.py           # App settings & env configurations
│   │   ├── database.py         # MongoDB connection & index setup
│   │   ├── main.py             # FastAPI entrypoint, CORS & lifespan
│   │   ├── routes/             # Auth, Movies, Ratings, Recommendations
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   └── security/           # JWT & bcrypt password hashing
│   └── requirements.txt        # Backend dependencies
├── frontend/                   # Netflix-Style React UI
│   ├── src/
│   │   ├── components/         # Navbar, HeroBanner, MovieCard, Carousel, Modal, StarRating
│   │   ├── context/            # AuthContext with demo fast login
│   │   ├── pages/              # Home, Recommendations, Ratings, Search, Onboarding, Login
│   │   ├── services/           # Axios API client
│   │   └── types/              # TypeScript interfaces
│   ├── index.html
│   ├── vite.config.ts
│   └── tailwind.config.js
├── data/
│   ├── raw/                    # Raw MovieLens Latest Small zip & extracts
│   └── processed/              # Chronological splits, stats & ID mappings
├── scripts/
│   ├── download_dataset.py     # Dataset download with SSL & checksum verification
│   ├── patch_surprise.py      # Windows AV runtime compatibility patch
│   ├── setup_project.py        # End-to-end Phase 1 pipeline runner
│   └── seed_database.py        # MongoDB database seeder (movies, demo users)
├── tests/
│   ├── test_ml.py              # ML test suite (12 tests)
│   └── test_backend.py         # Backend API test suite (6 tests)
├── .env.example
└── .gitignore
```

---

## ⚡ How to Run the Application

### 1. Set Up Backend & Python Virtual Environment

```powershell
cd cinematch-ai
python -m venv venv
.\venv\Scripts\activate
pip install -r backend\requirements.txt
```

### 2. Seed the MongoDB Database

Ensure MongoDB is running locally (e.g., `mongodb://localhost:27017`), then run:

```powershell
.\venv\Scripts\python.exe scripts\seed_database.py
```

This populates:
- 9,700+ movies with aggregated review scores and backdrop art
- Pre-trained demo user (`demo@cinematch.ai` / `password123`)
- Fresh cold-start user (`alex@cinematch.ai` / `password123`)

### 3. Start the FastAPI Backend

```powershell
.\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/api/health`

### 4. Start the Netflix-Style Frontend

In a separate terminal:

```powershell
cd cinematch-ai\frontend
npm install
npm run dev
```

Visit **`http://localhost:5173`** in your browser.

---

## 🧪 Testing

Run all 18 automated tests across ML and Backend:

```powershell
.\venv\Scripts\python.exe -m pytest -v
```

All 18 tests pass with 100% green status.
