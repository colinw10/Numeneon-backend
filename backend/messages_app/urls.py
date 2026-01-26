from django.urls import path
from . import views

urlpatterns = [
    # GET all messages / POST new message
    path('', views.MessageListCreateView.as_view(), name='message-list-create'),
    
    # GET list of all conversations
    path('conversations/', views.conversation_list, name='conversation-list'),
    
    # GET messages with specific user
    path('conversation/<int:user_id>/', views.ConversationView.as_view(), name='conversation-detail'),
    
    # POST/GET mark messages as read (query param version)
    path('read_all/', views.read_all, name='read-all'),
    
    # POST mark messages from user as read (path param version)
    path('conversation/<int:user_id>/read/', views.mark_as_read, name='mark-as-read'),
]
