from typing import Any

from django.db import IntegrityError
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.constants import Docs, Errors, Headers, QueryParams
from favorites.serializers import FavoritedListSerializer, FavoritedMovieSerializer
from favorites.services import FavoritesService, SharedListService


class BaseTMDBView(APIView):
    def initialize_request(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Request:
        drf_request = super().initialize_request(request=request, *args, **kwargs)
        auth_header = drf_request.headers.get(Headers.AUTHORIZATION)
        self.tmdb_headers = (
            {
                Headers.AUTHORIZATION: auth_header,
                Headers.ACCEPT: Headers.JSON_CT,
                Headers.CONTENT_TYPE: Headers.JSON_UTF8,
            }
            if auth_header
            else {}
        )
        return drf_request


class FavoritesView(BaseTMDBView):
    @extend_schema(
        tags=[Docs.Tags.FAVORITES],
        summary=Docs.Summaries.FAV_LIST,
        description=Docs.Descriptions.FAV_LIST,
        parameters=[
            OpenApiParameter(
                name="account_id",
                type=int,
                location=OpenApiParameter.QUERY,
                required=True,
            ),
            OpenApiParameter(
                name=QueryParams.PAGE,
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
            ),
        ],
        responses={200: OpenApiResponse(description="OK")},
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        account_id = request.query_params.get("account_id")
        page = request.query_params.get(QueryParams.PAGE, 1)
        if not account_id:
            return Response(
                {"error": Errors.ACCOUNT_ID_REQUIRED},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not self.tmdb_headers:
            return Response(
                {"error": Errors.UNAUTHORIZED}, status=status.HTTP_401_UNAUTHORIZED
            )

        service = FavoritesService(self.tmdb_headers)
        payload, status_code = service.list_tmdb_favorites(
            account_id=account_id, page=page
        )

        list_name = SharedListService.latest_name_for_account(account_id)
        if isinstance(payload, dict) and list_name:
            payload["list_name"] = list_name

        return Response(payload, status=status_code)

    @extend_schema(
        tags=[Docs.Tags.FAVORITES],
        summary=Docs.Summaries.FAV_POST,
        description=Docs.Descriptions.FAV_POST,
        request=FavoritedMovieSerializer,
        responses={200: OpenApiResponse(description="OK")},
    )
    def post(self, request: Request) -> Response:
        serializer = FavoritedMovieSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if not self.tmdb_headers:
            return Response(
                {"error": Errors.UNAUTHORIZED}, status=status.HTTP_401_UNAUTHORIZED
            )

        service = FavoritesService(self.tmdb_headers)
        payload, status_code = service.toggle_tmdb_favorite(
            account_id=data["account_id"],
            movie_id=data["movie_id"],
            favorite=request.data.get("favorite", True),
            media_type=request.data.get("media_type", "movie"),
        )
        return Response(payload, status=status_code)


class ShareFavoritedListView(BaseTMDBView):
    @extend_schema(
        tags=[Docs.Tags.FAVORITES],
        summary=Docs.Summaries.FAV_SHARE,
        description=Docs.Descriptions.FAV_SHARE,
        request={
            "application/json": {
                "example": {"account_id": 1234567, "list_name": "october"}
            }
        },
        responses={200: OpenApiResponse(response=FavoritedListSerializer)},
    )
    def post(self, request: Request) -> Response:
        account_id = request.data.get("account_id")
        list_name = (request.data.get("list_name") or "").strip()
        if not account_id or not list_name:
            return Response(
                {"error": Errors.ACCOUNT_AND_LIST_REQUIRED},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if SharedListService.is_name_in_use(list_name, exclude_account_id=account_id):
            return Response(
                {"error": Errors.LIST_NAME_IN_USE}, status=status.HTTP_409_CONFLICT
            )

        try:
            instance, created = SharedListService.upsert(
                account_id=account_id, list_name=list_name
            )
            return Response(
                FavoritedListSerializer(instance).data,
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
            )
        except IntegrityError:
            return Response(
                {"error": Errors.LIST_NAME_IN_USE}, status=status.HTTP_409_CONFLICT
            )


class GetSharedFavoritedListView(BaseTMDBView):
    @extend_schema(
        tags=[Docs.Tags.FAVORITES],
        summary=Docs.Summaries.FAV_SHARED_GET,
        description=Docs.Descriptions.FAV_SHARED_GET,
        parameters=[
            OpenApiParameter(
                name="list_name",
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
            )
        ],
        responses={200: OpenApiResponse(response=FavoritedMovieSerializer(many=True))},
    )
    def get(self, request: Request) -> Response:
        list_name = (request.query_params.get("list_name") or "").strip()
        if not list_name:
            return Response(
                {"error": Errors.LIST_NAME_REQUIRED}, status=status.HTTP_400_BAD_REQUEST
            )

        record = None
        try:
            from favorites.models import FavoritedList

            record = FavoritedList.objects.filter(list_name__iexact=list_name).latest(
                "created_at"
            )
        except FavoritedList.DoesNotExist:
            return Response(
                {"error": Errors.SHARED_LIST_NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not self.tmdb_headers:
            return Response(
                {"error": Errors.UNAUTHORIZED}, status=status.HTTP_401_UNAUTHORIZED
            )

        service = FavoritesService(self.tmdb_headers)
        tmdb_items = service.fetch_all_tmdb_favorites(account_id=record.account_id)

        mapped = [
            {
                "account_id": record.account_id,
                "movie_id": item.get("id"),
                "title": item.get("title") or "",
                "overview": item.get("overview"),
                "poster_path": item.get("poster_path"),
                "release_date": item.get("release_date"),
                "genre_ids": item.get("genre_ids") or [],
                "vote_average": item.get("vote_average") or 0.0,
                "created_at": None,
            }
            for item in tmdb_items
            if isinstance(item.get("id"), int)
        ]

        serializer = FavoritedMovieSerializer(data=mapped, many=True)
        serializer.is_valid(raise_exception=False)
        return Response(serializer.data, status=status.HTTP_200_OK)
