from typing import Any, cast

from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.constants import TMDB_DEFAULT_LANG, Docs, Errors, Headers, QueryParams
from tmdb.serializers import (
    DiscoverQueryParamsSerializer,
    MovieDetailsSerializer,
    MovieDiscoverListSerializer,
)
from tmdb.services import TMDBService


class BaseTMDBView(APIView):
    def initialize_request(self, request, *args, **kwargs):
        drf_request = super().initialize_request(request, *args, **kwargs)
        self.service = TMDBService(
            bearer_token=drf_request.headers.get(Headers.AUTHORIZATION)
        )
        return drf_request


class DiscoverMoviesView(BaseTMDBView):
    serializer_class = MovieDiscoverListSerializer

    @extend_schema(
        tags=[Docs.Tags.MOVIES],
        summary=Docs.Summaries.DISCOVER,
        description=Docs.Descriptions.DISCOVER,
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
        ser_in = cast(
            DiscoverQueryParamsSerializer,
            DiscoverQueryParamsSerializer(data=request.query_params),
        )
        ser_in.is_valid(raise_exception=True)
        params = dict(ser_in.validated_data)

        payload = self.service.discover(params)
        results = payload.get("results", [])
        for item in results:
            item["favorite"] = False

        account_id = request.query_params.get("account_id")
        if account_id:
            favorite_ids = self.service.fetch_favorite_ids(account_id)
            self.service.annotate_favorites(results, favorite_ids)

        ser_out = self.serializer_class(data=payload)
        ser_out.is_valid(raise_exception=False)
        return Response(ser_out.data, status=status.HTTP_200_OK)


class SearchMoviesView(BaseTMDBView):
    serializer_class = MovieDiscoverListSerializer

    @extend_schema(
        tags=[Docs.Tags.MOVIES],
        summary=Docs.Summaries.SEARCH,
        description=Docs.Descriptions.SEARCH,
        parameters=[
            OpenApiParameter(
                name=QueryParams.QUERY,
                type=str,
                location=OpenApiParameter.QUERY,
                description="Movie title to search",
                required=True,
            ),
            OpenApiParameter(
                name=QueryParams.PAGE,
                type=int,
                location=OpenApiParameter.QUERY,
                description="Page number (default=1)",
                required=False,
            ),
            OpenApiParameter(
                name=QueryParams.LANGUAGE,
                type=str,
                location=OpenApiParameter.QUERY,
                description=f"Locale (default={TMDB_DEFAULT_LANG})",
                required=False,
            ),
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
        query_text = request.query_params.get(QueryParams.QUERY)
        if not query_text:
            return Response(
                {"error": Errors.QUERY_REQUIRED}, status=status.HTTP_400_BAD_REQUEST
            )

        page = request.query_params.get(QueryParams.PAGE, 1)
        language = request.query_params.get(QueryParams.LANGUAGE, TMDB_DEFAULT_LANG)

        payload = self.service.search_movies(
            query=query_text, page=page, language=language
        )
        results = payload.get("results", [])
        for item in results:
            item["favorite"] = False

        account_id = request.query_params.get("account_id")
        if account_id:
            favorite_ids = self.service.fetch_favorite_ids(account_id)
            self.service.annotate_favorites(results, favorite_ids)

        ser_out = self.serializer_class(data=payload)
        ser_out.is_valid(raise_exception=False)
        return Response(ser_out.data, status=status.HTTP_200_OK)


class MovieDetailsView(BaseTMDBView):
    serializer_class = MovieDetailsSerializer

    @extend_schema(
        tags=[Docs.Tags.MOVIES],
        summary=Docs.Summaries.DETAILS,
        description=Docs.Descriptions.DETAILS,
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
            200: OpenApiResponse(
                response=MovieDetailsSerializer, description="Movie details."
            ),
            404: OpenApiResponse(description="Movie not found."),
        },
    )
    def get(
        self, request: Request, tmdb_id: int, *args: Any, **kwargs: Any
    ) -> Response:
        details = self.service.details(tmdb_id)
        return Response(details, status=status.HTTP_200_OK)
