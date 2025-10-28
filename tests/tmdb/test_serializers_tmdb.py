import pytest

from tmdb.serializers import DiscoverQueryParamsSerializer, MovieDiscoverListSerializer


def movie_item(id_: int, title: str, favorite: bool):
    return {
        "adult": False,
        "backdrop_path": "/b.jpg",
        "genre_ids": [28, 12],
        "id": id_,
        "original_language": "en",
        "original_title": title,
        "overview": "desc",
        "popularity": 123.4,
        "poster_path": "/p.jpg",
        "release_date": "2020-01-01",
        "title": title,
        "video": False,
        "vote_average": 7.8,
        "vote_count": 120,
        "favorite": favorite,
    }


@pytest.mark.parametrize(
    "payload,expected",
    [
        (
            {
                "language": "pt-BR",
                "page": "2",
                "include_adult": "false",
                "include_video": "false",
                "sort_by": "popularity.desc",
            },
            {
                "language": "pt-BR",
                "page": 2,
                "include_adult": False,
                "include_video": False,
                "sort_by": "popularity.desc",
            },
        ),
        ({"page": 1}, {"page": 1}),
    ],
)
def test_discover_query_params_serializer(payload, expected):
    ser = DiscoverQueryParamsSerializer(data=payload)
    assert ser.is_valid(), ser.errors
    for k, v in expected.items():
        assert ser.validated_data[k] == v


def test_movie_discover_list_serializer_accepts_structure():
    payload = {
        "page": 1,
        "results": [
            movie_item(1, "X", False),
            movie_item(2, "Y", True),
        ],
        "total_pages": 1,
        "total_results": 2,
    }
    ser = MovieDiscoverListSerializer(data=payload)
    assert ser.is_valid(), ser.errors
    data = ser.validated_data
    assert data["page"] == 1
    assert len(data["results"]) == 2
