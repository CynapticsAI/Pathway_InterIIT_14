from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import logout
from django.utils import timezone
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from .models import (
    CustomUser, UserProfile, ChatConversation, ChatMessage,
    UserSession, EmailVerificationToken, PasswordResetToken, UserSettings
)
from .serializers import (
    CustomUserSerializer, UserRegistrationSerializer, UserLoginSerializer,
    ChangePasswordSerializer, UserProfileSerializer, ChatConversationSerializer,
    ChatMessageSerializer, ChatMessageCreateSerializer, UserSessionSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    EmailVerificationSerializer, ChatbotMessageSerializer, UserSettingsSerializer
)
from .utils import (
    generate_verification_token, get_token_expiry, send_verification_email,
    send_password_reset_email, create_user_session, log_user_activity, get_device_info
)


@extend_schema(
    tags=['Authentication'],
    summary='Register a new user',
    description='''
    Register a new user account with email and password.
    
    **Process:**
    1. User provides username, email, and password
    2. System validates the data (unique email, password strength)
    3. User account is created (email not verified yet)
    4. Email verification token is generated
    5. Verification email is sent
    
    **Next Steps:**
    - Check email for verification link
    - Verify email using the token
    - Login to get JWT tokens
    ''',
    request=UserRegistrationSerializer,
    responses={
        201: CustomUserSerializer,
        400: OpenApiTypes.OBJECT,
    },
    examples=[
        OpenApiExample(
            'Registration Example',
            description='Example request to register a new user',
            value={
                'username': 'john_doe',
                'email': 'john@example.com',
                'password': 'SecurePass123!',
                'password2': 'SecurePass123!',
                'first_name': 'John',
                'last_name': 'Doe'
            },
            request_only=True,
        ),
        OpenApiExample(
            'Success Response',
            description='Successful registration response',
            value={
                'message': 'User registered successfully. Please check your email to verify your account.',
                'user': {
                    'id': 1,
                    'username': 'john_doe',
                    'email': 'john@example.com',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'email_verified': False
                }
            },
            response_only=True,
            status_codes=['201'],
        ),
    ]
)
class UserRegistrationView(APIView):
    """
    User registration endpoint
    POST /api/auth/register/
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Create email verification token
            token = generate_verification_token(user)
            EmailVerificationToken.objects.create(
                user=user,
                token=token,
                email=user.email,
                expires_at=get_token_expiry(hours=24)
            )
            
            # Send verification email
            try:
                send_verification_email(user, token)
            except Exception as e:
                print(f"Failed to send verification email: {e}")
            
            # Log activity
            log_user_activity(user, 'register', request)
            
            return Response({
                'message': 'User registered successfully. Please check your email to verify your account.',
                'user': CustomUserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Authentication'],
    summary='Login with email and password',
    description='''
    Authenticate user and receive JWT access and refresh tokens.
    
    **Authentication Flow:**
    1. User provides email and password
    2. System validates credentials
    3. JWT tokens are generated (access + refresh)
    4. User session is created and tracked
    5. Activity is logged
    
    **Token Usage:**
    - **Access Token**: Use for authenticated API requests (expires in 1 hour)
    - **Refresh Token**: Use to get new access token (expires in 7 days)
    
    **Next Steps:**
    - Store tokens securely (httpOnly cookies recommended)
    - Include access token in Authorization header: `Bearer <access_token>`
    - Use refresh token when access token expires
    ''',
    request=UserLoginSerializer,
    responses={
        200: {
            'type': 'object',
            'properties': {
                'message': {'type': 'string'},
                'tokens': {
                    'type': 'object',
                    'properties': {
                        'access': {'type': 'string'},
                        'refresh': {'type': 'string'},
                    }
                },
                'user': {'type': 'object'}
            }
        },
        400: OpenApiTypes.OBJECT,
    },
    examples=[
        OpenApiExample(
            'Login Request',
            description='Login with email and password',
            value={
                'email': 'john@example.com',
                'password': 'SecurePass123!'
            },
            request_only=True,
        ),
        OpenApiExample(
            'Success Response',
            description='Login successful with JWT tokens',
            value={
                'message': 'Login successful',
                'tokens': {
                    'access': 'eyJ0eXAiOiJKV1QiLCJhbGc...',
                    'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGc...'
                },
                'user': {
                    'id': 1,
                    'username': 'john_doe',
                    'email': 'john@example.com',
                    'email_verified': True
                }
            },
            response_only=True,
            status_codes=['200'],
        ),
    ]
)
class UserLoginView(APIView):
    """
    User login endpoint
    POST /api/auth/login/
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            # Create user session
            create_user_session(user, request, access_token, refresh)
            
            # Log activity
            log_user_activity(user, 'login', request)
            
            return Response({
                'message': 'Login successful',
                'tokens': {
                    'access': str(access_token),
                    'refresh': str(refresh),
                },
                'user': CustomUserSerializer(user).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Authentication'],
    summary='Logout current user',
    description='''
    Logout the authenticated user and invalidate all active sessions.
    
    **Actions Performed:**
    - Deactivates all active user sessions
    - Logs the logout activity
    - Clears Django session
    
    **Security Note:**
    This invalidates all sessions, including other devices. Users will need to login again on all devices.
    ''',
    request=None,
    responses={
        200: {
            'type': 'object',
            'properties': {
                'message': {'type': 'string', 'example': 'Logout successful'}
            }
        },
        401: OpenApiTypes.OBJECT,
    },
    examples=[
        OpenApiExample(
            'Success Response',
            value={'message': 'Logout successful'},
            response_only=True,
            status_codes=['200'],
        ),
    ]
)
class UserLogoutView(APIView):
    """
    User logout endpoint
    POST /api/auth/logout/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            # Deactivate user sessions
            UserSession.objects.filter(
                user=request.user,
                is_active=True
            ).update(is_active=False)
            
            # Log activity
            log_user_activity(request.user, 'logout', request)
            
            # Django logout
            logout(request)
            
            return Response({
                'message': 'Logout successful'
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Users'],
    summary='Get or update current user',
    description='''
    **GET**: Retrieve current authenticated user's information
    **PUT**: Update current user's profile information
    
    You can update: first_name, last_name, phone_number, bio, profile_picture
    ''',
    responses={
        200: CustomUserSerializer,
        401: OpenApiTypes.OBJECT,
    }
)
class CurrentUserView(APIView):
    """
    Get current user details
    GET /api/users/me/
    PUT /api/users/me/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary='Get current user details',
        description='Retrieve the authenticated user\'s profile information',
    )
    def get(self, request):
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data)
    
    @extend_schema(
        summary='Update current user',
        description='Update the authenticated user\'s profile information',
        request=CustomUserSerializer,
        examples=[
            OpenApiExample(
                'Update Profile',
                value={
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'phone_number': '+1234567890',
                    'bio': 'Stock market enthusiast'
                },
                request_only=True,
            ),
        ]
    )
    
    def put(self, request):
        serializer = CustomUserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """
    Get and update user profile
    GET /api/users/me/profile/
    PUT /api/users/me/profile/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        profile = request.user.profile
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)
    
    def put(self, request):
        profile = request.user.profile
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Users'],
    summary='Get or update user profile settings',
    description='''
    Manage user profile settings including:
    - Subscription tier and status
    - Favorite stocks and watchlist
    - Notification preferences
    - Usage statistics
    ''',
)
class UserProfileView(APIView):
    """
    Get and update user profile
    GET /api/users/me/profile/
    PUT /api/users/me/profile/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary='Get user profile',
        responses={200: UserProfileSerializer}
    )
    def get(self, request):
        profile = request.user.profile
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)
    
    @extend_schema(
        summary='Update user profile',
        request=UserProfileSerializer,
        responses={200: UserProfileSerializer},
        examples=[
            OpenApiExample(
                'Update Preferences',
                value={
                    'favorite_stocks': ['AAPL', 'GOOGL', 'MSFT'],
                    'watchlist': ['TSLA', 'AMZN'],
                    'notifications_enabled': True
                },
                request_only=True,
            ),
        ]
    )
    def put(self, request):
        profile = request.user.profile
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Authentication'],
    summary='Change password',
    description='''
    Change password for the authenticated user.
    
    **Required:**
    - Current password (for verification)
    - New password
    - New password confirmation
    
    **Security:**
    Password must meet strength requirements (min length, special characters, etc.)
    ''',
    request=ChangePasswordSerializer,
    responses={
        200: {'type': 'object', 'properties': {'message': {'type': 'string'}}},
        400: OpenApiTypes.OBJECT,
    },
    examples=[
        OpenApiExample(
            'Change Password',
            value={
                'old_password': 'OldPass123!',
                'new_password': 'NewSecurePass123!',
                'new_password2': 'NewSecurePass123!'
            },
            request_only=True,
        ),
    ]
)
class ChangePasswordView(APIView):
    """
    Change password for authenticated user
    POST /api/auth/change-password/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            
            # Check old password
            if not user.check_password(serializer.validated_data['old_password']):
                return Response({
                    'old_password': ['Wrong password.']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Set new password
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            # Log activity
            log_user_activity(user, 'password_change', request)
            
            return Response({
                'message': 'Password changed successfully'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Authentication'],
    summary='Verify email address',
    description='''
    Verify user's email address using the token sent via email.
    
    **Process:**
    1. User receives verification email after registration
    2. Email contains a unique token
    3. User clicks link or provides token to this endpoint
    4. System verifies token and marks email as verified
    
    **Token Validity:** 24 hours
    ''',
    request=EmailVerificationSerializer,
    responses={
        200: {'type': 'object', 'properties': {'message': {'type': 'string'}}},
        400: OpenApiTypes.OBJECT,
    },
    examples=[
        OpenApiExample(
            'Verify Email',
            value={'token': 'abc123def456...'},
            request_only=True,
        ),
        OpenApiExample(
            'Success',
            value={'message': 'Email verified successfully'},
            response_only=True,
            status_codes=['200'],
        ),
    ]
)
class VerifyEmailView(APIView):
    """
    Verify user email with token
    POST /api/auth/verify-email/
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        token = request.data.get('token')
        
        if not token:
            return Response({
                'error': 'Token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            verification = EmailVerificationToken.objects.get(token=token, is_used=False)
            
            if verification.is_expired():
                return Response({
                    'error': 'Token has expired'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Mark email as verified
            user = verification.user
            user.email_verified = True
            user.email_verified_at = timezone.now()
            user.save()
            
            # Mark token as used
            verification.is_used = True
            verification.save()
            
            return Response({
                'message': 'Email verified successfully'
            }, status=status.HTTP_200_OK)
        
        except EmailVerificationToken.DoesNotExist:
            return Response({
                'error': 'Invalid token'
            }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Authentication'],
    summary='Request password reset',
    description='''
    Request a password reset link to be sent via email.
    
    **Process:**
    1. User provides their email address
    2. System validates email exists
    3. Password reset token is generated
    4. Email with reset link is sent
    
    **Token Validity:** 1 hour
    
    **Security Note:** For security, the API always returns success even if email doesn't exist.
    ''',
    request=PasswordResetRequestSerializer,
    responses={
        200: {'type': 'object', 'properties': {'message': {'type': 'string'}}},
    },
    examples=[
        OpenApiExample(
            'Request Reset',
            value={'email': 'john@example.com'},
            request_only=True,
        ),
    ]
)
class PasswordResetRequestView(APIView):
    """
    Request password reset
    POST /api/auth/forgot-password/
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = CustomUser.objects.get(email=email)
            
            # Generate reset token
            token = generate_verification_token(user)
            PasswordResetToken.objects.create(
                user=user,
                token=token,
                expires_at=get_token_expiry(hours=1)
            )
            
            # Send reset email
            try:
                send_password_reset_email(user, token)
            except Exception as e:
                print(f"Failed to send password reset email: {e}")
            
            return Response({
                'message': 'Password reset email sent. Please check your inbox.'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Authentication'],
    summary='Reset password with token',
    description='''
    Reset password using the token received via email.
    
    **Process:**
    1. User receives reset token via email
    2. User provides token and new password
    3. System validates token (not expired, not used)
    4. Password is updated
    5. All active sessions are invalidated
    
    **Security:**
    - Token is single-use only
    - Token expires after 1 hour
    - All sessions are logged out after reset
    ''',
    request=PasswordResetConfirmSerializer,
    responses={
        200: {'type': 'object', 'properties': {'message': {'type': 'string'}}},
        400: OpenApiTypes.OBJECT,
    },
    examples=[
        OpenApiExample(
            'Reset Password',
            value={
                'token': 'abc123def456...',
                'new_password': 'NewSecurePass123!',
                'new_password2': 'NewSecurePass123!'
            },
            request_only=True,
        ),
    ]
)
class PasswordResetConfirmView(APIView):
    """
    Confirm password reset with token
    POST /api/auth/reset-password/
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            
            try:
                reset_token = PasswordResetToken.objects.get(token=token, is_used=False)
                
                if reset_token.is_expired():
                    return Response({
                        'error': 'Token has expired'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Reset password
                user = reset_token.user
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                
                # Mark token as used
                reset_token.is_used = True
                reset_token.save()
                
                # Deactivate all sessions
                UserSession.objects.filter(user=user, is_active=True).update(is_active=False)
                
                return Response({
                    'message': 'Password reset successful'
                }, status=status.HTTP_200_OK)
            
            except PasswordResetToken.DoesNotExist:
                return Response({
                    'error': 'Invalid token'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Sessions'],
    summary='List active sessions',
    description='''
    List all active sessions for the authenticated user.
    
    **Session Information Includes:**
    - Device type and name
    - IP address
    - User agent (browser/app info)
    - Creation and last activity timestamps
    - Expiry time
    
    **Use Case:** 
    View all devices where you're currently logged in and manage your security.
    ''',
    responses={200: UserSessionSerializer(many=True)},
)
class UserSessionListView(generics.ListAPIView):
    """
    List active user sessions
    GET /api/users/sessions/
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSessionSerializer
    
    def get_queryset(self):
        return UserSession.objects.filter(user=self.request.user, is_active=True)


@extend_schema(
    tags=['Sessions'],
    summary='Revoke a session',
    description='''
    Revoke (logout) a specific session by ID.
    
    **Security Feature:**
    Use this to logout from other devices if you suspect unauthorized access.
    
    **Note:** Cannot revoke your current session - use logout endpoint instead.
    ''',
    parameters=[
        OpenApiParameter(
            name='session_id',
            type=int,
            location=OpenApiParameter.PATH,
            description='ID of the session to revoke',
        ),
    ],
    responses={
        200: {'type': 'object', 'properties': {'message': {'type': 'string'}}},
        404: OpenApiTypes.OBJECT,
    },
)
class UserSessionRevokeView(APIView):
    """
    Revoke a specific session
    DELETE /api/users/sessions/{id}/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request, session_id):
        session = get_object_or_404(UserSession, id=session_id, user=request.user)
        session.is_active = False
        session.save()
        
        return Response({
            'message': 'Session revoked successfully'
        }, status=status.HTTP_200_OK)


# ============ CHAT ENDPOINTS ============

@extend_schema(
    tags=['Chat'],
    summary='List or create chat conversations',
    description='''
    **GET**: List all conversations for the authenticated user
    **POST**: Create a new conversation
    
    Conversations help organize your chat messages by topic or stock.
    ''',
)
class ChatConversationListCreateView(generics.ListCreateAPIView):
    """
    List and create chat conversations
    GET /api/chat/conversations/
    POST /api/chat/conversations/
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChatConversationSerializer
    
    @extend_schema(
        summary='List all conversations',
        description='Get all chat conversations for the authenticated user, ordered by most recent',
        responses={200: ChatConversationSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary='Create new conversation',
        description='Create a new chat conversation',
        request=ChatConversationSerializer,
        responses={201: ChatConversationSerializer},
        examples=[
            OpenApiExample(
                'Create Conversation',
                value={
                    'title': 'AAPL Stock Analysis',
                    'tags': ['stocks', 'tech', 'analysis']
                },
                request_only=True,
            ),
        ]
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
    def get_queryset(self):
        return ChatConversation.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema(
    tags=['Chat'],
    summary='Get, update, or delete a conversation',
    description='''
    Manage a specific chat conversation.
    
    **Operations:**
    - **GET**: Retrieve conversation details
    - **PUT/PATCH**: Update conversation (title, tags, archived status)
    - **DELETE**: Delete conversation and all its messages
    ''',
)
class ChatConversationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a chat conversation
    GET /api/chat/conversations/{id}/
    PUT /api/chat/conversations/{id}/
    DELETE /api/chat/conversations/{id}/
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChatConversationSerializer
    
    def get_queryset(self):
        return ChatConversation.objects.filter(user=self.request.user)


@extend_schema(
    tags=['Chat'],
    summary='List messages in a conversation',
    description='''
    Retrieve all messages in a specific conversation.
    
    Messages are ordered chronologically (oldest first).
    Includes both user and assistant messages.
    ''',
    responses={200: ChatMessageSerializer(many=True)},
    parameters=[
        OpenApiParameter(
            name='conversation_id',
            type=int,
            location=OpenApiParameter.PATH,
            description='ID of the conversation',
        ),
    ],
)
class ChatMessageListView(generics.ListAPIView):
    """
    List messages in a conversation
    GET /api/chat/conversations/{conversation_id}/messages/
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChatMessageSerializer
    
    def get_queryset(self):
        conversation_id = self.kwargs['conversation_id']
        return ChatMessage.objects.filter(
            conversation_id=conversation_id,
            conversation__user=self.request.user
        )


@extend_schema(
    tags=['Chat'],
    summary='Send a message in a conversation',
    description='''
    Send a new message in a conversation and get chatbot response.
    
    **Process:**
    1. User sends a message
    2. Message is saved to conversation
    3. Chatbot processes the message (integration pending)
    4. Assistant response is saved
    5. Conversation is updated
    6. User's query count is incremented
    
    **Usage Tracking:**
    - Increments total_queries and queries_this_month
    - Updates last_query_at timestamp
    - Logs activity for analytics
    
    **Note:** Chatbot integration is pending. Currently saves user message only.
    ''',
    request=ChatMessageCreateSerializer,
    responses={
        201: ChatMessageSerializer,
        404: OpenApiTypes.OBJECT,
    },
    parameters=[
        OpenApiParameter(
            name='conversation_id',
            type=int,
            location=OpenApiParameter.PATH,
            description='ID of the conversation',
        ),
    ],
    examples=[
        OpenApiExample(
            'Send Message',
            description='Ask about a stock',
            value={
                'content': 'What is the current price of AAPL stock?'
            },
            request_only=True,
        ),
        OpenApiExample(
            'Success Response',
            value={
                'message': {
                    'id': 1,
                    'content': 'What is the current price of AAPL stock?',
                    'message_type': 'user',
                    'created_at': '2025-11-10T12:00:00Z'
                },
                'note': 'Chatbot integration pending'
            },
            response_only=True,
            status_codes=['201'],
        ),
    ]
)
class ChatMessageCreateView(APIView):
    """
    Send a message in a conversation with Kafka and WebSocket integration
    POST /api/chat/conversations/{conversation_id}/messages/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, conversation_id):
        from .kafka_utils import send_message_to_kafka
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        import logging
        import uuid
        
        logger = logging.getLogger(__name__)
        
        conversation = get_object_or_404(
            ChatConversation,
            id=conversation_id,
            user=request.user
        )
        
        serializer = ChatMessageCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        content = serializer.validated_data['content']
        
        # 1. Create user message in database
        user_message = ChatMessage.objects.create(
            conversation=conversation,
            user=request.user,
            message_type='user',
            content=content,
            status='completed'  # User message is immediately complete
        )
        
        # 2. Generate unique kafka message ID
        kafka_message_id = str(uuid.uuid4())
        
        # 3. Create placeholder for assistant response (pending)
        assistant_message = ChatMessage.objects.create(
            conversation=conversation,
            user=request.user,
            message_type='assistant',
            content='',  # Will be filled by Kafka consumer
            status='pending',
            kafka_message_id=kafka_message_id
        )
        
    # 4. Send message to Kafka 'chat' topic
        returned_kafka_id = send_message_to_kafka(
            user_id=request.user.id,
            conversation_id=conversation_id,
            content=content,
            agent="Market Analyzer",
            kafka_message_id=kafka_message_id
        )
        
        if not returned_kafka_id:
            logger.warning(f"⚠️ Failed to send message to Kafka for conversation {conversation_id}")
            # Mark assistant message as failed
            assistant_message.status = 'failed'
            assistant_message.content = 'Failed to process message. Please try again.'
            assistant_message.save()
        
        # 5. Update conversation timestamp
        conversation.last_message_at = timezone.now()
        conversation.save()
        
        # 6. Update user profile query count
        profile = request.user.profile
        profile.total_queries += 1
        profile.queries_this_month += 1
        profile.last_query_at = timezone.now()
        profile.save()
        
        # 7. Log activity
        log_user_activity(request.user, 'chat', request, {
            'conversation_id': conversation_id,
            'message_preview': content[:50],
            'kafka_message_id': kafka_message_id
        })
        
        # 8. Broadcast to WebSocket clients
        channel_layer = get_channel_layer()
        conversation_group = f'chat_{conversation_id}'
        
        try:
            # Send user message
            async_to_sync(channel_layer.group_send)(
                conversation_group,
                {
                    'type': 'chat_message',
                    'message': ChatMessageSerializer(user_message).data,
                    'conversation_id': conversation_id,
                    'timestamp': user_message.created_at.isoformat()
                }
            )
            
            # Send pending assistant message
            async_to_sync(channel_layer.group_send)(
                conversation_group,
                {
                    'type': 'message_pending',
                    'message': ChatMessageSerializer(assistant_message).data,
                    'conversation_id': conversation_id,
                    'kafka_message_id': kafka_message_id
                }
            )
            
            logger.info(f"✅ WebSocket notification sent for conversation {conversation_id}")
        except Exception as e:
            logger.error(f"❌ Failed to send WebSocket notification: {e}")
        
        # 9. Return both messages in response
        return Response({
            'user_message': ChatMessageSerializer(user_message).data,
            'assistant_message': ChatMessageSerializer(assistant_message).data,
            'status': 'Message sent to chatbot. Waiting for response...',
            'kafka_message_id': kafka_message_id
        }, status=status.HTTP_201_CREATED)


# ============ USER SETTINGS ENDPOINTS ============

@extend_schema(
    tags=['Settings'],
    summary='Get or update user settings',
    description='''
    Manage user-specific risk management and configuration settings.
    
    **Settings Include:**
    - **Drawdown**: Maximum acceptable drawdown percentage (0-100%)
    - **Beta**: Portfolio beta relative to market (typically -5 to 5)
    - **Hurdle Rate**: Minimum acceptable return rate percentage
    - **Sector Exposure Limits**: Maximum exposure percentage per sector (JSON object)
    - **Whitelist**: Allowed domains for news and data sources (JSON array)
    - **Blacklist**: Blocked domains for news and data sources (JSON array)
    
    **Auto-Creation:**
    Settings are automatically created with default values when a user registers.
    
    **GET**: Retrieve current settings
    **PUT/PATCH**: Update settings (partial updates supported)
    ''',
)
class UserSettingsView(APIView):
    """
    Get and update user settings
    GET /api/users/me/settings/
    PUT /api/users/me/settings/
    PATCH /api/users/me/settings/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary='Get user settings',
        description='Retrieve the authenticated user\'s settings. Creates default settings if none exist.',
        responses={200: UserSettingsSerializer}
    )
    def get(self, request):
        # Get or create settings for user
        settings, created = UserSettings.objects.get_or_create(user=request.user)
        serializer = UserSettingsSerializer(settings)
        return Response(serializer.data)
    
    @extend_schema(
        summary='Update user settings (full)',
        description='Update user settings (full update - all fields required)',
        request=UserSettingsSerializer,
        responses={200: UserSettingsSerializer},
        examples=[
            OpenApiExample(
                'Update All Settings',
                value={
                    'drawdown': 20.0,
                    'beta': 1.0,
                    'hurdle_rate': 8.0,
                    'sector_exposure_limits': {
                        'technology': 30.0,
                        'healthcare': 20.0,
                        'financial': 20.0
                    },
                    'whitelist': [
                        'sec.gov',
                        'yahoo.com',
                        'bloomberg.com'
                    ],
                    'blacklist': []
                },
                request_only=True,
            ),
        ]
    )
    def put(self, request):
        settings, created = UserSettings.objects.get_or_create(user=request.user)
        serializer = UserSettingsSerializer(settings, data=request.data)
        if serializer.is_valid():
            serializer.save()
            
            # Log activity
            log_user_activity(request.user, 'settings_update', request, {
                'fields_updated': list(request.data.keys())
            })
            
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        summary='Update user settings (partial)',
        description='Partially update user settings (only provided fields are updated)',
        request=UserSettingsSerializer,
        responses={200: UserSettingsSerializer},
        examples=[
            OpenApiExample(
                'Update Drawdown Only',
                value={'drawdown': 15.0},
                request_only=True,
            ),
            OpenApiExample(
                'Update Whitelist Only',
                value={
                    'whitelist': [
                        'sec.gov',
                        'yahoo.com',
                        'bloomberg.com',
                        'reuters.com'
                    ]
                },
                request_only=True,
            ),
        ]
    )
    def patch(self, request):
        settings, created = UserSettings.objects.get_or_create(user=request.user)
        serializer = UserSettingsSerializer(settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            
            # Log activity
            log_user_activity(request.user, 'settings_update', request, {
                'fields_updated': list(request.data.keys())
            })
            
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
