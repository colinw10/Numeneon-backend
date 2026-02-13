from django.urls import path
from . import views

urlpatterns = [
    # Search songs via Deezer
    path('search/', views.search_songs, name='mystudio-search'),
    
    # Current user's profile (must be before <username> to not conflict)
    path('profile/', views.get_my_mystudio_profile, name='mystudio-my-profile'),
    
    # Public - anyone can view
    path('<str:username>/', views.get_mystudio_profile, name='mystudio-profile'),

    # Authenticated - update your own settings
    path('', views.update_mystudio_settings, name='mystudio-update'),

    # Playlist management
    path('playlist/', views.add_song_to_playlist, name='playlist-add'),
    path('playlist/<int:song_id>/', views.remove_song_from_playlist, name='playlist-remove'),
    path('playlist/reorder/', views.reorder_playlist, name='playlist-reorder'),
]