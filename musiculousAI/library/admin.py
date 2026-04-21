from django.contrib import admin
from django.db.models import Count
from .models import Song, SiteConfiguration


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    """Singleton admin — only one row ever exists."""

    def has_add_permission(self, request):
        return not SiteConfiguration.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "song_name",
        "owner",
        "ai_source",
        "generation_status",
        "is_public",
        "time_created",
    )
    list_filter = ("generation_status", "is_public", "ai_source", "time_created")
    search_fields = ("song_name", "owner__username", "owner__email", "genres", "prompt")
    ordering = ("-time_created",)
    readonly_fields = ("time_created", "most_recent_update")
    actions = ["delete_selected"]
