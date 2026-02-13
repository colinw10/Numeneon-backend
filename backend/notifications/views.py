"""
Views for push notification management.
"""
from django.shortcuts import render
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .models import PushSubscription
from .serializers import PushSubscriptionSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def get_vapid_public_key(request):
    """
    Return the VAPID public key for the frontend to use when subscribing.
    This endpoint is public since it's needed before the user subscribes.
    """
    public_key = getattr(settings, 'VAPID_PUBLIC_KEY', None)
    
    if not public_key:
        return Response(
            {'error': 'Push notifications not configured'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    return Response({'publicKey': public_key})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def subscribe_push(request):
    """
    Subscribe a user's browser to push notifications.
    
    Expected body:
    {
        "endpoint": "https://fcm.googleapis.com/...",
        "keys": {
            "p256dh": "BNcRd...",
            "auth": "tB..."
        }
    }
    """
    serializer = PushSubscriptionSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if serializer.is_valid():
        serializer.save()
        return Response(
            {'message': 'Successfully subscribed to push notifications'},
            status=status.HTTP_201_CREATED
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unsubscribe_push(request):
    """
    Unsubscribe a user's browser from push notifications.
    
    Expected body:
    {
        "endpoint": "https://fcm.googleapis.com/..."
    }
    """
    endpoint = request.data.get('endpoint')
    
    if not endpoint:
        return Response(
            {'error': 'endpoint is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Delete subscription for this endpoint (only if it belongs to this user)
    deleted_count, _ = PushSubscription.objects.filter(
        user=request.user,
        endpoint=endpoint
    ).delete()
    
    if deleted_count > 0:
        return Response({'message': 'Successfully unsubscribed'})
    
    return Response(
        {'message': 'Subscription not found'},
        status=status.HTTP_404_NOT_FOUND
    )
