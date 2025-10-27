# Movies & Favorites API (Django + DRF)

Backend (Django + DRF) that integrates with **TMDb**.  
It exposes endpoints to **discover**, **search**, and **fetch movie details** from TMDb, plus **favorites** operations that act **directly on TMDb**.  
For sharing, the API stores **only** `account_id` and a human-friendly `list_name`. The shared listing itself is fetched **live from TMDb**.

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

---

## Overview
This service plays the role of a **BFF** for a movie app:

- **Discover/Search** movies (TMDb).
- **Movie details** (trailers/providers/credits handled inside the details view).
- **Favorites**: list and toggle **on TMDb** (no local persistence).
- **Shared favorites**: store only `account_id` + `list_name`; when someone opens a shared list, the API fetches the **current** favorites from TMDb for that account.

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

- **Authorization**: All TMDb calls require header `Authorization: Bearer <TMDB_V4_TOKEN>`.
- **Favorites**:
  - `GET /favorites/` reads favorites **from TMDb**.
  - `POST /favorites/` toggles favorite **on TMDb**.
  - No rows are created/updated for favorites locally.
- **Shared favorites**:
  - `POST /favorites/share/` stores only `{account_id, list_name}`.
    - If the same `account_id` shares again, we **update** the `list_name` (idempotent).
  - `GET /favorites/shared/{list_name}/` loads the record to resolve `account_id` and then fetches **live** favorites from TMDb.

---

## Project Layout
```
config/
  settings/
    base.py
favorites/
  models.py         # FavoritedList (stores only account_id + list_name)
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
> DB is only used for `FavoritedList` (share feature).
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

Create `.env`:
```ini
DEBUG=True
SECRET_KEY=change-me
DATABASE_URL=postgrsql://...

# TMDb (V4 token). Keep the "Bearer " prefix.
TMDB_API_KEY=Bearer <your_tmdb_v4_token>

# Frontend (Vite default)
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

> For Postgres, set `DATABASE_URL=postgres://user:pass@host:5432/dbname`.

---

## Commands

| Command | What it does |
|---|---|
| `poetry run python manage.py runserver` | Dev server |
| `poetry run python manage.py migrate` | Apply migrations |
| `poetry run pytest -q` | Run tests |
| `make run` / `make test` / `make lint` / `make type` | If you use the provided Makefile |

---

## API

### Auth header (required for TMDb-backed routes)
```
Authorization: Bearer <TMDB_V4_TOKEN>
```

### Movies

| Method | Route | Description | Query |
|---|---|---|---|
| GET | `/api/v1/movies/discover/` | Discover movies (TMDb) | `language`, `page`, `include_adult`, `include_video`, `sort_by`, `account_id` *(optional, used to flag `favorite` via TMDb favorites)* |
| GET | `/api/v1/movies/search/` | Search movies by title (TMDb) | `query` **required**, `language`, `page`, `account_id` *(optional to flag favorites)* |
| GET | `/api/v1/movies/{tmdb_id}/` | Movie details (TMDb) | — |

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
| POST | `/api/v1/favorites/share/` | Create or update a share record; stores **only** `account_id` + `list_name` | JSON: `{ "account_id": 123, "list_name": "My List" }` |
| GET | `/api/v1/favorites/shared/{list_name}/` | Resolve `account_id` by `list_name`, then fetch **live** favorites from TMDb | Path: `list_name` |

**Notes**
- If the same `account_id` shares again, the API **updates** the `list_name` instead of creating another record.
- Shared GET requires the same `Authorization` header to call TMDb.

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
| 401 from TMDb | Ensure the header is exactly `Authorization: Bearer <token>` (V4 Auth). |
| CORS in the browser | Set `CORS_ALLOWED_ORIGINS=http://localhost:5173` (or your front-end URL). |
| DB errors | Only `FavoritedList` uses the DB; run migrations. |
| “favorite” flag not appearing | Provide `account_id` in discover/search queries and include a valid `Authorization` header so the API can read favorites from TMDb. |

---
