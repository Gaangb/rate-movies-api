from typing import Any, cast
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from favorites.models import FavoritedMovie
from tmdb.client import TMDBClient
from tmdb.serializers import DiscoverQueryParamsSerializer, MovieDetailsSerializer, MovieDiscoverListSerializer

class BaseTMDBView(APIView): #TODO - reutilizar
    """
    Base view that provides a shared TMDB client instance.
    """

    def initialize_request(self, request, *args, **kwargs):
        req = super().initialize_request(request, *args, **kwargs)
        auth_header = req.headers.get("Authorization")
        self.tmdb_client = TMDBClient(bearer_token=auth_header)
        return req


class DiscoverMoviesView(BaseTMDBView):
    """
    Returns TMDb movie discovery results (cached and localized).
    """
    serializer_class = MovieDiscoverListSerializer

    @extend_schema(
        tags=["Movies"],
        summary="Discover movies",
        description="Fetches a paginated list of movies from TMDb based on filtering and sorting parameters, "
                    "and marks as favorite those stored locally for the given account_id.",
        parameters=[
            DiscoverQueryParamsSerializer,
            OpenApiParameter(
                name="account_id",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Account ID to check which movies are favorited locally.",
                required=False,
            ),
        ],
        responses={200: OpenApiResponse(response=MovieDiscoverListSerializer)},
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        # 1️⃣ Validar query params
        query_serializer = cast(
            DiscoverQueryParamsSerializer,
            DiscoverQueryParamsSerializer(data=request.query_params),
        )
        query_serializer.is_valid(raise_exception=True)
        validated: dict[str, Any] = query_serializer.validated_data
        params: dict[str, str | int | bool] = {k: v for k, v in validated.items()}

        # 2️⃣ Buscar filmes do TMDb
        data: dict[str, Any] = self.tmdb_client.discover_movies(params=params)

        # 3️⃣ Inicializar todos com favorite=False
        results = data.get("results", [])
        for movie in results:
            movie["favorite"] = False

        # 4️⃣ Se houver account_id, marcar favoritos locais
        account_id = request.query_params.get("account_id")
        if account_id:
            favorite_ids = set(
                FavoritedMovie.objects.filter(account_id=account_id)
                .values_list("movie_id", flat=True)
            )

            for movie in results:
                movie_id = movie.get("id")
                if movie_id in favorite_ids:
                    movie["favorite"] = True

        # 5️⃣ Serializar saída (mantém padrão)
        output_serializer = self.serializer_class(data=data)
        output_serializer.is_valid(raise_exception=False)

        return Response(output_serializer.data, status=status.HTTP_200_OK)


class MovieDetailsView(BaseTMDBView):
    """
    Returns detailed information for a specific movie.
    """
    serializer_class = MovieDetailsSerializer

    @extend_schema(
        tags=["Movies"],
        summary="Get detailed movie information",
        description=(
            "Retrieves detailed information for a specific movie from TMDb, "
            "including general metadata, trailers, and available streaming providers in Brazil."
        ),
        parameters=[
            OpenApiParameter(
                name="tmdb_id",
                type=int,
                location=OpenApiParameter.PATH,
                description="Unique TMDb movie identifier",
                required=True,
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=MovieDetailsSerializer,
                description="Detailed movie data, including trailers and streaming providers.",
            ),
            404: OpenApiResponse(description="Movie not found on TMDb."),
        },
    )
    def get(self, request: Request, tmdb_id: int, *args: Any, **kwargs: Any) -> Response:
        data: dict[str, Any] = self.tmdb_client.movie_details(tmdb_id)
        return Response(data, status=status.HTTP_200_OK)
