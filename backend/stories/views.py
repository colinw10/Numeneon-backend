"""
Stories Feature Views

API endpoints for Instagram-style stories that expire after 24 hours.
"""
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Story, StoryView, StoryReaction
from .serializers import StorySerializer, StoryCreateSerializer, StoryReactionSerializer
from friends.models import Friendship

# Import push notification utilities (optional - graceful fallback if not available)
try:
    from notifications.utils import send_push_notification
    PUSH_ENABLED = True
except ImportError:
    PUSH_ENABLED = False


def get_friend_ids(user):
    """Get list of friend user IDs for the given user."""
    return list(Friendship.objects.filter(user=user).values_list('friend_id', flat=True))


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def stories_list_create(request):
    """
    GET: Get all non-expired stories from friends (and self).
    POST: Create a new story.
    """
    if request.method == 'GET':
        # Get friend IDs + self
        friend_ids = get_friend_ids(request.user)
        friend_ids.append(request.user.id)  # Include own stories
        
        # Filter non-expired stories from friends
        stories = Story.objects.filter(
            user_id__in=friend_ids,
            expires_at__gt=timezone.now()
        ).select_related('user', 'user__profile').prefetch_related('views', 'reactions')
        
        serializer = StorySerializer(stories, many=True, context={'request': request})
        return Response({'stories': serializer.data})
    
    elif request.method == 'POST':
        serializer = StoryCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            story = serializer.save()
            # Return full story data
            response_serializer = StorySerializer(story, context={'request': request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stories_by_user(request, user_id):
    """
    GET: Get all non-expired stories from a specific user.
    """
    stories = Story.objects.filter(
        user_id=user_id,
        expires_at__gt=timezone.now()
    ).select_related('user', 'user__profile').prefetch_related('views', 'reactions')
    
    serializer = StorySerializer(stories, many=True, context={'request': request})
    return Response({'stories': serializer.data})


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def story_delete(request, story_id):
    """
    DELETE: Delete your own story.
    """
    story = get_object_or_404(Story, id=story_id)
    
    # Check ownership
    if story.user != request.user:
        return Response(
            {'error': 'You can only delete your own stories'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    story.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def story_view(request, story_id):
    """
    POST: Mark a story as viewed by current user.
    Idempotent - won't fail if already viewed.
    """
    story = get_object_or_404(Story, id=story_id)
    
    # Don't count self-views
    if story.user == request.user:
        return Response({
            'success': True,
            'view_count': story.views.count(),
            'message': 'Self-views not counted'
        })
    
    # Create view record (ignore if already exists)
    StoryView.objects.get_or_create(
        story=story,
        viewer=request.user
    )
    
    return Response({
        'success': True,
        'view_count': story.views.count()
    })


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def story_react(request, story_id):
    """
    POST: Add or update reaction to a story.
    DELETE: Remove your reaction from a story.
    """
    story = get_object_or_404(Story, id=story_id)
    
    if request.method == 'POST':
        serializer = StoryReactionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        reaction_type = serializer.validated_data['reaction_type']
        
        # Update or create reaction
        reaction, created = StoryReaction.objects.update_or_create(
            story=story,
            user=request.user,
            defaults={'reaction_type': reaction_type}
        )
        
        # Send push notification to story owner (if not self)
        if PUSH_ENABLED and story.user != request.user:
            emoji = '❤️' if reaction_type == 'heart' else '⚡'
            send_push_notification(
                user_id=story.user.id,
                title='Story Reaction',
                body=f'{request.user.username} reacted {emoji} to your story',
                data={
                    'type': 'story_reaction',
                    'story_id': str(story.id),
                    'reaction_type': reaction_type
                },
                tag=f'story-reaction-{story.id}'
            )
        
        return Response({
            'success': True,
            'reaction_type': reaction_type,
            'heart_count': story.reactions.filter(reaction_type='heart').count(),
            'thunder_count': story.reactions.filter(reaction_type='thunder').count()
        })
    
    elif request.method == 'DELETE':
        deleted_count, _ = StoryReaction.objects.filter(
            story=story,
            user=request.user
        ).delete()
        
        if deleted_count > 0:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'error': 'No reaction to remove'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_stories(request):
    """
    GET: Get all non-expired stories for the current user.
    Useful for managing your own stories.
    """
    stories = Story.objects.filter(
        user=request.user,
        expires_at__gt=timezone.now()
    ).select_related('user', 'user__profile').prefetch_related('views', 'reactions')
    
    serializer = StorySerializer(stories, many=True, context={'request': request})
    return Response({'stories': serializer.data})
