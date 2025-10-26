from django.db import models


class FavoritedMovie(models.Model):
    account_id = models.BigIntegerField()
    movie_id = models.BigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "favorited_movies"
        unique_together = ("account_id", "movie_id")
        indexes = [
            models.Index(fields=["account_id"]),
            models.Index(fields=["movie_id"]),
        ]

    def __str__(self):
        return f"Account {self.account_id} → Movie {self.movie_id}"
