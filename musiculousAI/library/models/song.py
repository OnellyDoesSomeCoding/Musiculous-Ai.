import uuid

from django.conf import settings
from django.db import models


class Song(models.Model):
    STATUS_CHOICES = (
        ("queued", "Queued"),
        ("generating", "Generating"),
        ("ready", "Ready"),
        ("failed", "Failed"),
    )

    # Core
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="songs")
    song_name = models.CharField(max_length=50)
    description = models.CharField(max_length=300, blank=True)
    prompt = models.TextField(max_length=500)
    duration_in_seconds = models.PositiveIntegerField(null=True, blank=True)

    # Media
    cover_image = models.ImageField(upload_to="song_covers/", null=True, blank=True)
    song_file = models.FileField(upload_to="songs/", null=True, blank=True)
    genres = models.CharField(max_length=120, blank=True)

    ai_source = models.CharField(max_length=20, blank=True, default="")  # e.g. "suno", "replicate"
    share_token = models.UUIDField(unique=True, null=True, blank=True, editable=False)

    is_public = models.BooleanField(default=False)
    time_created = models.DateTimeField("Time Created", auto_now_add=True)
    most_recent_update = models.DateTimeField("Most Recent Update", auto_now=True)
    generation_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="queued")

    def __str__(self):
        return self.song_name
