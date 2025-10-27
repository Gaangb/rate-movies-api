from django.db import models


class FavoritedMovie(models.Model):
    account_id = models.BigIntegerField()
    movie_id = models.BigIntegerField()
    title = models.CharField(max_length=255, blank=True, default="")
    overview = models.TextField(blank=True, null=True)
    poster_path = models.CharField(max_length=255, blank=True, null=True)
    release_date = models.CharField(max_length=20, blank=True, null=True)
    genre_ids = models.JSONField(default=list)
    vote_average = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "favorited_movies"
        unique_together = ("account_id", "movie_id")
        indexes = [
            models.Index(fields=["account_id"]),
            models.Index(fields=["movie_id"]),
        ]

    def __str__(self):
        return f"{self.title or 'Movie'} ({self.movie_id}) - Account {self.account_id}"


class FavoriteList(models.Model):
    account_id = models.BigIntegerField()
    list_name = models.CharField(max_length=255)
    movie_ids = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "favorite_lists"
        indexes = [
            models.Index(fields=["account_id"]),
        ]

    def __str__(self):
        return f"{self.list_name} (Account {self.account_id})"
