# Movies & Favorites API (Django + DRF)

A backend service built with **Django** and **Django REST Framework (DRF)** that integrates with **TMDb API** to manage movie data and user favorites.  
This project includes endpoints for listing movies, fetching detailed information (trailers, cast, and streaming providers), handling favorites, and sharing user favorite lists through a generated link.

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Tech Stack](#tech-stack)
3. [Features](#features)
4. [Project Structure](#project-structure)
5. [Setup & Installation](#setup--installation)
6. [Environment Variables](#environment-variables)
7. [Available Commands](#available-commands)
8. [API Endpoints](#api-endpoints)
9. [Testing](#testing)
10. [Troubleshooting](#troubleshooting)

---

## Project Overview
This service acts as a **Backend-for-Frontend (BFF)** for a movie web application.  
It allows clients to:
- Fetch and filter movie data from TMDb.
- Manage user favorites via session-based profiles.
- Share a list of favorites using a generated public link.

---

## Tech Stack
- Python 3.12+
- Django 5.x
- Django REST Framework (DRF)
- django-environ
- django-cors-headers
- django-filter
- drf-spectacular
- requests
- pytest + model-bakery
- Poetry 2.x

---

## Features

### Movies
1. List all movies  
2. Get movie by ID  
   - Fetch movie details  
   - Fetch trailer  
   - Fetch cast  
   - Fetch streaming providers  
3. Search movies by name  

### Favorites
4. Add or remove a movie from favorites  
5. Share favorites list  
   - Generates a public link based on user session  
   - Accepts a name parameter in the request  

### Other
6. Swagger documentation generated with drf-spectacular  

---

## Project Structure
```
config/
  settings/
    base.py
    local.py
    prod.py
favorites/
  models.py
  serializers.py
  views.py
  services.py
tmdb/
  client.py
  views.py
tests/
  test_favorites.py
  test_tmdb.py
```

---

## Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/movies-api.git
cd movies-api
```

---

### 2. Install Poetry (v2.x recommended)
If you don’t have Poetry installed, run:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Then verify the installation:
```bash
poetry --version
```

> **Note:** Poetry 2 no longer creates virtual environments automatically with `poetry shell`.  
> You can activate the environment manually using:
> ```bash
> poetry env use 3.12
> poetry shell
> ```

If you prefer not to activate the shell, prefix all commands with `poetry run`.

---

### 3. Configure the project environment
Install dependencies:
```bash
poetry install --no-root
```

---

### 4. Apply database migrations
```bash
poetry run python manage.py migrate
```

---

### 5. Run the development server
```bash
poetry run python manage.py runserver
```

Swagger documentation will be available at:
```
http://localhost:8000/api/docs/
```

---

## Environment Variables

Copy the example file:
```bash
cp .env.example .env
```

Edit `.env`:
```
DEBUG=True
SECRET_KEY=change-me
DATABASE_URL=sqlite:///db.sqlite3
TMDB_API_KEY=Bearer <your_tmdb_v4_token>
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

---

## Available Commands

| Command | Description |
|----------|-------------|
| `make run` | Start the development server |
| `make migrate` | Apply migrations |
| `make test` | Run all tests |
| `make lint` | Format and lint the codebase |
| `make type` | Run mypy type checks |

---

## API Endpoints

| Method | Endpoint | Description |
|---------|-----------|-------------|
| GET | `/api/v1/movies/` | List all movies |
| GET | `/api/v1/movies/{id}/` | Get movie details |
| GET | `/api/v1/movies/{id}/trailer/` | Get trailer |
| GET | `/api/v1/movies/{id}/cast/` | Get cast |
| GET | `/api/v1/movies/{id}/providers/` | Get streaming providers |
| GET | `/api/v1/search/?q={name}` | Search movies by name |
| GET | `/api/v1/favorites/` | List user favorites |
| POST | `/api/v1/favorites/` | Add movie to favorites |
| DELETE | `/api/v1/favorites/{tmdb_id}/` | Remove movie from favorites |
| POST | `/api/v1/favorites/share/` | Generate a public share link |

---

## Testing

Run all tests:
```bash
poetry run pytest -q
```

Recommended tools:
- pytest
- pytest-django
- model-bakery

---

## Troubleshooting

| Issue | Solution |
|--------|-----------|
| `poetry shell` not found | Use `poetry run ...` or `poetry env activate` |
| Package installation errors | Add `package-mode = false` in `pyproject.toml` |
| TMDb 401 Unauthorized | Check if `TMDB_API_KEY` includes the `Bearer` prefix |
| CORS issues | Ensure `CORS_ALLOWED_ORIGINS` is properly set in `.env` |

---
