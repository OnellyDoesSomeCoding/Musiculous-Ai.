from django.db import models


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
