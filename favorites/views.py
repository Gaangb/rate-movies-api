from typing import Any

import requests
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from favorites.models import FavoritedMovie

TMDB_BASE_URL = "https://api.themoviedb.org/3"


class BaseTMDBView(APIView):
    """
    Base view que injeta automaticamente o token TMDb do header Authorization.
    """

    def initialize_request(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Request:
        req = super().initialize_request(request=request, *args, **kwargs)
        auth_header = req.headers.get("Authorization")

        if not auth_header:
            self.tmdb_headers = {}
        else:
            self.tmdb_headers = {
                "Authorization": auth_header,
                "Accept": "application/json",
                "Content-Type": "application/json;charset=utf-8",
            }

        return req


class FavoritesView(BaseTMDBView):
    """
    Lista, adiciona ou remove filmes favoritados da conta TMDb autenticada.
    """

    @extend_schema(
        tags=["Favorites"],
        summary="Listar filmes favoritados",
        description="Retorna todos os filmes favoritados de uma conta TMDB específica. "
        "O token de autenticação deve ser enviado via header Authorization.",
        parameters=[
            OpenApiParameter(
                name="account_id",
                description="ID da conta TMDB",
                required=True,
                type=int,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="page",
                description="Número da página (opcional, padrão=1)",
                required=False,
                type=int,
                location=OpenApiParameter.QUERY,
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="Lista de filmes favoritados obtida com sucesso"
            )
        },
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Listar favoritos"""
        account_id = request.query_params.get("account_id")
        page = request.query_params.get("page", 1)

        if not account_id:
            return Response(
                {"error": "O parâmetro 'account_id' é obrigatório."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not self.tmdb_headers:
            return Response(
                {"error": "Token de autenticação TMDb não fornecido."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        resp = requests.get(
            f"{TMDB_BASE_URL}/account/{account_id}/favorite/movies",
            params={"language": "en-US", "page": page, "sort_by": "created_at.asc"},
            headers=self.tmdb_headers,
        )
        return Response(resp.json(), status=resp.status_code)

    @extend_schema(
        tags=["Favorites"],
        summary="Favoritar ou desfavoritar filme",
        description="Adiciona ou remove um filme dos favoritos da conta TMDb e sincroniza com o banco local.",
        request={
            "application/json": {
                "example": {
                    "account_id": 1234567,
                    "movie_id": 1156594,
                    "favorite": True,
                    "media_type": "movie",
                }
            }
        },
        responses={200: OpenApiResponse(description="Sincronizado com sucesso")},
    )
    def post(self, request: Request) -> Response:
        account_id = request.data.get("account_id")
        movie_id = request.data.get("movie_id")
        favorite = request.data.get("favorite", True)
        media_type = request.data.get("media_type", "movie")

        if not account_id or not movie_id:
            return Response(
                {"error": "account_id e movie_id são obrigatórios"}, status=400
            )

        if not self.tmdb_headers:
            return Response(
                {"error": "Token de autenticação TMDb não fornecido."}, status=401
            )

        # Envia para o TMDb
        tmdb_payload = {
            "media_type": media_type,
            "media_id": movie_id,
            "favorite": favorite,
        }
        tmdb_resp = requests.post(
            f"{TMDB_BASE_URL}/account/{account_id}/favorite",
            headers=self.tmdb_headers,
            json=tmdb_payload,
        )

        # Atualiza banco local
        if favorite:
            FavoritedMovie.objects.get_or_create(
                account_id=account_id, movie_id=movie_id
            )
        else:
            FavoritedMovie.objects.filter(
                account_id=account_id, movie_id=movie_id
            ).delete()

        return Response(tmdb_resp.json(), status=tmdb_resp.status_code)
