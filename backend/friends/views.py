# 🟣 CRYSTAL - Friends System Lead
# views.py - API endpoints for friend operations
"""
Create Friends API Views - manage friendships and requests
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from .models import FriendRequest, Friendship
from notifications.utils import notify_friend_request, notify_friend_accepted


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def friend_list(request):
    """
    Returns all friends of the logged-in user
    """
    user = request.user

    friendships = Friendship.objects.filter(user=user)

    friends = []
    for fs in friendships:
        friend = fs.friend
        friends.append({
            'id': friend.id,
            'username': friend.username,
            'last_name': friend.last_name
        })

    return Response(friends, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pending_requests(request):
    """
    Returns all pending friend requests TO the logged-in user
    """
    user = request.user

    requests = FriendRequest.objects.filter(to_user=user)

    pending = []
    for fr in requests:
        pending.append({
            'id': fr.id,
            'from_user': {
                'id': fr.from_user.id,
                'username': fr.from_user.username,
                'first_name': fr.from_user.first_name,
                'last_name': fr.from_user.last_name
            },
            'created_at': fr.created_at.isoformat()
        })
    return Response(pending, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def friend_suggestions(request):
    """
    Returns users who are NOT:
    - The current user
    - Already friends
    - Pending requests (sent OR received)
    """
    user = request.user
    
    # Get IDs to exclude
    friend_ids = Friendship.objects.filter(user=user).values_list('friend_id', flat=True)
    sent_request_ids = FriendRequest.objects.filter(from_user=user).values_list('to_user_id', flat=True)
    received_request_ids = FriendRequest.objects.filter(to_user=user).values_list('from_user_id', flat=True)
    
    exclude_ids = set(friend_ids) | set(sent_request_ids) | set(received_request_ids) | {user.id}
    
    # Get suggested users
    suggested_users = User.objects.exclude(id__in=exclude_ids).select_related('profile')[:20]
    
    suggestions = []
    for u in suggested_users:
        profile_picture = None
        if hasattr(u, 'profile') and u.profile:
            profile_picture = u.profile.profile_picture
        
        suggestions.append({
            'id': u.id,
            'username': u.username,
            'first_name': u.first_name,
            'last_name': u.last_name,
            'profile_picture': profile_picture,
        })
    
    return Response(suggestions, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_request(request, user_id):
    """
    Sends a friend request to another user
    """
    from_user = request.user

    try:
        to_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    if from_user == to_user:
        return Response({'error': 'You cannot friend yourself'}, status=status.HTTP_400_BAD_REQUEST)

    if FriendRequest.objects.filter(from_user=from_user, to_user=to_user).exists():
        return Response({'error': 'Friend request already sent'}, status=status.HTTP_400_BAD_REQUEST)

    if Friendship.objects.filter(user=from_user, friend=to_user).exists():
        return Response({'error': 'You are already friends'}, status=status.HTTP_400_BAD_REQUEST)

    # Create the friend request
    friend_request = FriendRequest.objects.create(
        from_user=from_user,
        to_user=to_user
    )

    #  Send real-time notification to recipient
    notify_friend_request(
        to_user_id=to_user.id,
        from_user=from_user,
        request_id=friend_request.id
    )


    return Response({'message': 'Friend request sent'}, status=status.HTTP_201_CREATED)
 


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_request(request, request_id):
    """
    Accepts a pending friend request
    """
    user = request.user

    try:
        fr = FriendRequest.objects.get(id=request_id)
    except FriendRequest.DoesNotExist:
        return Response({'error': 'Request not found'}, status=status.HTTP_404_NOT_FOUND)

    if fr.to_user != user:
        return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

    # Store the original sender before deleting the request
    original_sender = fr.from_user

    Friendship.objects.create(user=user, friend=original_sender)
    Friendship.objects.create(user=original_sender, friend=user)

    fr.delete()

    # Send real-time notification to original sender
    notify_friend_accepted(
        to_user_id=original_sender.id,
        friend=user  # The person who accepted
    )

    return Response({
        'message': 'Friend request accepted',
        'friend': {
            'id': original_sender.id,
            'username': original_sender.username,
            'first_name': original_sender.first_name,
            'last_name': original_sender.last_name
        }
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def decline_request(request, request_id):
    """
    Declines a pending friend request
    """
    user = request.user

    try:
        fr = FriendRequest.objects.get(id=request_id)
    except FriendRequest.DoesNotExist:
        return Response({'error': 'Request not found'}, status=status.HTTP_404_NOT_FOUND)

    if fr.to_user != user:
        return Response({'message': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
    
    fr.delete()

    return Response({'message': 'Friend request declined'}, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_friend(request, user_id):
    """
    Removes a friend from your friend list
    """
    me = request.user

    try:
        target = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    Friendship.objects.filter(user=me, friend=target).delete()
    Friendship.objects.filter(user=target, friend=me).delete()

    return Response({'message': 'Friend removed'}, status=status.HTTP_200_OK)