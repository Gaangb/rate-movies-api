from unittest.mock import MagicMock, patch

from core.constants import (
    TMDB_API_BASE,
    TMDB_DEFAULT_LANG,
    TMDB_REQUEST_TIMEOUT,
    Headers,
    QueryParams,
    TMDBPaths,
)
from tmdb.services import TMDBService


def _resp(status_code: int, payload: dict):
    r = MagicMock()
    r.status_code = status_code
    r.json.return_value = payload
    return r


class TestTMDBServiceDiscover:
    @patch("tmdb.services.TMDBClient")
    def test_discover_uses_client_and_returns_payload(self, mock_client):
        mock_instance = MagicMock()
        mock_instance.discover_movies.return_value = {
            "page": 1,
            "results": [{"id": 1}],
            "total_pages": 1,
        }
        mock_client.return_value = mock_instance

        service = TMDBService(bearer_token="Bearer token")
        payload = service.discover(
            params={QueryParams.LANGUAGE: TMDB_DEFAULT_LANG, QueryParams.PAGE: 2}
        )

        assert payload["results"][0]["id"] == 1
        mock_instance.discover_movies.assert_called_once_with(
            params={QueryParams.LANGUAGE: TMDB_DEFAULT_LANG, QueryParams.PAGE: 2}
        )


class TestTMDBServiceSearch:
    @patch("tmdb.services.requests.get")
    def test_search_movies_includes_include_adult_false(self, mock_get):
        mock_get.return_value = _resp(
            200, {"page": 1, "results": [{"id": 10}], "total_pages": 1}
        )

        service = TMDBService(bearer_token="Bearer XXX")
        payload = service.search_movies(query="Inception", page=3, language="en-US")

        assert payload["results"][0]["id"] == 10

        called_url = mock_get.call_args.kwargs.get("url") or mock_get.call_args.args[0]
        called_params = mock_get.call_args.kwargs["params"]
        called_headers = mock_get.call_args.kwargs["headers"]
        called_timeout = mock_get.call_args.kwargs["timeout"]

        assert called_url == f"{TMDB_API_BASE}{TMDBPaths.SEARCH_MOVIE}"
        assert called_params[QueryParams.QUERY] == "Inception"
        assert called_params[QueryParams.PAGE] == 3
        assert called_params[QueryParams.LANGUAGE] == "en-US"
        assert called_params[QueryParams.INCLUDE_ADULT] is False
        assert called_headers[Headers.AUTHORIZATION] == "Bearer XXX"
        assert called_timeout == TMDB_REQUEST_TIMEOUT


class TestTMDBServiceFavoriteIds:
    @patch("tmdb.services.requests.get")
    def test_fetch_favorite_ids_paginates(self, mock_get):
        mock_get.side_effect = [
            _resp(200, {"results": [{"id": 100}], "total_pages": 2}),
            _resp(200, {"results": [{"id": 200}], "total_pages": 2}),
        ]

        service = TMDBService(bearer_token="Bearer z")
        ids = service.fetch_favorite_ids(account_id=777)

        assert ids == {100, 200}
        assert mock_get.call_count == 2

        first_call = mock_get.call_args_list[0]
        first_url = first_call.kwargs.get("url") or first_call.args[0]
        first_params = first_call.kwargs["params"]
        first_headers = first_call.kwargs["headers"]

        assert (
            first_url
            == f"{TMDB_API_BASE}{TMDBPaths.ACCOUNT_FAVORITES.format(account_id=777)}"
        )
        assert first_params[QueryParams.PAGE] == 1
        assert first_params[QueryParams.LANGUAGE] == TMDB_DEFAULT_LANG
        assert first_headers[Headers.AUTHORIZATION] == "Bearer z"

    def test_fetch_favorite_ids_without_bearer_returns_empty(self):
        service = TMDBService(bearer_token=None)
        assert service.fetch_favorite_ids(account_id=1) == set()


class TestTMDBServiceAnnotateFavorites:
    def test_annotate_favorites_sets_flags(self):
        service = TMDBService(bearer_token="Bearer t")
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        favs = {2, 3}
        service.annotate_favorites(items, favs)
        flags = {m["id"]: m["favorite"] for m in items}
        assert flags[1] is False
        assert flags[2] is True
        assert flags[3] is True


class TestTMDBServiceDetails:
    @patch("tmdb.services.TMDBClient")
    def test_details_uses_client_and_returns_payload(self, mock_client):
        mock_instance = MagicMock()
        mock_instance.movie_details.return_value = {
            "id": 500,
            "title": "Interstellar",
            "videos": [],
            "providers": {},
            "credits": [],
        }
        mock_client.return_value = mock_instance

        service = TMDBService(bearer_token="Bearer tok")
        payload = service.details(500)

        assert payload["id"] == 500
        mock_instance.movie_details.assert_called_once_with(500)
