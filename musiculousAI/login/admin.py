from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Count
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = BaseUserAdmin.list_display + ("song_count",)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(song_count=Count("songs"))

    @admin.display(description="Songs Generated", ordering="song_count")
    def song_count(self, obj):
        return obj.song_count
