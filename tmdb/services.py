from __future__ import annotations

from typing import Any, Iterable

import requests

from core.constants import (
    TMDB_API_BASE,
    TMDB_DEFAULT_LANG,
    TMDB_REQUEST_TIMEOUT,
    Headers,
    QueryParams,
    SortBy,
    TMDBPaths,
)
from tmdb.client import TMDBClient


class TMDBService:
    def __init__(self, bearer_token: str | None) -> None:
        self.client = TMDBClient(bearer_token=bearer_token)

    def discover(self, params: dict[str, Any]) -> dict[str, Any]:
        return self.client.discover_movies(params=params)

    def details(self, tmdb_id: int) -> dict[str, Any]:
        return self.client.movie_details(tmdb_id)

    def search_movies(
        self, query: str, page: int | str = 1, language: str = TMDB_DEFAULT_LANG
    ) -> dict[str, Any]:
        resp = requests.get(
            f"{TMDB_API_BASE}{TMDBPaths.SEARCH_MOVIE}",
            params={
                QueryParams.QUERY: query,
                QueryParams.PAGE: page,
                QueryParams.LANGUAGE: language,
                QueryParams.INCLUDE_ADULT: False,
            },
            headers=self.client.session.headers,
            timeout=TMDB_REQUEST_TIMEOUT,
        )
        return resp.json()

    def fetch_favorite_ids(self, account_id: int | str) -> set[int]:
        bearer = self.client.session.headers.get(Headers.AUTHORIZATION)
        if not bearer:
            return set()

        page = 1
        favorite_ids: set[int] = set()
        endpoint = f"{TMDB_API_BASE}{TMDBPaths.ACCOUNT_FAVORITES.format(account_id=account_id)}"

        while True:
            resp = requests.get(
                endpoint,
                params={
                    QueryParams.LANGUAGE: TMDB_DEFAULT_LANG,
                    QueryParams.PAGE: page,
                    QueryParams.SORT_BY: SortBy.CREATED_AT_ASC,
                },
                headers={
                    Headers.AUTHORIZATION: bearer,
                    Headers.ACCEPT: Headers.JSON_CT,
                },
                timeout=TMDB_REQUEST_TIMEOUT,
            )
            if resp.status_code >= 400:
                return set()

            payload = resp.json()
            for item in payload.get("results", []):
                movie_id = item.get("id")
                if isinstance(movie_id, int):
                    favorite_ids.add(movie_id)

            total_pages = payload.get("total_pages") or 1
            if page >= total_pages:
                break
            page += 1

        return favorite_ids

    def annotate_favorites(
        self, results: Iterable[dict[str, Any]], favorite_ids: set[int]
    ) -> None:
        for movie in results:
            movie["favorite"] = (
                bool(movie.get("id") in favorite_ids) if favorite_ids else False
            )
