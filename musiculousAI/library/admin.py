from django.contrib import admin
from django.db.models import Count
from .models import Folder, Song, SiteConfiguration


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


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "owner", "time_created", "song_count")
    search_fields = ("name", "owner__username", "owner__email")
    ordering = ("name",)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_song_count=Count("songs"))

    def song_count(self, obj):
        return obj._song_count
