from typing import Any, Dict, Optional, Union

import requests
from django.conf import settings
from django.core.cache import cache


class TMDBClient:
    BASE = "https://api.themoviedb.org/3"
    IMAGE_BASE = "https://image.tmdb.org/t/p/"

    def __init__(self, bearer_token: Optional[str] = None, language: str = "pt-BR"):
        token = bearer_token or settings.TMDB_BEARER or ""
        self.language = language
        self.session = requests.Session()
        if token:
            self.session.headers.update({"Authorization": token})
        self.timeout = 10

    def _cached_request(
        self, path: str, params: Optional[dict[str, Union[str, int, bool]]]
    ) -> Dict[str, Any]:
        url = f"{self.BASE}{path}"
        key_params = params or {}
        cache_key = f"tmdb:{url}:{str(sorted(key_params.items()))}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        resp = self.session.get(url, params=key_params or None, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        cache.set(cache_key, data, timeout=600)
        return data

    def discover_movies(
        self, params: dict[str, Union[str, int, bool]]
    ) -> Dict[str, Any]:
        return self._cached_request("/discover/movie", params=params)

    def movie_details(self, tmdb_id: int) -> Dict[str, Any]:
        details = self._cached_request(f"/movie/{tmdb_id}", {"language": self.language})

        if details.get("poster_path"):
            details["poster_path"] = f"{self.IMAGE_BASE}w500{details['poster_path']}"
        if details.get("backdrop_path"):
            details["backdrop_path"] = (
                f"{self.IMAGE_BASE}w780{details['backdrop_path']}"
            )

        videos_data = self._cached_request(
            f"/movie/{tmdb_id}/videos", {"language": self.language}
        )
        youtube_videos = [
            {
                "name": v.get("name"),
                "url": f"https://www.youtube.com/watch?v={v['key']}",
                "site": v.get("site"),
                "type": v.get("type"),
            }
            for v in videos_data.get("results", [])
            if v.get("site") == "YouTube" and v.get("key")
        ]

        providers_data = self._cached_request(f"/movie/{tmdb_id}/watch/providers", None)
        providers_br = providers_data.get("results", {}).get("BR")
        if providers_br and providers_br.get("flatrate"):
            for p in providers_br["flatrate"]:
                if p.get("logo_path"):
                    p["logo_path"] = f"{self.IMAGE_BASE}w92{p['logo_path']}"

        credits_data = self._cached_request(f"/movie/{tmdb_id}/credits", None)
        filtered_credits = [
            {
                "name": c.get("name"),
                "profile_path": (
                    f"{self.IMAGE_BASE}w185{c['profile_path']}"
                    if c.get("profile_path")
                    else None
                ),
                "character": c.get("character"),
                "known_for_department": c.get("known_for_department"),
            }
            for c in credits_data.get("cast", [])
            if c.get("known_for_department") in ("Acting", "Directing")
        ]

        details["videos"] = youtube_videos
        details["providers"] = providers_br
        details["credits"] = filtered_credits
        return details
