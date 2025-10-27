from django.urls import path

from favorites.views import FavoritesView, GetSharedFavoriteListView, ShareFavoriteListView

urlpatterns = [
    path("favorites/", FavoritesView.as_view(), name="favorites"),
    path("share-list/", ShareFavoriteListView.as_view(), name="share-list"),
    path("get-shared-list/<str:list_name>/", GetSharedFavoriteListView.as_view(), name="get-shared-list"),
]
