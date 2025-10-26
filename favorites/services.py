from typing import Dict

from .models import Favorite, Profile


def ensure_profile(session) -> Profile:
    if not session.session_key:
        session.create()
    profile, _ = Profile.objects.get_or_create(session_key=session.session_key)
    return profile


def add_favorite(owner: Profile, payload: Dict) -> Favorite:
    fav, _ = Favorite.objects.get_or_create(
        owner=owner,
        tmdb_id=payload["tmdb_id"],
        defaults={
            "title": payload.get("title", ""),
            "poster_path": payload.get("poster_path", ""),
            "vote_average": payload.get("vote_average"),
        },
    )
    return fav
