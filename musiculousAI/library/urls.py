from django.urls import path
from . import views

urlpatterns = [
    path('', views.library_home, name='library_home'),
    path('folders/create/', views.folder_create, name='folder_create'),
    path('folders/<int:folder_id>/', views.folder_detail, name='folder_detail'),
    path('folders/<int:folder_id>/add-song/', views.folder_add_song, name='folder_add_song'),
    path('song/<int:song_id>/', views.song_detail, name='song_detail'),
    path('song/<int:song_id>/share/', views.song_share, name='song_share'),
    path('create/', views.song_create, name='song_create'),
    path('song/<int:song_id>/edit/', views.song_edit, name='song_edit'),
    path('song/<int:song_id>/delete/', views.song_delete, name='song_delete'),
    path('song/<int:song_id>/toggle-public/', views.song_toggle_public, name='song_toggle_public'),
    path('song/<int:song_id>/download/', views.song_download, name='song_download'),
    path('share/<uuid:share_token>/', views.song_shared_detail, name='song_shared_detail'),
    path('share/<uuid:share_token>/download/', views.song_shared_download, name='song_shared_download'),
]
