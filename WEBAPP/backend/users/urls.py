from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    # Authentication
    UserRegistrationView, UserLoginView, UserLogoutView,
    VerifyEmailView, PasswordResetRequestView, PasswordResetConfirmView,
    ChangePasswordView,
    
    # User Profile
    CurrentUserView, UserProfileView, UserSettingsView,
    
    # Sessions
    UserSessionListView, UserSessionRevokeView,
    
    # Chat
    ChatConversationListCreateView, ChatConversationDetailView,
    ChatMessageListView, ChatMessageCreateView,
)

app_name = 'users'

urlpatterns = [
    # ========== Authentication ==========
    path('auth/register/', UserRegistrationView.as_view(), name='register'),
    path('auth/login/', UserLoginView.as_view(), name='login'),
    path('auth/logout/', UserLogoutView.as_view(), name='logout'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('auth/forgot-password/', PasswordResetRequestView.as_view(), name='forgot-password'),
    path('auth/reset-password/', PasswordResetConfirmView.as_view(), name='reset-password'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change-password'),
    
    # ========== User Profile ==========
    path('users/me/', CurrentUserView.as_view(), name='current-user'),
    path('users/me/profile/', UserProfileView.as_view(), name='user-profile'),
    path('users/me/settings/', UserSettingsView.as_view(), name='user-settings'),
    
    # ========== Sessions ==========
    path('users/sessions/', UserSessionListView.as_view(), name='session-list'),
    path('users/sessions/<int:session_id>/', UserSessionRevokeView.as_view(), name='session-revoke'),
    
    # ========== Chat ==========
    path('chat/conversations/', ChatConversationListCreateView.as_view(), name='conversation-list'),
    path('chat/conversations/<int:pk>/', ChatConversationDetailView.as_view(), name='conversation-detail'),
    path('chat/conversations/<int:conversation_id>/messages/', ChatMessageListView.as_view(), name='message-list'),
    path('chat/conversations/<int:conversation_id>/messages/create/', ChatMessageCreateView.as_view(), name='message-create'),
]
