from django.urls import path

from .views import (
    DiscoverMoviesView,
    MovieDetailsView,
)

urlpatterns = [
    path("discover/", DiscoverMoviesView.as_view(), name="discover-movies"),
    path("movies/<int:tmdb_id>/", MovieDetailsView.as_view(), name="movie-details"),
]
