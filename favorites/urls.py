from django.urls import path

from favorites.views import FavoritesView, GetSharedFavoritedListView, ShareFavoritedListView

urlpatterns = [
    path("favorites/", FavoritesView.as_view(), name="favorites"),
    path("share-list/", ShareFavoritedListView.as_view(), name="share-list"),
    path("get-shared-list/<str:list_name>/", GetSharedFavoritedListView.as_view(), name="get-shared-list"),
]
