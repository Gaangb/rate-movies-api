from favorites.serializers import FavoritedMovieSerializer


def test_favorited_movie_serializer_requires_fields():
    ser = FavoritedMovieSerializer(data={})
    assert not ser.is_valid()
    assert "account_id" in ser.errors
    assert "movie_id" in ser.errors


def test_favorited_movie_serializer_defaults_and_types():
    payload = {"account_id": 1, "movie_id": 10}
    ser = FavoritedMovieSerializer(data=payload)
    assert ser.is_valid(), ser.errors
    data = ser.validated_data
    assert data["account_id"] == 1
    assert data["movie_id"] == 10
    assert data.get("favorite", True) is True
    assert data.get("media_type", "movie") == "movie"


def test_favorited_movie_serializer_accepts_mapped_readonly_fields():
    payload = {
        "account_id": 7,
        "movie_id": 22,
        "title": "Avatar",
        "overview": "Plot...",
        "poster_path": "/x.png",
        "release_date": "2009-12-18",
        "genre_ids": [28, 12],
        "vote_average": 7.8,
        "created_at": None,
    }
    ser = FavoritedMovieSerializer(data=payload)
    assert ser.is_valid(), ser.errors
    data = ser.validated_data
    assert data["account_id"] == 7
    assert data["movie_id"] == 22
    assert data.get("genre_ids") == [28, 12]
    assert data.get("vote_average") == 7.8


def test_favorited_movie_serializer_many_mode():
    items = [
        {"account_id": 1, "movie_id": 100},
        {"account_id": 1, "movie_id": 200, "favorite": False},
    ]
    ser = FavoritedMovieSerializer(data=items, many=True)
    assert ser.is_valid(), ser.errors
    out = ser.validated_data
    assert len(out) == 2
    assert out[0]["favorite"] is True
    assert out[1]["favorite"] is False
