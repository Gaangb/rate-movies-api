from typing import Any

import requests
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from favorites.models import FavoritedList, FavoritedMovie
from favorites.serializers import FavoritedListSerializer, FavoritedMovieSerializer
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

TMDB_BASE_URL = "https://api.themoviedb.org/3"


class BaseTMDBView(APIView): #TODO -  reuse
    def initialize_request(self, request: Request, *args: Any, **kwargs: Any) -> Request:
        req = super().initialize_request(request=request, *args, **kwargs)
        auth_header = req.headers.get("Authorization")
        self.tmdb_headers = (
            {
                "Authorization": auth_header,
                "Accept": "application/json",
                "Content-Type": "application/json;charset=utf-8",
            }
            if auth_header
            else {}
        )
        return req


class FavoritesView(BaseTMDBView):
    @extend_schema(
        tags=["Favorites"],
        summary="List favorite movies",
        description="Returns favorite movies for a TMDb account. Requires Authorization header.",
        parameters=[
            OpenApiParameter(
                name="account_id",
                description="TMDb account ID",
                required=True,
                type=int,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="page",
                description="Page number (default=1)",
                required=False,
                type=int,
                location=OpenApiParameter.QUERY,
            ),
        ],
        responses={200: OpenApiResponse(description="Favorites listed successfully")},
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        account_id = request.query_params.get("account_id")
        page = request.query_params.get("page", 1)

        if not account_id:
            return Response({"error": "'account_id' is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not self.tmdb_headers:
            return Response({"error": "Missing TMDb Authorization token."}, status=status.HTTP_401_UNAUTHORIZED)

        resp = requests.get(
            f"{TMDB_BASE_URL}/account/{account_id}/favorite/movies",
            params={"language": "en-US", "page": page, "sort_by": "created_at.asc"},
            headers=self.tmdb_headers,
        )
        return Response(resp.json(), status=resp.status_code)

    @extend_schema(
        tags=["Favorites"],
        summary="Favorite or unfavorite a movie",
        description="Syncs favorite state with TMDb and persists local copy when favoriting.",
        request=FavoritedMovieSerializer,
        responses={200: OpenApiResponse(description="Synchronized successfully")},
    )
    def post(self, request: Request) -> Response:
        serializer = FavoritedMovieSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        account_id = data["account_id"]
        movie_id = data["movie_id"]
        favorite = request.data.get("favorite", True)
        media_type = request.data.get("media_type", "movie")

        if not self.tmdb_headers:
            return Response({"error": "Missing TMDb Authorization token."}, status=status.HTTP_401_UNAUTHORIZED)

        payload = {"media_type": media_type, "media_id": movie_id, "favorite": favorite}
        tmdb_resp = requests.post(
            f"{TMDB_BASE_URL}/account/{account_id}/favorite",
            headers=self.tmdb_headers,
            json=payload,
        )

        if favorite:
            FavoritedMovie.objects.update_or_create(
                account_id=account_id,
                movie_id=movie_id,
                defaults={
                    "title": data.get("title", ""),
                    "overview": data.get("overview"),
                    "poster_path": data.get("poster_path"),
                    "release_date": data.get("release_date"),
                    "genre_ids": data.get("genre_ids", []),
                    "vote_average": data.get("vote_average", 0.0),
                },
            )
        else:
            FavoritedMovie.objects.filter(account_id=account_id, movie_id=movie_id).delete()

        return Response(tmdb_resp.json(), status=tmdb_resp.status_code)


class ShareFavoritedListView(APIView):
    @extend_schema(
        tags=["Favorites"],
        summary="Create shareable favorites list",
        description="Creates a shareable list containing the provided movie IDs that are currently favorited by the account.",
        request={
            "application/json": {
                "example": {
                    "account_id": 1234567,
                    "list_name": "October favorites",
                    "movie_ids": [1156594, 872585, 502356],
                }
            }
        },
        responses={201: OpenApiResponse(response=FavoritedListSerializer)},
    )
    def post(self, request: Request) -> Response:
        account_id = request.data.get("account_id")
        list_name = request.data.get("list_name")
        movie_ids = request.data.get("movie_ids", [])

        if not account_id or not list_name:
            return Response({"error": "account_id and list_name are required."}, status=status.HTTP_400_BAD_REQUEST)
        if not isinstance(movie_ids, list) or not all(isinstance(m, int) for m in movie_ids):
            return Response({"error": "movie_ids must be a list of integers."}, status=status.HTTP_400_BAD_REQUEST)
        if not movie_ids:
            return Response({"error": "movie_ids cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)

        valid_ids = list(
            FavoritedMovie.objects.filter(account_id=account_id, movie_id__in=movie_ids).values_list("movie_id", flat=True)
        )
        if not valid_ids:
            return Response(
                {"error": "None of the provided movie_ids are favorited for this account_id."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        fav_list, _ = FavoritedList.objects.update_or_create(
            account_id=account_id, list_name=list_name, defaults={"movie_ids": valid_ids}
        )
        return Response(FavoritedListSerializer(fav_list).data, status=status.HTTP_201_CREATED)


class GetSharedFavoritedListView(APIView):
    @extend_schema(
        tags=["Favorites"],
        summary="Get shared favorites by list name",
        description="Returns movies belonging to the most recent shared list identified by list_name.",
        responses={200: OpenApiResponse(response=FavoritedMovieSerializer(many=True))},
    )
    def get(self, request: Request, list_name: str) -> Response:
        try:
            fav_list = FavoritedList.objects.filter(list_name__iexact=list_name).latest("created_at")
        except FavoritedList.DoesNotExist:
            return Response({"error": "No shared list found with this name."}, status=status.HTTP_404_NOT_FOUND)

        movies = FavoritedMovie.objects.filter(
            account_id=fav_list.account_id,
            movie_id__in=fav_list.movie_ids,
        )
        return Response(FavoritedMovieSerializer(movies, many=True).data, status=status.HTTP_200_OK)
