from django.db import models
from django.utils import timezone

class RateCache(models.Model):
    base_currency = models.CharField(max_length=3, default="USD")
    rates = models.JSONField()          # full matrix + fetched_at + stale
    fetched_at = models.DateTimeField()
    stale = models.BooleanField(default=False)

    class Meta:
        get_latest_by = "fetched_at"
        verbose_name = "Rate Cache"

    def __str__(self):
        return f"Rates @ {self.fetched_at}"
