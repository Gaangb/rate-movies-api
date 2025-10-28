from rest_framework import serializers

from favorites.models import FavoritedList


class FavoritedMovieSerializer(serializers.Serializer):
    account_id = serializers.IntegerField()
    movie_id = serializers.IntegerField()

    favorite = serializers.BooleanField(required=False, default=True)
    midia_type = serializers.CharField(required=False, default="movie", max_length=20)

    title = serializers.CharField(required=False, allow_blank=True, default="")
    overview = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    poster_path = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    release_date = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    genre_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list
    )
    vote_average = serializers.FloatField(required=False, default=0.0)

    created_at = serializers.DateTimeField(required=False, allow_null=True)


class FavoritedListSerializer(serializers.ModelSerializer):
    movie_ids = serializers.ListField(child=serializers.IntegerField(), required=False)

    class Meta:
        model = FavoritedList
        fields = ["account_id", "list_name", "movie_ids", "created_at"]
