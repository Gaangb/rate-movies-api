from rest_framework import serializers

from favorites.models import FavoritedList, FavoritedMovie


class FavoritedMovieSerializer(serializers.Serializer):
    account_id = serializers.IntegerField()
    movie_id = serializers.IntegerField()
    favorite = serializers.BooleanField(required=False, default=True)
    midia_type = serializers.CharField(required=False, default="movie", max_length=20)


class FavoritedListSerializer(serializers.ModelSerializer):
    movie_ids = serializers.ListField(child=serializers.IntegerField(), required=False)

    class Meta:
        model = FavoritedList
        fields = ["account_id", "list_name", "movie_ids", "created_at"]