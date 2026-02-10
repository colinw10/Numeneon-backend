"""
URL configuration for push notifications.

Endpoints:
- GET  /api/notifications/vapid-public-key/ - Get VAPID public key (public)
- POST /api/notifications/subscribe/        - Subscribe to push notifications
- POST /api/notifications/unsubscribe/      - Unsubscribe from push notifications
"""
from django.urls import path
from . import views

urlpatterns = [
    # VAPID public key - frontend needs this to subscribe
    path('vapid-public-key/', views.get_vapid_public_key, name='vapid-public-key'),
    
    # Push subscription management
    path('subscribe/', views.subscribe_push, name='push-subscribe'),
    path('unsubscribe/', views.unsubscribe_push, name='push-unsubscribe'),
]
