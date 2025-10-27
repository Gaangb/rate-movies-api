# Movies & Favorites API (Django + DRF)

Backend (Django + DRF) that integrates with **TMDb**.  
It exposes endpoints to **discover**, **search**, and **fetch movie details** from TMDb, plus **favorites** operations that act **directly on TMDb**.  
For sharing, the API stores **only** `account_id` and a human-friendly `list_name`; the shared listing itself is fetched **live from TMDb**.

---

## Table of Contents
1. [Overview](#overview)  
2. [Tech Stack](#tech-stack)  
3. [Key Behavior](#key-behavior)  
4. [Project Layout](#project-layout)  
5. [Setup](#setup)  
6. [Environment](#environment)  
7. [Commands](#commands)  
8. [API](#api)  
9. [Testing](#testing)  
10. [Troubleshooting](#troubleshooting)  
11. [Deploy & Rationale](#deploy--rationale)  
12. [Limitations & Next Steps](#limitations--next-steps)

---

## Overview
This service acts as a **BFF** for a movie app:

- **Discover/Search** (TMDb)
- **Movie details** (trailers/providers/credits handled by the details endpoint)
- **Favorites**: list and toggle **on TMDb** (no local persistence)
- **Shared favorites**: stores only `account_id` + `list_name`; when a list is opened, favorites are retrieved **live** from TMDb

---

## Tech Stack
- Python 3.12+  
- Django 5.x  
- Django REST Framework  
- drf-spectacular (OpenAPI)  
- django-environ, django-filter, django-cors-headers  
- requests  
- Poetry  
- pytest + pytest-django

---

## Key Behavior

- **Authorization**: all TMDb calls require the header `Authorization: Bearer <TMDB_V4_TOKEN>`.
- **Favorites**
  - `GET /favorites/` reads favorites **from TMDb**.
  - `POST /favorites/` toggles favorite **on TMDb**.
  - No rows are created/updated locally for favorites.
- **Shared favorites**
  - `POST /favorites/share/` stores only `{account_id, list_name}`; if the same `account_id` shares again, the `list_name` is **updated** (idempotent).
  - `GET /favorites/shared/{list_name}/` resolves `account_id` and fetches the list **live from TMDb**.

---

## Project Layout
```
config/
  settings/
    base.py
favorites/
  models.py         # FavoritedList (only account_id + list_name)
  serializers.py
  views.py          # favorites + share + shared (TMDb-backed)
tmdb/
  client.py         # TMDb client
  serializers.py
  views.py          # discover, search, movie details (TMDb-backed)
tests/
  favorites/
    test_views.py
  tmdb/
    test_views.py
```

---

## Setup

### 1) Clone
```bash
git clone https://github.com/<your-username>/movies-api.git
cd movies-api
```

### 2) Install Poetry
```bash
curl -sSL https://install.python-poetry.org | python3 -
poetry --version
```

### 3) Install deps
```bash
poetry install --no-root
```

### 4) Migrate DB
> The DB is only used for `FavoritedList` (sharing feature).
```bash
poetry run python manage.py migrate
```

### 5) Run
```bash
poetry run python manage.py runserver
```

Swagger / Redoc:
- Swagger UI: `http://localhost:8000/api/docs/`  
- OpenAPI JSON: `http://localhost:8000/api/schema/`

---

## Environment

Create a `.env`:
```ini
DEBUG=True
SECRET_KEY=change-me
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# TMDb (V4 token). Keep the "Bearer " prefix.
TMDB_API_KEY=Bearer <your_tmdb_v4_token>

# Frontend (Vite default)
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

> For local SQLite: `DATABASE_URL=sqlite:///db.sqlite3`

---

## Commands

| Command | What it does |
|---|---|
| `poetry run python manage.py runserver` | Dev server |
| `poetry run python manage.py migrate` | Apply migrations |
| `poetry run pytest -q` | Run tests |
| `make run` / `make test` / `make lint` / `make type` | If you use the Makefile |

---

## API

### Auth header (required for TMDb-backed routes)
```
Authorization: Bearer <TMDB_V4_TOKEN>
```

### Movies

| Method | Route | Description | Query |
|---|---|---|---|
| GET | `/api/v1/movies/discover/` | Discover (TMDb) | `language`, `page`, `include_adult`, `include_video`, `sort_by`, `account_id` *(optional, to mark `favorite` via TMDb)* |
| GET | `/api/v1/movies/search/` | Search by title (TMDb) | `query` **required**, `language`, `page`, `account_id` *(optional to mark favorites)* |
| GET | `/api/v1/movies/{tmdb_id}/` | Details (TMDb) | — |

**Examples**
```bash
# Discover
curl 'http://localhost:8000/api/v1/movies/discover/?page=1&language=pt-BR&account_id=123'   -H 'Authorization: Bearer <TMDB_V4_TOKEN>'

# Search
curl 'http://localhost:8000/api/v1/movies/search/?query=Inception&language=pt-BR&account_id=123'   -H 'Authorization: Bearer <TMDB_V4_TOKEN>'

# Details
curl 'http://localhost:8000/api/v1/movies/27205/'   -H 'Authorization: Bearer <TMDB_V4_TOKEN>'
```

### Favorites (TMDb only)

| Method | Route | Description | Body / Query |
|---|---|---|---|
| GET | `/api/v1/favorites/` | List favorites from TMDb | `account_id` **required**, `page` *(optional)* |
| POST | `/api/v1/favorites/` | Toggle favorite on TMDb | JSON: `{ "account_id": int, "movie_id": int, "favorite": bool=true, "media_type": "movie" }` |

**Examples**
```bash
# List
curl 'http://localhost:8000/api/v1/favorites/?account_id=123'   -H 'Authorization: Bearer <TMDB_V4_TOKEN>'

# Toggle
curl -X POST 'http://localhost:8000/api/v1/favorites/'   -H 'Authorization: Bearer <TMDB_V4_TOKEN>'   -H 'Content-Type: application/json'   -d '{"account_id":123,"movie_id":27205,"favorite":true,"media_type":"movie"}'
```

### Shared favorites

| Method | Route | Description | Body / Path |
|---|---|---|---|
| POST | `/api/v1/favorites/share/` | Create/update a share record; stores **only** `account_id` + `list_name` | JSON: `{ "account_id": 123, "list_name": "My List" }` |
| GET | `/api/v1/favorites/shared/{list_name}/` | Resolve `account_id` and fetch favorites **live** from TMDb | Path: `list_name` |

**Notes**
- If the same `account_id` shares again, the API **updates** the `list_name`.
- The shared GET requires the same `Authorization` header to call TMDb.

---

## Testing

```bash
poetry run pytest -q
```

Current suites:
- `tests/tmdb/test_views.py`: discover, search, details (TMDb mocked)  
- `tests/favorites/test_views.py`: favorites list/toggle (TMDb mocked)

---

## Troubleshooting

| Symptom | Check |
|---|---|
| 401 from TMDb | Header exactly `Authorization: Bearer <token>` (V4). |
| CORS in the browser | Set `CORS_ALLOWED_ORIGINS=http://localhost:5173` (or your front-end URL). |
| DB errors | Only `FavoritedList` uses the DB; run migrations. |
| `favorite` flag missing | Provide `account_id` on discover/search and include a valid `Authorization` header so the API can read favorites on TMDb. |

---

## Deploy & Rationale

**Production URLs**
- Front (Vercel): https://rate-movies-ag.vercel.app/  
- Back (Render): https://rate-movies-api.onrender.com

**Why Render for Backend + Postgres?**
- **Simple DX**: build/deploy from Git, real-time logs, easy env vars.  
- **Practical free tier** for prototyping/PoCs.  
- **Integrations**: managed web services, workers, and databases (Postgres) with quick setup.  
- **Basic scalability** without re-planning infra — a great fit for this project phase.

> ⚠️ **Heads up (Render Free Plan)**  
> Render **idles** the service after ~**5 minutes** without traffic. The first request afterwards will suffer a **cold start**, which may take **up to ~50s**. This is expected for the free tier.

---

## Limitations & Next Steps

Because my current full-time job takes most of my day, I couldn’t implement several nice-to-have features yet:

- **Metrics** (APM, dashboards, distributed tracing)  
- **Watchlist** (besides favorites)  
- **TV routes** (current focus is Movie)  
- **Higher coverage** (more unit/integration tests and error scenarios)  
- Additional robustness/observability/CI-CD improvements

Each repository’s README explains the tech choices and how to run things in more detail.
