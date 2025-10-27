from typing import Any, cast

from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from favorites.models import FavoritedMovie
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from tmdb.client import TMDBClient
from tmdb.serializers import DiscoverQueryParamsSerializer, MovieDetailsSerializer, MovieDiscoverListSerializer


class BaseTMDBView(APIView):
    def initialize_request(self, request, *args, **kwargs):
        req = super().initialize_request(request, *args, **kwargs)
        auth_header = req.headers.get("Authorization")
        self.tmdb_client = TMDBClient(bearer_token=auth_header)
        return req


class DiscoverMoviesView(BaseTMDBView):
    serializer_class = MovieDiscoverListSerializer

    @extend_schema(
        tags=["Movies"],
        summary="Discover movies",
        description="Returns a paginated list from TMDb based on filters and marks local favorites for the given account_id.",
        parameters=[
            DiscoverQueryParamsSerializer,
            OpenApiParameter(
                name="account_id",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Account ID used to flag movies already favorited locally.",
                required=False,
            ),
        ],
        responses={200: OpenApiResponse(response=MovieDiscoverListSerializer)},
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        query_serializer = cast(DiscoverQueryParamsSerializer, DiscoverQueryParamsSerializer(data=request.query_params))
        query_serializer.is_valid(raise_exception=True)
        validated: dict[str, Any] = query_serializer.validated_data
        params: dict[str, str | int | bool] = {k: v for k, v in validated.items()}

        data: dict[str, Any] = self.tmdb_client.discover_movies(params=params)
        results = data.get("results", [])
        for movie in results:
            movie["favorite"] = False

        account_id = request.query_params.get("account_id")
        if account_id:
            favorite_ids = set(
                FavoritedMovie.objects.filter(account_id=account_id).values_list("movie_id", flat=True)
            )
            for movie in results:
                if movie.get("id") in favorite_ids:
                    movie["favorite"] = True

        out = self.serializer_class(data=data)
        out.is_valid(raise_exception=False)
        return Response(out.data, status=status.HTTP_200_OK)


class MovieDetailsView(BaseTMDBView):
    serializer_class = MovieDetailsSerializer

    @extend_schema(
        tags=["Movies"],
        summary="Get movie details",
        description="Returns detailed information including videos, providers in Brazil, and credits.",
        parameters=[
            OpenApiParameter(
                name="tmdb_id",
                type=int,
                location=OpenApiParameter.PATH,
                description="TMDb movie ID",
                required=True,
            ),
        ],
        responses={
            200: OpenApiResponse(response=MovieDetailsSerializer, description="Movie details."),
            404: OpenApiResponse(description="Movie not found."),
        },
    )
    def get(self, request: Request, tmdb_id: int, *args: Any, **kwargs: Any) -> Response:
        data: dict[str, Any] = self.tmdb_client.movie_details(tmdb_id)
        return Response(data, status=status.HTTP_200_OK)
