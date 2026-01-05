from django.urls import path
from .views import (
    RegisterAPI,
    LoginAPIView,
    GetProfileView,
    UpdateProfileView,
    ChangePasswordView,
    UserListAPIView,
    ChangeAccountStatusAPIView,
    VerifyAccountAPI,
    ForgotPasswordView,
    VerifyPasswordOTPView
)   

urlpatterns = [
    # auth
    path('register/', RegisterAPI.as_view(), name='register'),
    path('verify_email/', VerifyAccountAPI.as_view(), name='verify_email'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('forgot_password/', ForgotPasswordView.as_view(), name='forgot_password' ),
    path('reset_password/', VerifyPasswordOTPView.as_view(), name='reset_password' ),

    # profile
    path('profile/', GetProfileView.as_view(), name='get_profile'),
    path('update_profile/', UpdateProfileView.as_view(), name='update_profile'),
    path('change_password/', ChangePasswordView.as_view(), name='change_password'),

    # admin
    path('users/', UserListAPIView.as_view(), name='user_list'),
    path('users/<int:user_id>/change_status/', ChangeAccountStatusAPIView.as_view(), name='change_user_status'),
]