from __future__ import annotations
from django.http import JsonResponse
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.shortcuts import render
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAdminUser, IsAuthenticated

User = get_user_model()

### USER REGISTRATION AND LOGIN VIEW###
class RegisterAPI(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email') 
        
        if User.objects.filter(email=email).exists():
            return Response({
                "error": "Email already exists."
            }, status=status.HTTP_400_BAD_REQUEST)  

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
    def to_local(dt):
        return timezone.localtime(dt).strftime("%Y-%m-%d %H:%M:%S") if dt else None
    
    return {
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'phone': user.phone,
        'address': user.address,
        
        'is_staff': user.is_staff,
        'is_active': user.is_active,
        'date_joined': to_local(user.date_joined),
        'last_login': to_local(user.last_login),
        'updated_at': to_local(getattr(user, 'updated_at', None)),
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
        ALLOWED_FIELDS = {"first_name", "last_name", "email", "phone", "address"}

        for key in request.data.keys():
            if key not in ALLOWED_FIELDS:
                return Response(
                    {"error": f"Field '{key}' is not allowed."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        user = request.user

        email = request.data.get("email")
        if email:
            if User.objects.filter(email=email).exclude(id=user.id).exists():
                return Response(
                    {"error": "Email already exists."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.email = email

        first_name = request.data.get("first_name")
        if first_name:
            user.first_name = first_name

        last_name = request.data.get("last_name")
        if last_name:
            user.last_name = last_name

        user.save()

        return Response({
            "message": "Profile updated successfully.",
            "profile": build_profile_data(user),
        }, status=status.HTTP_200_OK)
   

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not old_password or not new_password:
            return Response(
                {"error": "Old password and new password are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user

        if not user.check_password(old_password):
            return Response(
                {"error": "Old password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(new_password) < 6:
            return Response(
                {"error": "New password must be at least 6 characters."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if old_password == new_password:
            return Response(
                {"error": "New password must be different from old password."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()

        return Response({"message": "Password changed successfully."},
                        status=status.HTTP_200_OK)

####ADMIN VIEWS####  
class UserListAPIView(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        users = User.objects.all().values('id', 'username', 'email', 'first_name', 'last_name', 'phone', 'address', 'is_staff', 'is_active', 'date_joined', 'last_login', 'updated_at')
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