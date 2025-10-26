from django.urls import reverse


def test_add_and_list(client):
    client.get("/api/v1/search/?q=x")
    r = client.post("/api/v1/favorites/", {"tmdb_id": 1, "title": "Matrix"})
    assert r.status_code in (200, 201)
    r2 = client.get("/api/v1/favorites/")
    assert r2.status_code == 200
    assert r2.json()[0]["tmdb_id"] == 1