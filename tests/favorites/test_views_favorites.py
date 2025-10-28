from unittest.mock import MagicMock, patch

import pytest
from rest_framework import status
from rest_framework.test import APIRequestFactory

from core.constants import (
    TMDB_API_BASE,
    TMDB_DEFAULT_LANG,
    TMDB_REQUEST_TIMEOUT,
    Headers,
    QueryParams,
    SortBy,
    TMDBPaths,
)
from favorites.views import FavoritesView


@pytest.fixture
def api_factory():
    return APIRequestFactory()


class TestFavoritesViewGET:
    def test_missing_account_id_returns_400(self, api_factory):
        request = api_factory.get("/api/v1/favorites/")
        view = FavoritesView.as_view()
        resp = view(request)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "account_id" in resp.data["error"]

    def test_missing_authorization_header_returns_401(self, api_factory):
        request = api_factory.get("/api/v1/favorites/?account_id=999")
        view = FavoritesView.as_view()
        resp = view(request)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Authorization" in resp.data["error"]

    @patch(
        "favorites.services.SharedListService.latest_name_for_account",
        return_value=None,
    )
    @patch("favorites.services.requests.get")
    def test_successful_get_calls_tmdb_api(self, mock_get, _mock_latest, api_factory):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"results": [{"id": 123, "title": "Movie A"}]}
        mock_get.return_value = mock_resp

        headers = {"HTTP_AUTHORIZATION": "Bearer test_token"}
        request = api_factory.get("/api/v1/favorites/?account_id=42&page=1", **headers)
        view = FavoritesView.as_view()
        resp = view(request)

        assert resp.status_code == status.HTTP_200_OK
        called_url = mock_get.call_args.kwargs.get("url") or mock_get.call_args.args[0]
        called_params = mock_get.call_args.kwargs["params"]
        assert (
            called_url
            == f"{TMDB_API_BASE}{TMDBPaths.ACCOUNT_FAVORITES.format(account_id=42)}"
        )
        assert called_params == {
            QueryParams.LANGUAGE: TMDB_DEFAULT_LANG,
            QueryParams.PAGE: "1",
            QueryParams.SORT_BY: SortBy.CREATED_AT_ASC,
        }
        assert resp.data == {"results": [{"id": 123, "title": "Movie A"}]}


class TestFavoritesViewPOST:
    def test_missing_required_fields_returns_400(self, api_factory):
        headers = {"HTTP_AUTHORIZATION": "Bearer token"}
        request = api_factory.post(
            "/api/v1/favorites/", {"account_id": 1}, format="json", **headers
        )
        view = FavoritesView.as_view()
        resp = view(request)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "movie_id" in resp.data

    def test_missing_authorization_header_returns_401(self, api_factory):
        payload = {"account_id": 1, "movie_id": 100}
        request = api_factory.post("/api/v1/favorites/", payload, format="json")
        view = FavoritesView.as_view()
        resp = view(request)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Authorization" in resp.data["error"]

    @patch("favorites.services.requests.post")
    def test_favorite_calls_tmdb(self, mock_post, api_factory):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status_message": "Success."}
        mock_post.return_value = mock_resp

        headers = {"HTTP_AUTHORIZATION": "Bearer test_token"}
        payload = {"account_id": 10, "movie_id": 555, "favorite": True}
        request = api_factory.post(
            "/api/v1/favorites/", payload, format="json", **headers
        )
        view = FavoritesView.as_view()
        resp = view(request)

        called_url = mock_post.call_args.args[0]
        called_headers = mock_post.call_args.kwargs["headers"]
        called_json = mock_post.call_args.kwargs["json"]
        called_timeout = mock_post.call_args.kwargs["timeout"]

        assert (
            called_url
            == f"{TMDB_API_BASE}{TMDBPaths.ACCOUNT_FAVORITE_TOGGLE.format(account_id=10)}"
        )
        assert called_headers[Headers.AUTHORIZATION] == "Bearer test_token"
        assert called_json == {"media_type": "movie", "media_id": 555, "favorite": True}
        assert called_timeout == TMDB_REQUEST_TIMEOUT
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["status_message"] == "Success."

    @patch("favorites.services.requests.post")
    def test_unfavorite_calls_tmdb(self, mock_post, api_factory):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status_message": "Removed."}
        mock_post.return_value = mock_resp

        headers = {"HTTP_AUTHORIZATION": "Bearer test_token"}
        payload = {"account_id": 20, "movie_id": 888, "favorite": False}
        request = api_factory.post(
            "/api/v1/favorites/", payload, format="json", **headers
        )
        view = FavoritesView.as_view()
        resp = view(request)

        assert mock_post.call_args.kwargs["json"] == {
            "media_type": "movie",
            "media_id": 888,
            "favorite": False,
        }
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["status_message"] == "Removed."

    def test_missing_required_fields_returns_400(self, api_factory):
        headers = {"HTTP_AUTHORIZATION": "Bearer token"}
        request = api_factory.post(
            "/api/v1/favorites/", {"account_id": 1}, format="json", **headers
        )
        view = FavoritesView.as_view()
        resp = view(request)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "movie_id" in resp.data

    def test_missing_authorization_header_returns_401(self, api_factory):
        payload = {"account_id": 1, "movie_id": 100}
        request = api_factory.post("/api/v1/favorites/", payload, format="json")
        view = FavoritesView.as_view()
        resp = view(request)
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Authorization" in resp.data["error"]

    @patch("favorites.services.requests.post")
    def test_favorite_calls_tmdb(self, mock_post, api_factory):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status_message": "Success."}
        mock_post.return_value = mock_resp

        headers = {"HTTP_AUTHORIZATION": "Bearer test_token"}
        payload = {"account_id": 10, "movie_id": 555, "favorite": True}
        request = api_factory.post(
            "/api/v1/favorites/", payload, format="json", **headers
        )
        view = FavoritesView.as_view()
        resp = view(request)

        called_url = mock_post.call_args.args[0]
        called_headers = mock_post.call_args.kwargs["headers"]
        called_json = mock_post.call_args.kwargs["json"]
        called_timeout = mock_post.call_args.kwargs["timeout"]

        assert (
            called_url
            == f"{TMDB_API_BASE}{TMDBPaths.ACCOUNT_FAVORITE_TOGGLE.format(account_id=10)}"
        )
        assert called_headers[Headers.AUTHORIZATION] == "Bearer test_token"
        assert called_json == {"media_type": "movie", "media_id": 555, "favorite": True}
        assert called_timeout == TMDB_REQUEST_TIMEOUT
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["status_message"] == "Success."

    @patch("favorites.services.requests.post")
    def test_unfavorite_calls_tmdb(self, mock_post, api_factory):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status_message": "Removed."}
        mock_post.return_value = mock_resp

        headers = {"HTTP_AUTHORIZATION": "Bearer test_token"}
        payload = {"account_id": 20, "movie_id": 888, "favorite": False}
        request = api_factory.post(
            "/api/v1/favorites/", payload, format="json", **headers
        )
        view = FavoritesView.as_view()
        resp = view(request)

        assert mock_post.call_args.kwargs["json"] == {
            "media_type": "movie",
            "media_id": 888,
            "favorite": False,
        }
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["status_message"] == "Removed."
