# LoanCheck — Unsecured Personal Loan Eligibility Expert System

Rule-based loan eligibility expert system for unsecured personal loans in INR. Uses production rules and first-order logic to decide `ELIGIBLE`, `INELIGIBLE`, or `REFER`, recommend an amount and interest band, and provide full auditable explanations. A machine learning classifier baseline is included for comparison alongside fairness evaluations.

> **Academic Prototype**: Illustrative policy values on synthetic and public data. Not financial or credit advice.

---

## Deploy to Vercel

The application is pre-configured for zero-configuration serverless deployment on [Vercel](https://vercel.com).

### CLI Deployment

```bash
# 1. Install the Vercel CLI globally (if not already installed)
npm i -g vercel

# 2. Preview deployment
vercel

# 3. Production deployment
vercel --prod
```

### Web Console (GitHub Import)

1. Push your branch to GitHub (or fork the repository).
2. In the Vercel dashboard, click **Add New...** -> **Project**.
3. Import the repository.
4. Leave all build and environment settings at their defaults and click **Deploy**.

### Deployment Details & Configuration

- **Entrypoint**: `app.py` exposes the ASGI FastAPI `app` instance.
- **Python Runtime**: Python 3.14 pinned via `.python-version`.
- **Environment Variables**: No environment variables are required. When running on Vercel (`VERCEL=1`), `AUDIT_DB_PATH` defaults automatically to `/tmp/audit.db`.
- **Static Assets & Reports**: Served directly by FastAPI; static assets in `src/ui/static/` and project documentation reports in `docs/reports/` are bundled.
- **Search Engine Indexing**: `X-Robots-Tag: noindex` header is injected on all routes, and `/robots.txt` disallows all crawlers.

### Known Limits of Serverless Deployment

- **Temporary Audit Log**: Vercel serverless execution environments have an ephemeral writable filesystem (`/tmp`). The audit database (`/tmp/audit.db`) resets when containers recycle or cold-boot. In demo mode, reports clearly state `"Audit stored: Yes (demo, temporary)"`.
- **Non-Unique IDs**: Sequence numbers for application/decision IDs reset across cold container restarts.
- **Cold Starts**: Initial invocations after inactivity may experience a slight latency while the Python runtime initializes and loads synthetic ML models (`d3_lr.joblib`, `d3_gb.joblib`).

### Fallback Deployment (Persistent Host)

For a persistent audit store and stateful production hosting:
- Run with Docker or a VPS host:
  ```bash
  uvicorn src.ui.app:app --host 0.0.0.0 --port 8000
  ```
- Mount a persistent volume to `data/audit/` or point `AUDIT_DB_PATH` to a persistent directory or volume.

---

## Local Development

```bash
# Install dependencies
make setup

# Run tests
make test

# Start the local demo UI
make demo-ui
```
Open `http://localhost:8000` in your browser.
