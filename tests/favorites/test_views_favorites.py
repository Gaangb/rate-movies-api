from unittest.mock import MagicMock, patch

import pytest
from rest_framework import status
from rest_framework.test import APIRequestFactory

from favorites.views import TMDB_BASE_URL, FavoritesView


@pytest.fixture
def api_factory():
    return APIRequestFactory()


@pytest.mark.django_db
class TestFavoritesViewGET:
    def test_missing_account_id_returns_400(self, api_factory):
        request = api_factory.get("/api/v1/favorites/")
        view = FavoritesView.as_view()

        response = view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "account_id" in response.data["error"]

    def test_missing_authorization_header_returns_401(self, api_factory):
        request = api_factory.get("/api/v1/favorites/?account_id=999")
        view = FavoritesView.as_view()

        response = view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Authorization" in response.data["error"]

    @patch("favorites.views.requests.get")
    def test_successful_get_calls_tmdb_api(self, mock_get, api_factory):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"results": [{"id": 123, "title": "Movie A"}]}
        mock_get.return_value = mock_resp

        headers = {"HTTP_AUTHORIZATION": "Bearer test_token"}
        request = api_factory.get("/api/v1/favorites/?account_id=42&page=1", **headers)
        view = FavoritesView.as_view()

        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        mock_get.assert_called_once_with(
            f"{TMDB_BASE_URL}/account/42/favorite/movies",
            params={"language": "en-US", "page": "1", "sort_by": "created_at.asc"},
            headers={
                "Authorization": "Bearer test_token",
                "Accept": "application/json",
                "Content-Type": "application/json;charset=utf-8",
            },
            timeout=10,
        )
        assert response.data == {"results": [{"id": 123, "title": "Movie A"}]}


@pytest.mark.django_db
class TestFavoritesViewPOST:
    def test_missing_required_fields_returns_400(self, api_factory):
        headers = {"HTTP_AUTHORIZATION": "Bearer token"}
        # falta movie_id -> DRF retorna erros do serializer
        request = api_factory.post("/api/v1/favorites/", {"account_id": 1}, format="json", **headers)
        view = FavoritesView.as_view()

        response = view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "movie_id" in response.data  # erro do serializer

    def test_missing_authorization_header_returns_401(self, api_factory):
        payload = {"account_id": 1, "movie_id": 100}
        request = api_factory.post("/api/v1/favorites/", payload, format="json")
        view = FavoritesView.as_view()

        response = view(request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Authorization" in response.data["error"]

    @patch("favorites.views.requests.post")
    def test_favorite_calls_tmdb(self, mock_post, api_factory):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status_message": "Success."}
        mock_post.return_value = mock_resp

        headers = {"HTTP_AUTHORIZATION": "Bearer test_token"}
        payload = {"account_id": 10, "movie_id": 555, "favorite": True}
        request = api_factory.post("/api/v1/favorites/", payload, format="json", **headers)
        view = FavoritesView.as_view()

        response = view(request)

        mock_post.assert_called_once_with(
            f"{TMDB_BASE_URL}/account/10/favorite",
            headers={
                "Authorization": "Bearer test_token",
                "Accept": "application/json",
                "Content-Type": "application/json;charset=utf-8",
            },
            json={"media_type": "movie", "media_id": 555, "favorite": True},
            timeout=10,
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status_message"] == "Success."

    @patch("favorites.views.requests.post")
    def test_unfavorite_calls_tmdb(self, mock_post, api_factory):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status_message": "Removed."}
        mock_post.return_value = mock_resp

        headers = {"HTTP_AUTHORIZATION": "Bearer test_token"}
        payload = {"account_id": 20, "movie_id": 888, "favorite": False}
        request = api_factory.post("/api/v1/favorites/", payload, format="json", **headers)
        view = FavoritesView.as_view()

        response = view(request)

        mock_post.assert_called_once_with(
            f"{TMDB_BASE_URL}/account/20/favorite",
            headers={
                "Authorization": "Bearer test_token",
                "Accept": "application/json",
                "Content-Type": "application/json;charset=utf-8",
            },
            json={"media_type": "movie", "media_id": 888, "favorite": False},
            timeout=10,
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status_message"] == "Removed."
