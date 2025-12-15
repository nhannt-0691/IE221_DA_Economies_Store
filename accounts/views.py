from __future__ import annotations
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.shortcuts import render
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework.permissions import IsAdminUser, IsAuthenticated

### USER REGISTRATION AND LOGIN VIEW###
class RegisterAPI(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')

        if not username or not password or not email:
            return Response({'error': 'Username, password, and email are required.'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists.'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, password=password, email=email)
        user.save()

        return Response({'message': 'User registered successfully.'}, status=status.HTTP_201_CREATED)
    
    
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        
        
        data = super().validate(attrs)
        self.user.last_login = timezone.now()
        self.user.save(update_fields=["last_login"])
        data.update({"message": "User logined successfully."})

        return data

class LoginAPIView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    
def build_profile_data(user):
    return {
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        
        'is_staff': user.is_staff,
        'is_active': user.is_active,
        'date_joined': user.date_joined,
        'last_login': user.last_login,
    }


### USER VIEWS ###   
class GetProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile_data = build_profile_data(request.user)
        return Response(profile_data, status=status.HTTP_200_OK)
 
class UpdateProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def patch(self, request):
        user = request.user
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        email = request.data.get('email')

        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        if email:
            user.email = email

        user.save()
        profile_data = build_profile_data(request.user)
        
        return Response({
            'message': 'Profile updated successfully.',
            'profile': profile_data
        }, status=status.HTTP_200_OK)    
####ADMIN VIEWS####
    
class UserListAPIView(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        
        users = User.objects.all().values('id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined', 'last_login')
        return Response(users, status=status.HTTP_200_OK)
    
class ChangeAccountStatusAPIView(APIView):
    permission_classes = [IsAdminUser]
    
    def patch(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            user.is_active = not user.is_active
            user.save()
            return Response({'message': 'User status changed successfully.'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)