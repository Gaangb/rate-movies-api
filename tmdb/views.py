from typing import Any, cast

import requests
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from tmdb.client import TMDBClient
from tmdb.serializers import (
    DiscoverQueryParamsSerializer,
    MovieDetailsSerializer,
    MovieDiscoverListSerializer,
)


class BaseTMDBView(APIView):
    def initialize_request(self, request, *args, **kwargs):
        req = super().initialize_request(request, *args, **kwargs)
        auth_header = req.headers.get("Authorization")
        self.tmdb_client = TMDBClient(bearer_token=auth_header)
        return req


class DiscoverMoviesView(BaseTMDBView):
    serializer_class = MovieDiscoverListSerializer

    def _fetch_tmdb_favorite_ids(self, account_id: str | int) -> set[int]:
        auth = self.tmdb_client.session.headers.get("Authorization")
        if not auth:
            return set()

        base = "https://api.themoviedb.org/3"
        url = f"{base}/account/{account_id}/favorite/movies"
        page = 1
        ids: set[int] = set()

        while True:
            r = requests.get(
                url,
                params={"language": "en-US", "page": page, "sort_by": "created_at.asc"},
                headers={"Authorization": auth, "Accept": "application/json"},
                timeout=10,
            )
            if r.status_code >= 400:
                return set()
            payload = r.json()
            for m in payload.get("results", []):
                mid = m.get("id")
                if isinstance(mid, int):
                    ids.add(mid)
            total_pages = payload.get("total_pages") or 1
            if page >= total_pages:
                break
            page += 1

        return ids

    @extend_schema(
        tags=["Movies"],
        summary="Discover movies",
        description="Returns a paginated list from TMDb based on filters and marks TMDb favorites for the given account_id.",
        parameters=[
            DiscoverQueryParamsSerializer,
            OpenApiParameter(
                name="account_id",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Account ID used to flag movies favorited on TMDb.",
                required=False,
            ),
        ],
        responses={200: OpenApiResponse(response=MovieDiscoverListSerializer)},
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        query_serializer = cast(
            DiscoverQueryParamsSerializer, DiscoverQueryParamsSerializer(data=request.query_params)
        )
        query_serializer.is_valid(raise_exception=True)
        validated: dict[str, Any] = query_serializer.validated_data
        params: dict[str, str | int | bool] = {k: v for k, v in validated.items()}

        data: dict[str, Any] = self.tmdb_client.discover_movies(params=params)
        results = data.get("results", [])
        for movie in results:
            movie["favorite"] = False

        account_id = request.query_params.get("account_id")
        if account_id:
            fav_ids = self._fetch_tmdb_favorite_ids(account_id)
            if fav_ids:
                for movie in results:
                    if movie.get("id") in fav_ids:
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
