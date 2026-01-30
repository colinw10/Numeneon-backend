from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.db.models import Q, Max, Count
from .models import Message
from .serializers import MessageSerializer, ConversationSerializer
import logging

logger = logging.getLogger(__name__)


class MessageListCreateView(generics.ListCreateAPIView):
    """
    GET: List all messages for the authenticated user (sent and received)
    POST: Send a new message
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(
            Q(sender=user) | Q(receiver=user)
        ).select_related('sender', 'receiver')

    def create(self, request, *args, **kwargs):
        logger.info(f"Message create request from user {request.user.id}: {request.data}")
        response = super().create(request, *args, **kwargs)
        logger.info(f"Message created successfully: {response.data}")
        return response


class ConversationView(generics.ListAPIView):
    """
    GET: Get all messages in a conversation with a specific user
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        other_user_id = self.kwargs.get('user_id')
        return Message.objects.filter(
            (Q(sender=user) & Q(receiver_id=other_user_id)) |
            (Q(sender_id=other_user_id) & Q(receiver=user))
        ).select_related('sender', 'receiver')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def conversation_list(request):
    """
    Get list of all conversations for the authenticated user.
    Returns the other user and the last message in each conversation.
    """
    user = request.user
    
    # Get all users the current user has messaged with
    sent_to = Message.objects.filter(sender=user).values_list('receiver', flat=True)
    received_from = Message.objects.filter(receiver=user).values_list('sender', flat=True)
    user_ids = set(sent_to) | set(received_from)
    
    conversations = []
    for other_id in user_ids:
        other_user = User.objects.get(id=other_id)
        last_message = Message.objects.filter(
            (Q(sender=user) & Q(receiver_id=other_id)) |
            (Q(sender_id=other_id) & Q(receiver=user))
        ).order_by('-created_at').first()
        
        unread_count = Message.objects.filter(
            sender_id=other_id,
            receiver=user,
            is_read=False
        ).count()
        
        conversations.append({
            'user': {'id': other_user.id, 'username': other_user.username},
            'last_message': MessageSerializer(last_message).data,
            'unread_count': unread_count
        })
    
    # Sort by last message date
    conversations.sort(key=lambda x: x['last_message']['created_at'], reverse=True)
    
    return Response(conversations)


@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def read_all(request):
    """
    Mark all messages from a specific user as read.
    Accepts user_id as query parameter: /api/messages/read_all/?user_id=123
    """
    user_id = request.query_params.get('user_id')
    if not user_id:
        return Response({'error': 'user_id query parameter required'}, status=status.HTTP_400_BAD_REQUEST)
    
    updated = Message.objects.filter(
        sender_id=user_id,
        receiver=request.user,
        is_read=False
    ).update(is_read=True)
    
    return Response({'marked_read': updated})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_as_read(request, user_id):
    """
    Mark all messages from a specific user as read.
    """
    updated = Message.objects.filter(
        sender_id=user_id,
        receiver=request.user,
        is_read=False
    ).update(is_read=True)
    
    return Response({'marked_read': updated})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def debug_messages(request):
    """
    Debug endpoint to check all messages for current user.
    """
    user = request.user
    total_messages = Message.objects.count()
    user_messages = Message.objects.filter(
        Q(sender=user) | Q(receiver=user)
    ).count()
    
    sent = Message.objects.filter(sender=user).values('receiver__username', 'content', 'created_at')[:10]
    received = Message.objects.filter(receiver=user).values('sender__username', 'content', 'created_at')[:10]
    
    return Response({
        'total_messages_in_db': total_messages,
        'user_messages': user_messages,
        'user_id': user.id,
        'username': user.username,
        'recent_sent': list(sent),
        'recent_received': list(received),
    })
