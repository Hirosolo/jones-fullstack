# Jones

Print-on-demand e-commerce platform.

## Architecture

| Component | Tech | Deploy |
|-----------|------|--------|
| Frontend | Next.js 15 / TypeScript / Tailwind 4 | **Vercel** |
| Backend | Django 5.2 / DRF | **Google Cloud Run** |
| Database | PostgreSQL 16 | Cloud SQL |
| Media | File uploads | Cloud Storage |
| CI/CD | GitHub Actions | Auto-deploy on push |

```
jones.com       → Vercel (Frontend)
api.jones.com   → Cloud Run (Backend API)
```

## Project Structure

```
├── backend/          Django REST API
├── frontend/         Next.js app
├── deploy/           Docker, Cloud Run scripts, nginx config
└── .github/          CI/CD workflows
```

## Quick Start (Local Dev)

### Option 1: Docker (recommended)

```bash
docker compose -f deploy/docker-compose.yml up
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- DB: PostgreSQL on port 5432

### Option 2: Manual

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

**Frontend:**
```bash
cd frontend
pnpm install
pnpm dev
```

## Deploy

### Backend → Google Cloud Run

```bash
# First time: creates Cloud SQL, Storage, and deploys
bash deploy/cloudrun-deploy.sh

# Map api.jones.com
bash deploy/cloudrun-domain.sh
```

### Frontend → Vercel

Auto-deploys on push to `master` via GitHub Actions.

Manual: [Vercel Dashboard](https://vercel.com) → Import repo → Root: `frontend`

### Environment Variables

**Backend (Cloud Run):**
- `DATABASE_URL` — Cloud SQL connection string
- `SITE_URL` — https://jones.com
- `DJANGO_BASE_URL` — https://api.jones.com
- `CORS_ALLOWED_ORIGINS` — https://jones.com
- `GS_BUCKET_NAME` — Media storage bucket

**Frontend (Vercel):**
- `NEXT_PUBLIC_DJANGO_BASE_URL` — https://api.jones.com
- `NEXT_PUBLIC_SITE_URL` — https://jones.com

## DNS Setup

Add these records at your DNS provider:

| Type | Host | Value |
|------|------|-------|
| A | @ | 76.76.21.21 (Vercel) |
| CNAME | www | cname.vercel-dns.com |
| CNAME | api | ghs.googlehosted.com |
