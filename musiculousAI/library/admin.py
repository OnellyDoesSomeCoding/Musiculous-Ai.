from django.contrib import admin
from .models import Song

@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
	list_display = (
		"id",
		"song_name",
		"owner",
		"generation_status",
		"is_public",
		"time_created",
	)
	list_filter = ("generation_status", "is_public", "time_created")
	search_fields = ("song_name", "owner__username", "owner__email", "genres", "prompt")
	ordering = ("-time_created",)
	readonly_fields = ("time_created", "most_recent_update")
