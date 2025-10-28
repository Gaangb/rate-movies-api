from unittest.mock import MagicMock, patch

import pytest
from rest_framework import status
from rest_framework.test import APIRequestFactory

from core.constants import TMDB_API_BASE, QueryParams, TMDBPaths
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
    @patch("tmdb.views.TMDBService")
    def test_discover_movies_without_account_id(self, mock_service_cls, api_factory):
        svc = MagicMock()
        svc.discover.return_value = {
            "page": 1,
            "results": [{"id": 100, "title": "Movie A"}],
            "total_pages": 1,
            "total_results": 1,
        }
        mock_service_cls.return_value = svc

        request = api_factory.get("/api/v1/movies/discover/")
        resp = DiscoverMoviesView.as_view()(request)

        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["results"][0]["favorite"] is False
        svc.discover.assert_called_once()

    @patch("tmdb.views.TMDBService")
    def test_discover_movies_with_account_id_marks_favorites(
        self, mock_service_cls, api_factory
    ):
        svc = MagicMock()
        svc.discover.return_value = {
            "page": 1,
            "results": [{"id": 200, "title": "Fav"}, {"id": 300, "title": "Other"}],
            "total_pages": 1,
            "total_results": 2,
        }
        svc.fetch_favorite_ids.return_value = {200}

        def _annotate(results, ids):
            for m in results:
                m["favorite"] = m.get("id") in ids

        svc.annotate_favorites.side_effect = _annotate
        mock_service_cls.return_value = svc

        req = api_factory.get(
            "/api/v1/movies/discover/?account_id=42", HTTP_AUTHORIZATION="Bearer x"
        )
        resp = DiscoverMoviesView.as_view()(req)

        assert resp.status_code == status.HTTP_200_OK
        by_id = {m["id"]: m["favorite"] for m in resp.data["results"]}
        assert by_id[200] is True
        assert by_id[300] is False

    @patch("tmdb.views.TMDBService")
    def test_discover_movies_empty_results(self, mock_service_cls, api_factory):
        svc = MagicMock()
        svc.discover.return_value = {
            "page": 1,
            "results": [],
            "total_pages": 1,
            "total_results": 0,
        }
        mock_service_cls.return_value = svc

        request = api_factory.get("/api/v1/movies/discover/")
        view = DiscoverMoviesView.as_view()

        resp = view(request)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["results"] == []


@pytest.mark.django_db
class TestSearchMoviesView:
    @patch("tmdb.services.requests.get")
    def test_search_movies_by_title_without_account_id(
        self, mock_requests_get, api_factory
    ):
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

    @patch("tmdb.services.requests.get")
    def test_search_movies_marks_favorites_with_account_id(
        self, mock_requests_get, api_factory
    ):
        search_url = f"{TMDB_API_BASE}{TMDBPaths.SEARCH_MOVIE}"
        fav_url = f"{TMDB_API_BASE}{TMDBPaths.ACCOUNT_FAVORITES.format(account_id=7)}"

        mock_requests_get.side_effect = [
            _resp(
                200,
                {
                    "page": 1,
                    "results": [
                        {"id": 11, "title": "Matrix"},
                        {"id": 22, "title": "Avatar"},
                    ],
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
            f"/api/v1/movies/search/?{QueryParams.QUERY}=ava&account_id=7",
            HTTP_AUTHORIZATION="Bearer bearer",
        )
        view = SearchMoviesView.as_view()
        resp = view(request)

        assert resp.status_code == status.HTTP_200_OK
        res = {m["id"]: m["favorite"] for m in resp.data["results"]}
        assert res[11] is False
        assert res[22] is True

        first_call_url = mock_requests_get.call_args_list[0].args[0]
        second_call_url = mock_requests_get.call_args_list[1].args[0]
        assert first_call_url == search_url
        assert second_call_url == fav_url

    def test_search_requires_query_param(self, api_factory):
        request = api_factory.get("/api/v1/movies/search/")
        view = SearchMoviesView.as_view()
        resp = view(request)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert QueryParams.QUERY.strip("'") in resp.data.get("error", "").lower()


@pytest.mark.django_db
class TestMovieDetailsView:
    @patch("tmdb.views.TMDBService")
    def test_movie_details_success(self, mock_service_cls, api_factory):
        svc = MagicMock()
        svc.details.return_value = {
            "id": 500,
            "title": "Interstellar",
            "overview": "A space exploration film.",
        }
        mock_service_cls.return_value = svc

        request = api_factory.get("/api/v1/movies/500/")
        view = MovieDetailsView.as_view()

        resp = view(request, tmdb_id=500)

        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["title"] == "Interstellar"
        svc.details.assert_called_once_with(500)
