from rest_framework import serializers
from .models import FavoritedMovie


class FavoritedMovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = FavoritedMovie
        fields = ["id", "account_id", "movie_id", "created_at"]
