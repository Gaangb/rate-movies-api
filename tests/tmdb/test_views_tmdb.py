from unittest.mock import MagicMock, patch

import pytest
from rest_framework import status
from rest_framework.test import APIRequestFactory

from tmdb.views import DiscoverMoviesView, MovieDetailsView, SearchMoviesView


@pytest.fixture
def api_factory():
    return APIRequestFactory()


def _resp(status_code: int, payload: dict):
    r = MagicMock()
    r.status_code = status_code
    r.json.return_value = payload
    return r


@pytest.mark.django_db
class TestDiscoverMoviesView:
    @patch("tmdb.views.TMDBClient")
    def test_discover_movies_without_account_id(self, mock_client, api_factory):
        mock_tmdb = MagicMock()
        mock_tmdb.discover_movies.return_value = {
            "page": 1,
            "results": [{"id": 100, "title": "Movie A"}],
            "total_pages": 1,
            "total_results": 1,
        }
        mock_client.return_value = mock_tmdb

        request = api_factory.get("/api/v1/movies/discover/")
        view = DiscoverMoviesView.as_view()

        resp = view(request)
        assert resp.status_code == status.HTTP_200_OK
        assert "results" in resp.data
        assert resp.data["results"][0]["favorite"] is False
        mock_tmdb.discover_movies.assert_called_once()

    @patch("tmdb.views.requests.get")
    @patch("tmdb.views.TMDBClient")
    def test_discover_movies_with_account_id_marks_favorites(
        self, mock_client, mock_requests_get, api_factory
    ):
        account_id = 42

        mock_tmdb = MagicMock()
        mock_tmdb.session.headers = {"Authorization": "Bearer test-token"}
        mock_tmdb.discover_movies.return_value = {
            "page": 1,
            "results": [
                {"id": 200, "title": "Favorite Movie"},
                {"id": 300, "title": "Non-favorite Movie"},
            ],
            "total_pages": 1,
            "total_results": 2,
        }
        mock_client.return_value = mock_tmdb

        mock_requests_get.return_value = _resp(
            200,
            {
                "page": 1,
                "results": [{"id": 200}],
                "total_pages": 1,
                "total_results": 1,
            },
        )

        request = api_factory.get(
            f"/api/v1/movies/discover/?account_id={account_id}",
            HTTP_AUTHORIZATION="Bearer test-token",
        )
        view = DiscoverMoviesView.as_view()

        resp = view(request)
        assert resp.status_code == status.HTTP_200_OK
        results = resp.data["results"]

        fav_movie = next(m for m in results if m["id"] == 200)
        non_fav_movie = next(m for m in results if m["id"] == 300)
        assert fav_movie["favorite"] is True
        assert non_fav_movie["favorite"] is False

    @patch("tmdb.views.TMDBClient")
    def test_discover_movies_empty_results(self, mock_client, api_factory):
        mock_tmdb = MagicMock()
        mock_tmdb.discover_movies.return_value = {"page": 1, "results": [], "total_pages": 1, "total_results": 0}
        mock_client.return_value = mock_tmdb

        request = api_factory.get("/api/v1/movies/discover/")
        view = DiscoverMoviesView.as_view()

        resp = view(request)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["results"] == []


@pytest.mark.django_db
class TestSearchMoviesView:
    @patch("tmdb.views.requests.get")
    def test_search_movies_by_title_without_account_id(self, mock_requests_get, api_factory):
        mock_requests_get.return_value = _resp(
            200,
            {
                "page": 1,
                "results": [{"id": 10, "title": "Inception"}],
                "total_pages": 1,
                "total_results": 1,
            },
        )

        request = api_factory.get(
            "/api/v1/movies/search/?query=Inception",
            HTTP_AUTHORIZATION="Bearer test-token",
        )
        view = SearchMoviesView.as_view()

        resp = view(request)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["results"][0]["favorite"] is False

    @patch("tmdb.views.requests.get")
    def test_search_movies_marks_favorites_with_account_id(self, mock_requests_get, api_factory):
        # 1st call -> search payload; 2nd call -> favorites list
        mock_requests_get.side_effect = [
            _resp(
                200,
                {
                    "page": 1,
                    "results": [{"id": 11, "title": "Matrix"}, {"id": 22, "title": "Avatar"}],
                    "total_pages": 1,
                    "total_results": 2,
                },
            ),
            _resp(
                200,
                {
                    "page": 1,
                    "results": [{"id": 22}],
                    "total_pages": 1,
                    "total_results": 1,
                },
            ),
        ]

        request = api_factory.get(
            "/api/v1/movies/search/?query=ava&account_id=7",
            HTTP_AUTHORIZATION="Bearer bearer",
        )
        view = SearchMoviesView.as_view()
        resp = view(request)

        assert resp.status_code == status.HTTP_200_OK
        res = {m["id"]: m["favorite"] for m in resp.data["results"]}
        assert res[11] is False
        assert res[22] is True

    def test_search_requires_query_param(self, api_factory):
        request = api_factory.get("/api/v1/movies/search/")
        view = SearchMoviesView.as_view()
        resp = view(request)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "query" in resp.data.get("error", "").lower()


@pytest.mark.django_db
class TestMovieDetailsView:
    @patch("tmdb.views.TMDBClient")
    def test_movie_details_success(self, mock_client, api_factory):
        mock_tmdb = MagicMock()
        mock_tmdb.movie_details.return_value = {
            "id": 500,
            "title": "Interstellar",
            "overview": "A space exploration film.",
        }
        mock_client.return_value = mock_tmdb

        request = api_factory.get("/api/v1/movies/500/")
        view = MovieDetailsView.as_view()

        resp = view(request, tmdb_id=500)

        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["title"] == "Interstellar"
        mock_tmdb.movie_details.assert_called_once_with(500)
