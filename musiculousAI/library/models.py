from django.conf import settings
from django.db import models
import uuid


class SiteConfiguration(models.Model):
    """Singleton model for site-wide admin controls."""
    generation_enabled = models.BooleanField(
        default=True,
        help_text="Uncheck to disable new AI music generation for all users.",
    )

    class Meta:
        verbose_name = "Site Configuration"
        verbose_name_plural = "Site Configuration"

    def __str__(self):
        return "Site Configuration"

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


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


class Folder(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="folders",
    )
    name = models.CharField(max_length=50)
    image = models.ImageField(upload_to="folder_images/", null=True, blank=True)
    songs = models.ManyToManyField(Song, related_name="folders", blank=True)
    time_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("name",)
        unique_together = ("owner", "name")

    def __str__(self):
        return f"{self.owner}: {self.name}"
