from typing import Any

import requests
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from favorites.models import FavoritedList
from favorites.serializers import FavoritedListSerializer, FavoritedMovieSerializer
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

TMDB_BASE_URL = "https://api.themoviedb.org/3"


class BaseTMDBView(APIView):
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
        parameters=[
            OpenApiParameter(name="account_id", type=int, location=OpenApiParameter.QUERY, required=True),
            OpenApiParameter(name="page", type=int, location=OpenApiParameter.QUERY, required=False),
        ],
        responses={200: OpenApiResponse(description="OK")},
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        account_id = request.query_params.get("account_id")
        page = request.query_params.get("page", 1)
        if not account_id:
            return Response({"error": "'account_id' is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not self.tmdb_headers:
            return Response({"error": "Missing TMDb Authorization token."}, status=status.HTTP_401_UNAUTHORIZED)

        r = requests.get(
            f"{TMDB_BASE_URL}/account/{account_id}/favorite/movies",
            params={"language": "en-US", "page": page, "sort_by": "created_at.asc"},
            headers=self.tmdb_headers,
            timeout=10,
        )

        data = r.json()
        list_name = (
            FavoritedList.objects
            .filter(account_id=account_id)
            .order_by("-created_at")
            .values_list("list_name", flat=True)
            .first()
        )
        if isinstance(data, dict):
            data["list_name"] = list_name if list_name is not None else None

        return Response(data, status=r.status_code)

    @extend_schema(
        tags=["Favorites"],
        summary="Favorite or unfavorite a movie",
        request=FavoritedMovieSerializer,
        responses={200: OpenApiResponse(description="OK")},
    )
    def post(self, request: Request) -> Response:
        ser = FavoritedMovieSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        account_id = data["account_id"]
        movie_id = data["movie_id"]
        favorite = request.data.get("favorite", True)
        media_type = request.data.get("media_type", "movie")

        if not self.tmdb_headers:
            return Response({"error": "Missing TMDb Authorization token."}, status=status.HTTP_401_UNAUTHORIZED)

        payload = {"media_type": media_type, "media_id": movie_id, "favorite": favorite}
        r = requests.post(
            f"{TMDB_BASE_URL}/account/{account_id}/favorite",
            headers=self.tmdb_headers,
            json=payload,
            timeout=10,
        )

        return Response(r.json(), status=r.status_code)


class ShareFavoritedListView(BaseTMDBView):
    @extend_schema(
        tags=["Favorites"],
        summary="Create or update shareable favorites list (stores only name and account)",
        request={"application/json": {"example": {"account_id": 1234567, "list_name": "October favorites"}}},
        responses={200: OpenApiResponse(response=FavoritedListSerializer)},
    )
    def post(self, request: Request) -> Response:
        account_id = request.data.get("account_id")
        list_name = request.data.get("list_name")
        if not account_id or not list_name:
            return Response({"error": "account_id and list_name are required."}, status=status.HTTP_400_BAD_REQUEST)

        obj = FavoritedList.objects.filter(account_id=account_id).order_by("-created_at").first()
        if obj:
            obj.list_name = list_name
            obj.save(update_fields=["list_name"])
            status_code = status.HTTP_200_OK
        else:
            obj = FavoritedList.objects.create(account_id=account_id, list_name=list_name)
            status_code = status.HTTP_201_CREATED

        return Response(FavoritedListSerializer(obj).data, status=status_code)


class GetSharedFavoritedListView(BaseTMDBView):
    def _fetch_tmdb_favorites_all(self, account_id: int | str) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        page = 1
        while True:
            r = requests.get(
                f"{TMDB_BASE_URL}/account/{account_id}/favorite/movies",
                params={"language": "en-US", "page": page, "sort_by": "created_at.asc"},
                headers=self.tmdb_headers,
                timeout=10,
            )
            if r.status_code >= 400:
                return []
            payload = r.json()
            items.extend(payload.get("results", []))
            total_pages = payload.get("total_pages") or 1
            if page >= total_pages:
                break
            page += 1
        return items

    @extend_schema(
        tags=["Favorites"],
        summary="Get shared favorites by list name (live from TMDb)",
        responses={200: OpenApiResponse(response=FavoritedMovieSerializer(many=True))},
    )
    def get(self, request: Request, list_name: str) -> Response:
        try:
            fav_list = FavoritedList.objects.filter(list_name__iexact=list_name).latest("created_at")
        except FavoritedList.DoesNotExist:
            return Response({"error": "No shared list found with this name."}, status=status.HTTP_404_NOT_FOUND)
        if not self.tmdb_headers:
            return Response({"error": "Missing TMDb Authorization token."}, status=status.HTTP_401_UNAUTHORIZED)

        results = self._fetch_tmdb_favorites_all(fav_list.account_id)
        mapped = [
            {
                "account_id": fav_list.account_id,
                "movie_id": m.get("id"),
                "title": m.get("title") or "",
                "overview": m.get("overview"),
                "poster_path": m.get("poster_path"),
                "release_date": m.get("release_date"),
                "genre_ids": m.get("genre_ids") or [],
                "vote_average": m.get("vote_average") or 0.0,
                "created_at": None,
            }
            for m in results
            if isinstance(m.get("id"), int)
        ]
        out = FavoritedMovieSerializer(data=mapped, many=True)
        out.is_valid(raise_exception=False)
        return Response(out.data, status=status.HTTP_200_OK)
