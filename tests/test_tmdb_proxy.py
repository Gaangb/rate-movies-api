from unittest.mock import patch


@patch("tmdb.client.requests.get")
def test_search_proxy(mock_get, client):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"results": [{"id": 1, "title": "X"}]}
    r = client.get("/api/v1/search/?q=x")
    assert r.status_code == 200
    assert r.json()["results"][0]["id"] == 1