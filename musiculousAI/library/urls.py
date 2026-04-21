from django.urls import path
from . import views

urlpatterns = [
    path('', views.library_home, name='library_home'),
    path('song/<int:song_id>/', views.song_detail, name='song_detail'),
    path('create/', views.song_create, name='song_create'),
    path('song/<int:song_id>/edit/', views.song_edit, name='song_edit'),
    path('song/<int:song_id>/delete/', views.song_delete, name='song_delete'),
    path('song/<int:song_id>/toggle-public/', views.song_toggle_public, name='song_toggle_public'),
    path('song/<int:song_id>/download/', views.song_download, name='song_download'),
]
