from contextlib import nullcontext
from unittest.mock import MagicMock, patch

import pytest

from core.constants import (
    TMDB_API_BASE,
    TMDB_DEFAULT_LANG,
    TMDB_REQUEST_TIMEOUT,
    Headers,
    QueryParams,
    SortBy,
    TMDBPaths,
)
from favorites import models as fav_models
from favorites.services import FavoritesService, SharedListService


@pytest.fixture(autouse=True)
def _neutralize_atomic(monkeypatch):
    try:
        monkeypatch.setattr("favorites.services.atomic", lambda: nullcontext())
    except AttributeError:
        pass

    try:
        monkeypatch.setattr(
            "favorites.services.transaction.atomic", lambda: nullcontext()
        )
    except AttributeError:
        pass


@pytest.fixture
def mock_favorited_list(monkeypatch):
    state = [
        {"account_id": 1, "list_name": "mylist"},
        {"account_id": 2, "list_name": "shared"},
        {"account_id": 7, "list_name": "new"},
    ]

    def _to_instance(row: dict) -> MagicMock:
        inst = MagicMock()
        inst.account_id = row["account_id"]
        inst.list_name = row["list_name"]

        def _save(update_fields=None):
            for r in state:
                if r["account_id"] == inst.account_id:
                    r["list_name"] = inst.list_name
                    break

        inst.save.side_effect = _save
        return inst

    class _VLS:
        """Objeto retornado por values_list(...), oferecendo .first()."""

        def __init__(self, values):
            self._values = values

        def first(self):
            return self._values[0] if self._values else None

    class _QS:
        def __init__(self, items):
            self._items = list(items)

        def filter(self, **kwargs):
            items = self._items
            for k, v in kwargs.items():
                if k == "list_name__iexact":
                    items = [
                        i for i in items if i["list_name"].lower() == str(v).lower()
                    ]
                elif k == "account_id":
                    items = [i for i in items if i["account_id"] == v]
            return _QS(items)

        def exclude(self, **kwargs):
            items = self._items
            for k, v in kwargs.items():
                if k == "account_id":
                    items = [i for i in items if i["account_id"] != v]
            return _QS(items)

        def exists(self):
            return bool(self._items)

        def first(self):
            return _to_instance(self._items[0]) if self._items else None

        def order_by(self, *_args, **_kw):
            return self

        def values_list(self, field, flat=False):
            vals = [i[field] for i in self._items]
            return _VLS(vals if flat else [(v,) for v in vals])

    objects = MagicMock()

    def _objects_filter(**kwargs):
        return _QS(state).filter(**kwargs)

    def _objects_create(**kwargs):
        row = {"account_id": kwargs["account_id"], "list_name": kwargs["list_name"]}
        state.append(row)
        return _to_instance(row)

    objects.filter.side_effect = _objects_filter
    objects.create.side_effect = _objects_create

    monkeypatch.setattr(fav_models.FavoritedList, "objects", objects)
    return {"objects": objects, "state": state}


class TestSharedListService:
    def test_is_name_in_use_without_exclude(self, mock_favorited_list):
        assert SharedListService.is_name_in_use("mylist") is True
        assert SharedListService.is_name_in_use("other") is False

    def test_is_name_in_use_with_exclude(self, mock_favorited_list):
        assert SharedListService.is_name_in_use("shared", exclude_account_id=2) is False
        assert SharedListService.is_name_in_use("shared", exclude_account_id=1) is True

    def test_latest_name_for_account(self, mock_favorited_list):
        assert SharedListService.latest_name_for_account(7) == "new"
        assert SharedListService.latest_name_for_account(99) is None

    def test_upsert_creates_when_not_exists(self, mock_favorited_list):
        inst, created = SharedListService.upsert(10, "october")
        assert created is True
        assert inst.account_id == 10
        assert inst.list_name == "october"
        state = mock_favorited_list["state"]
        assert any(
            r for r in state if r["account_id"] == 10 and r["list_name"] == "october"
        )

    def test_upsert_updates_when_exists(self, mock_favorited_list):
        SharedListService.upsert(10, "old")
        inst, created = SharedListService.upsert(10, "new")
        assert created is False
        assert inst.account_id == 10
        assert inst.list_name == "new"
        state = mock_favorited_list["state"]
        assert any(
            r for r in state if r["account_id"] == 10 and r["list_name"] == "new"
        )


