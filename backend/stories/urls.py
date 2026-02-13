"""
Stories Feature URLs

Endpoints:
- GET/POST  /api/stories/              - List all stories / Create story
- GET       /api/stories/me/           - Get my stories
- GET       /api/stories/user/<id>/    - Get stories by user
- DELETE    /api/stories/<id>/         - Delete a story
- POST      /api/stories/<id>/view/    - Mark story as viewed
- POST/DEL  /api/stories/<id>/react/   - Add/remove reaction
"""
from django.urls import path
from . import views

urlpatterns = [
    # List all stories from friends / Create new story
    path('', views.stories_list_create, name='stories-list-create'),
    
    # Get current user's stories
    path('me/', views.my_stories, name='my-stories'),
    
    # Get stories by specific user
    path('user/<int:user_id>/', views.stories_by_user, name='stories-by-user'),
    
    # Delete a story (owner only)
    path('<uuid:story_id>/', views.story_delete, name='story-delete'),
    
    # Mark story as viewed
    path('<uuid:story_id>/view/', views.story_view, name='story-view'),
    
    # Add/remove reaction to story
    path('<uuid:story_id>/react/', views.story_react, name='story-react'),
]
