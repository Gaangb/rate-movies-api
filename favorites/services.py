from __future__ import annotations

from typing import Any, Dict, Iterable, Optional, Tuple

import requests
from django.db import IntegrityError, transaction

from core.constants import (
    TMDB_API_BASE,
    TMDB_DEFAULT_LANG,
    TMDB_REQUEST_TIMEOUT,
    QueryParams,
    SortBy,
    TMDBPaths,
)
from favorites.models import FavoritedList


class FavoritesService:
    def __init__(self, tmdb_headers: Optional[Dict[str, str]] = None) -> None:
        self.tmdb_headers = tmdb_headers or {}

    def list_tmdb_favorites(
        self, account_id: int | str, page: int | str = 1
    ) -> Tuple[Dict[str, Any], int]:
        url = f"{TMDB_API_BASE}{TMDBPaths.ACCOUNT_FAVORITES.format(account_id=account_id)}"
        resp = requests.get(
            url,
            params={
                QueryParams.LANGUAGE: TMDB_DEFAULT_LANG,
                QueryParams.PAGE: page,
                QueryParams.SORT_BY: SortBy.CREATED_AT_ASC,
            },
            headers=self.tmdb_headers,
            timeout=TMDB_REQUEST_TIMEOUT,
        )
        return resp.json(), resp.status_code

    def toggle_tmdb_favorite(
        self,
        account_id: int | str,
        movie_id: int,
        favorite: bool = True,
        media_type: str = "movie",
    ) -> Tuple[Dict[str, Any], int]:
        url = f"{TMDB_API_BASE}{TMDBPaths.ACCOUNT_FAVORITE_TOGGLE.format(account_id=account_id)}"
        payload = {"media_type": media_type, "media_id": movie_id, "favorite": favorite}
        resp = requests.post(
            url,
            headers=self.tmdb_headers,
            json=payload,
            timeout=TMDB_REQUEST_TIMEOUT,
        )
        return resp.json(), resp.status_code

    def fetch_all_tmdb_favorites(self, account_id: int | str) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        page = 1
        url = f"{TMDB_API_BASE}{TMDBPaths.ACCOUNT_FAVORITES.format(account_id=account_id)}"

        while True:
            resp = requests.get(
                url,
                params={
                    QueryParams.LANGUAGE: TMDB_DEFAULT_LANG,
                    QueryParams.PAGE: page,
                    QueryParams.SORT_BY: SortBy.CREATED_AT_ASC,
                },
                headers=self.tmdb_headers,
                timeout=TMDB_REQUEST_TIMEOUT,
            )
            if resp.status_code >= 400:
                return []
            payload = resp.json()
            results: Iterable[dict[str, Any]] = payload.get("results", []) or []
            items.extend(results)
            total_pages = payload.get("total_pages") or 1
            if page >= total_pages:
                break
            page += 1

        return items


class SharedListService:
    @staticmethod
    def is_name_in_use(
        list_name: str, exclude_account_id: Optional[int | str] = None
    ) -> bool:
        qs = FavoritedList.objects.filter(list_name__iexact=list_name)
        if exclude_account_id is not None:
            qs = qs.exclude(account_id=exclude_account_id)
        return qs.exists()

    @staticmethod
    def latest_name_for_account(account_id: int | str) -> Optional[str]:
        return (
            FavoritedList.objects.filter(account_id=account_id)
            .order_by("-created_at")
            .values_list("list_name", flat=True)
            .first()
        )

    @staticmethod
    def upsert(account_id: int | str, list_name: str) -> tuple[FavoritedList, bool]:
        with transaction.atomic():
            existing = (
                FavoritedList.objects.filter(account_id=account_id)
                .order_by("-created_at")
                .first()
            )
            if existing:
                existing.list_name = list_name
                existing.save(update_fields=["list_name"])
                return existing, False

            try:
                created = FavoritedList.objects.create(
                    account_id=account_id,
                    list_name=list_name,
                )
                return created, True
            except IntegrityError as exc:
                raise exc
