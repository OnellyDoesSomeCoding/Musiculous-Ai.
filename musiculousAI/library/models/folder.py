from django.conf import settings
from django.db import models

from .song import Song


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
