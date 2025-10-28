from django.urls import path

from favorites.views import (
    FavoritesView,
    GetSharedFavoritedListView,
    ShareFavoritedListView,
)

urlpatterns = [
    path("favorites/", FavoritesView.as_view(), name="favorites"),
    path("share-favorites/", ShareFavoritedListView.as_view(), name="share-favorites"),
    path(
        "get-shared-favorites/",
        GetSharedFavoritedListView.as_view(),
        name="get-share-favorites",
    ),
]
