import pytest
from unittest.mock import patch, MagicMock
from rest_framework.test import APIRequestFactory
from rest_framework import status

from tmdb.views import DiscoverMoviesView, MovieDetailsView
from favorites.models import FavoritedMovie


@pytest.fixture
def api_factory():
    return APIRequestFactory()


@pytest.mark.django_db
class TestDiscoverMoviesView:
    @patch("tmdb.views.TMDBClient")
    def test_discover_movies_without_account_id(self, mock_client, api_factory):
        mock_instance = MagicMock()
        mock_instance.discover_movies.return_value = {
            "page": 1,
            "results": [{"id": 100, "title": "Movie A"}],
            "total_pages": 1,
            "total_results": 1,
        }
        mock_client.return_value = mock_instance

        request = api_factory.get("/api/v1/discover/")
        view = DiscoverMoviesView.as_view()

        response = view(request)
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
        assert response.data["results"][0]["favorite"] is False
        mock_instance.discover_movies.assert_called_once()

    @patch("tmdb.views.TMDBClient")
    def test_discover_movies_with_account_id_and_favorite(self, mock_client, api_factory, db):
        """Should mark favorite=True for movies present in the database for given account_id."""
        # Arrange: DB contains a favorite
        account_id = 42
        FavoritedMovie.objects.create(account_id=account_id, movie_id=200)

        # Mock TMDBClient
        mock_instance = MagicMock()
        mock_instance.discover_movies.return_value = {
            "page": 1,
            "results": [
                {"id": 200, "title": "Favorite Movie"},
                {"id": 300, "title": "Non-favorite Movie"},
            ],
            "total_pages": 1,
            "total_results": 2,
        }
        mock_client.return_value = mock_instance

        request = api_factory.get(f"/api/v1/discover/?account_id={account_id}")
        view = DiscoverMoviesView.as_view()

        response = view(request)

        assert response.status_code == status.HTTP_200_OK
        results = response.data["results"]

        fav_movie = next(m for m in results if m["id"] == 200)
        non_fav_movie = next(m for m in results if m["id"] == 300)
        assert fav_movie["favorite"] is True
        assert non_fav_movie["favorite"] is False

    @patch("tmdb.views.TMDBClient")
    def test_discover_movies_empty_results(self, mock_client, api_factory):
        mock_instance = MagicMock()
        mock_instance.discover_movies.return_value = {"page": 1, "results": []}
        mock_client.return_value = mock_instance

        request = api_factory.get("/api/v1/discover/")
        view = DiscoverMoviesView.as_view()

        response = view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == []


@pytest.mark.django_db
class TestMovieDetailsView:
    @patch("tmdb.views.TMDBClient")
    def test_movie_details_success(self, mock_client, api_factory):
        mock_instance = MagicMock()
        mock_instance.movie_details.return_value = {
            "id": 500,
            "title": "Interstellar",
            "overview": "A space exploration film."
        }
        mock_client.return_value = mock_instance

        request = api_factory.get("/api/v1/movies/500/")
        view = MovieDetailsView.as_view()

        response = view(request, tmdb_id=500)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Interstellar"
        mock_instance.movie_details.assert_called_once_with(500)
