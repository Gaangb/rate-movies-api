from rest_framework import serializers
from typing import Any, TypedDict

class DiscoverQueryParamsDict(TypedDict):
    language: str
    page: int
    include_adult: bool
    include_video: bool
    sort_by: str

class DiscoverQueryParamsSerializer(serializers.Serializer[DiscoverQueryParamsDict]):
    language = serializers.CharField(default="en-US")
    page = serializers.IntegerField(default=1, min_value=1)
    include_adult = serializers.BooleanField(default=False)
    include_video = serializers.BooleanField(default=False)
    sort_by = serializers.CharField(default="popularity.desc")


class MovieDiscoverResultSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    original_title = serializers.CharField()
    original_language = serializers.CharField()
    overview = serializers.CharField(allow_blank=True, allow_null=True)
    poster_path = serializers.CharField(allow_blank=True, allow_null=True)
    backdrop_path = serializers.CharField(allow_blank=True, allow_null=True)
    release_date = serializers.CharField(allow_blank=True, allow_null=True)
    genre_ids = serializers.ListField(child=serializers.IntegerField())
    adult = serializers.BooleanField()
    video = serializers.BooleanField()
    popularity = serializers.FloatField()
    vote_average = serializers.FloatField()
    vote_count = serializers.IntegerField()
    favorite = serializers.BooleanField()


class MovieDiscoverListSerializer(serializers.Serializer):
    page = serializers.IntegerField()
    results = MovieDiscoverResultSerializer(many=True)
    total_pages = serializers.IntegerField()
    total_results = serializers.IntegerField()


class VideoSerializer(serializers.Serializer):
    name = serializers.CharField()
    url = serializers.URLField()
    site = serializers.CharField()
    type = serializers.CharField()


class ProviderItemSerializer(serializers.Serializer):
    logo_path = serializers.CharField(allow_null=True, required=False)
    provider_id = serializers.IntegerField(required=False)
    provider_name = serializers.CharField()
    display_priority = serializers.IntegerField(required=False)


class ProviderSerializer(serializers.Serializer):
    link = serializers.URLField()
    flatrate = ProviderItemSerializer(many=True, required=False)


class MovieDetailsSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    overview = serializers.CharField(allow_blank=True, required=False)
    release_date = serializers.CharField(required=False)
    runtime = serializers.IntegerField(required=False, allow_null=True)
    vote_average = serializers.FloatField(required=False)
    vote_count = serializers.IntegerField(required=False)
    poster_path = serializers.CharField(allow_null=True, required=False)
    backdrop_path = serializers.CharField(allow_null=True, required=False)
    videos = VideoSerializer(many=True, required=False)
    providers = ProviderSerializer(required=False, allow_null=True)


class CreditSerializer(serializers.Serializer):
    name = serializers.CharField()
    profile_path = serializers.SerializerMethodField()
    character = serializers.CharField(allow_null=True, required=False)
    known_for_department = serializers.CharField()

    def get_profile_path(self, obj: dict[str, Any]) -> str | None:
        """
        Retorna a URL completa da imagem de perfil do ator/diretor.
        """
        path = obj.get("profile_path")
        if not path:
            return None
        return f"https://image.tmdb.org/t/p/w185{path}"