class TestFavoritesService:
    @patch("favorites.services.requests.get")
    def test_list_favorites_calls_tmdb_with_expected_params(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"results": []}
        mock_get.return_value = mock_resp

        headers = {
            Headers.AUTHORIZATION: "Bearer token",
            Headers.ACCEPT: Headers.JSON_CT,
            Headers.CONTENT_TYPE: Headers.JSON_UTF8,
        }
        service = FavoritesService(tmdb_headers=headers)

        payload, status_code = service.list_tmdb_favorites(
            account_id=42,
            page="2",
        )

        assert status_code == 200
        assert payload == {"results": []}

        called_url = mock_get.call_args.kwargs.get("url") or mock_get.call_args.args[0]
        called_params = mock_get.call_args.kwargs["params"]
        called_headers = mock_get.call_args.kwargs["headers"]
        called_timeout = mock_get.call_args.kwargs["timeout"]

        assert (
            called_url
            == f"{TMDB_API_BASE}{TMDBPaths.ACCOUNT_FAVORITES.format(account_id=42)}"
        )
        assert called_params == {
            QueryParams.LANGUAGE: TMDB_DEFAULT_LANG,
            QueryParams.PAGE: "2",
            QueryParams.SORT_BY: SortBy.CREATED_AT_ASC,
        }
        assert called_headers == headers
        assert called_timeout == TMDB_REQUEST_TIMEOUT

    @patch("favorites.services.requests.post")
    def test_toggle_favorite_calls_tmdb_post(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status_message": "Success."}
        mock_post.return_value = mock_resp

        headers = {
            Headers.AUTHORIZATION: "Bearer token",
            Headers.ACCEPT: Headers.JSON_CT,
            Headers.CONTENT_TYPE: Headers.JSON_UTF8,
        }
        service = FavoritesService(tmdb_headers=headers)

        payload, status_code = service.toggle_tmdb_favorite(
            account_id=99,
            movie_id=27205,
            favorite=True,
            media_type="movie",
        )

        assert status_code == 200
        assert payload == {"status_message": "Success."}

        called_url = mock_post.call_args.args[0]
        called_headers = mock_post.call_args.kwargs["headers"]
        called_json = mock_post.call_args.kwargs["json"]
        called_timeout = mock_post.call_args.kwargs["timeout"]

        assert (
            called_url
            == f"{TMDB_API_BASE}{TMDBPaths.ACCOUNT_FAVORITE_TOGGLE.format(account_id=99)}"
        )
        assert called_headers == headers
        assert called_json == {
            "media_type": "movie",
            "media_id": 27205,
            "favorite": True,
        }
        assert called_timeout == TMDB_REQUEST_TIMEOUT

    @patch("favorites.services.requests.get")
    def test_fetch_all_tmdb_favorites_paginates_and_stops(self, mock_get):
        mock_get.side_effect = [
            MagicMock(
                status_code=200, json=lambda: {"results": [{"id": 1}], "total_pages": 2}
            ),
            MagicMock(
                status_code=200, json=lambda: {"results": [{"id": 2}], "total_pages": 2}
            ),
        ]

        headers = {Headers.AUTHORIZATION: "Bearer token"}
        service = FavoritesService(tmdb_headers=headers)

        items = service.fetch_all_tmdb_favorites(account_id=5)
        assert items == [{"id": 1}, {"id": 2}]
        assert mock_get.call_count == 2

    @patch("favorites.services.requests.get")
    def test_fetch_all_tmdb_favorites_handles_upstream_error(self, mock_get):
        mock_get.return_value = MagicMock(status_code=500, json=lambda: {})
        headers = {Headers.AUTHORIZATION: "Bearer token"}
        service = FavoritesService(tmdb_headers=headers)

        items = service.fetch_all_tmdb_favorites(account_id=5)
        assert items == []
