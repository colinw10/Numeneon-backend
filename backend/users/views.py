from django.contrib.auth.models import User
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .models import Profile
from .serializers import ProfileSerializer
from .serializers import EmailLoginSerializer
from rest_framework_simplejwt.tokens import RefreshToken


# ViewSet for Profile CRUD operations - only authenticated users can access
class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# Create new user account with username, email, password, and optional display_name
@api_view(['POST']) 
@permission_classes([AllowAny])
def signup(request):
    data = request.data
    username = data.get('username')
    display_name = data.get('display_name', '')
    email = data.get('email')
    password = data.get('password')

    if not all([username, email, password]):
        return Response({'error': 'Missing required fields.'}, status=status.HTTP_400_BAD_REQUEST)
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already taken.'}, status=status.HTTP_400_BAD_REQUEST)
    if User.objects.filter(email=email).exists():
        return Response({'error': 'Email already registered.'}, status=status.HTTP_400_BAD_REQUEST)

    name_parts = display_name.split(' ', 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ''

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name
    )
    profile = user.profile

    return Response({'message': 'User created successfully.', 'user': {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'profile': ProfileSerializer(profile).data
    }}, status=status.HTTP_201_CREATED)


# Login with email and password, returns JWT tokens
@api_view(['POST'])
@permission_classes([AllowAny])
def email_login(request):
    serializer = EmailLoginSerializer(data=request.data)
    if serializer.is_valid():
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
    else:
        error_msg = serializer.errors.get('non_field_errors', ['Invalid credentials.'])[0]
        return Response({'error': error_msg}, status=status.HTTP_401_UNAUTHORIZED)


# Return currently logged-in user's info with nested profile data
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    user = request.user
    try:
        profile_data = ProfileSerializer(user.profile).data
    except Profile.DoesNotExist:
        profile_data = None

    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'profile': profile_data
    })


# Update current user's profile fields (bio, location, website, avatar)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    user = request.user
    profile, created = Profile.objects.get_or_create(user=user)
    
    data = request.data
    if 'bio' in data:
        profile.bio = data['bio']
    if 'location' in data:
        profile.location = data['location']
    if 'website' in data:
        profile.website = data['website']
    if 'avatar' in data:
        profile.avatar = data['avatar']
    
    profile.save()
    
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'profile': ProfileSerializer(profile).data
    })


# Search users by username, first_name, or last_name - returns up to 20 results
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_users(request):
    from django.db.models import Q
    
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        users = User.objects.exclude(
            id=request.user.id
        ).exclude(
            is_superuser=True
        ).order_by('-date_joined')[:20]
    else:
        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ).exclude(id=request.user.id)[:20]
    
    results = []
    for user in users:
        user_data = {
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }
        try:
            if user.profile and user.profile.avatar:
                user_data['avatar'] = user.profile.avatar
        except Profile.DoesNotExist:
            pass
        results.append(user_data)
    
    return Response(results)