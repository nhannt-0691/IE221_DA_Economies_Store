from django.urls import path
from .views import (
    RegisterAPI,
    LoginAPIView,
    GetProfileView,
    UpdateProfileView,
    ChangePasswordView,
    UserListAPIView,
    ChangeAccountStatusAPIView,
)

urlpatterns = [
    # auth
    path('register/', RegisterAPI.as_view(), name='register'),
    path('login/', LoginAPIView.as_view(), name='login'),

    # profile
    path('profile/', GetProfileView.as_view(), name='get_profile'),
    path('update_profile/', UpdateProfileView.as_view(), name='update_profile'),
    path('change_password/', ChangePasswordView.as_view(), name='change_password'),

    # admin
    path('users/', UserListAPIView.as_view(), name='user_list'),
    path('users/<int:user_id>/change_status/', ChangeAccountStatusAPIView.as_view(), name='change_user_status'),
]