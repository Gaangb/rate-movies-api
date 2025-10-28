from enum import StrEnum

from django.conf import settings

TMDB_API_BASE: str = getattr(settings, "TMDB_API_BASE", "https://api.themoviedb.org/3")
TMDB_IMAGE_BASE: str = getattr(
    settings, "TMDB_IMAGE_BASE", "https://image.tmdb.org/t/p/"
)
TMDB_DEFAULT_LANG: str = getattr(settings, "TMDB_DEFAULT_LANG", "en-US")
TMDB_REQUEST_TIMEOUT: int = int(getattr(settings, "TMDB_REQUEST_TIMEOUT", 10))


class TMDBPaths:
    ACCOUNT_FAVORITES = "/account/{account_id}/favorite/movies"
    ACCOUNT_FAVORITE_TOGGLE = "/account/{account_id}/favorite"
    MOVIE_DISCOVER = "/discover/movie"
    MOVIE_DETAILS = "/movie/{tmdb_id}"
    MOVIE_VIDEOS = "/movie/{tmdb_id}/videos"
    MOVIE_PROVIDERS = "/movie/{tmdb_id}/watch/providers"
    MOVIE_CREDITS = "/movie/{tmdb_id}/credits"
    SEARCH_MOVIE = "/search/movie"


class Headers:
    AUTHORIZATION = "Authorization"
    ACCEPT = "Accept"
    CONTENT_TYPE = "Content-Type"
    JSON_CT = "application/json"
    JSON_UTF8 = "application/json;charset=utf-8"


class QueryParams:
    LANGUAGE = "language"
    PAGE = "page"
    SORT_BY = "sort_by"
    INCLUDE_ADULT = "include_adult"
    INCLUDE_VIDEO = "include_video"
    QUERY = "query"


class SortBy(StrEnum):
    POPULARITY_DESC = "popularity.desc"
    RELEASE_DATE_DESC = "release_date.desc"
    VOTE_AVERAGE_DESC = "vote_average.desc"
    CREATED_AT_ASC = "created_at.asc"


class ImageSize(StrEnum):
    W92 = "w92"
    W154 = "w154"
    W185 = "w185"
    W342 = "w342"
    W500 = "w500"
    W780 = "w780"
    ORIGINAL = "original"


class Docs:
    class Tags:
        MOVIES = "Movies"
        FAVORITES = "Favorites"

    class Summaries:
        DISCOVER = "Discover movies"
        SEARCH = "Search movies by title"
        DETAILS = "Get movie details"

        FAV_LIST = "List favorite movies"
        FAV_POST = "Favorite or unfavorite a movie"
        FAV_SHARE = (
            "Create or update shareable favorites list (stores only name and account)"
        )
        FAV_SHARED_GET = "Get shared favorites by list name (live from TMDb)"

    class Descriptions:
        DISCOVER = (
            "Returns a paginated list from TMDb based on filters and marks TMDb "
            "favorites for the given account_id."
        )
        SEARCH = (
            "Searches TMDb by movie title and flags favorites for the given account_id."
        )
        DETAILS = "Returns detailed information including videos, providers in Brazil, and credits."

        FAV_LIST = "Returns favorite movies from TMDb and appends the latest saved list_name (if any)."
        FAV_POST = "Toggles favorite on TMDb for the given account_id and movie_id."
        FAV_SHARE = (
            "Creates or updates a share record storing only {account_id, list_name}. "
            "If the same account shares again, the list_name is updated."
        )
        FAV_SHARED_GET = "Resolves account_id by list_name, then fetches live favorites from TMDb for that account."


class Errors:
    BAD_REQUEST = "Bad request."
    UNAUTHORIZED = "Missing TMDb Authorization token."
    FORBIDDEN = "Forbidden."
    NOT_FOUND = "Resource not found."
    CONFLICT = "Conflict."

    ACCOUNT_ID_REQUIRED = "'account_id' is required."
    LIST_NAME_REQUIRED = "'list_name' is required."
    ACCOUNT_AND_LIST_REQUIRED = "account_id and list_name are required."
    LIST_NAME_IN_USE = "This list_name is already in use."
    SHARED_LIST_NOT_FOUND = "No shared list found with this name."

    QUERY_REQUIRED = "'query' is required."

    TMDB_UPSTREAM_ERROR = "Upstream TMDb error."


API_DEFAULT_LANG = TMDB_DEFAULT_LANG
