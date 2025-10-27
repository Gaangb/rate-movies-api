from django.urls import path

from tmdb.views import DiscoverMoviesView, MovieDetailsView, SearchMoviesView

urlpatterns = [
    path("discover/", DiscoverMoviesView.as_view(), name="discover-movies"),
    path("movies/search/", SearchMoviesView.as_view()),
    path("movies/<int:tmdb_id>/", MovieDetailsView.as_view(), name="movie-details"),
]
