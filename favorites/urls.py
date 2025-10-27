from django.urls import path

from favorites.views import FavoritesView

urlpatterns = [
    path("favorites/", FavoritesView.as_view(), name="favorites"),
]
