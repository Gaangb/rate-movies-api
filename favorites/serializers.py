from rest_framework import serializers

from favorites.models import FavoriteList, FavoritedMovie


class FavoritedMovieSerializer(serializers.ModelSerializer):
    genre_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False
    )

    class Meta:
        model = FavoritedMovie
        fields = [
            "account_id",
            "movie_id",
            "title",
            "overview",
            "poster_path",
            "release_date",
            "genre_ids",
            "vote_average",
            "created_at",
        ]


class FavoriteListSerializer(serializers.ModelSerializer):
    movie_ids = serializers.ListField(child=serializers.IntegerField(), required=False)

    class Meta:
        model = FavoriteList
        fields = ["account_id", "list_name", "movie_ids", "created_at"]