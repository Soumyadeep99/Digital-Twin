# Diabetes Digital Twin frontend

## Run locally

Use Node.js 20.19 or newer.

1. Start FastAPI from the repository root: `uvicorn app.main:app --reload` (default `http://127.0.0.1:8000`).
2. In `frontend/`, copy `.env.example` to `.env`, run `npm ci`, then `npm run dev`.
3. Open `http://localhost:5173`. Set `VITE_API_BASE_URL` in `.env` when the backend uses another URL.

The app uses the backend for patients, readings, model status, forecasts, and CGMacros replay. It displays connection errors and empty states instead of substituting local sample data. Forecasting remains unavailable while the original GluFormer source/config/preprocessing is missing.
