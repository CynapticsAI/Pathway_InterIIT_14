from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema_field
from .models import CustomUser, UserProfile, ChatConversation, ChatMessage, UserSession, UserSettings


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for UserProfile
    """
    class Meta:
        model = UserProfile
        fields = [
            'subscription_tier', 'subscription_status', 'subscription_start_date',
            'subscription_end_date', 'favorite_stocks', 'watchlist',
            'notifications_enabled', 'total_queries', 'queries_this_month',
            'last_query_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['total_queries', 'queries_this_month', 'last_query_at', 'created_at', 'updated_at']


class CustomUserSerializer(serializers.ModelSerializer):
    """
    Serializer for CustomUser model
    """
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'bio', 'profile_picture', 'email_verified',
            'email_verified_at', 'created_at', 'updated_at', 'profile'
        ]
        read_only_fields = ['id', 'email_verified', 'email_verified_at', 'created_at', 'updated_at']
        extra_kwargs = {
            'email': {'required': True},
        }


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, label="Confirm Password")
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name']
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        # Check if email already exists
        if CustomUser.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "A user with this email already exists."})
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        # Try to find user by email
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError({"email": "Invalid email or password."})
        
        # Authenticate using username (Django default)
        user = authenticate(username=user.username, password=password)
        
        if user is None:
            raise serializers.ValidationError({"password": "Invalid email or password."})
        
        if not user.is_active:
            raise serializers.ValidationError({"detail": "User account is disabled."})
        
        attrs['user'] = user
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change
    """
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    new_password2 = serializers.CharField(write_only=True, required=True, label="Confirm New Password")
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs


class ChatConversationSerializer(serializers.ModelSerializer):
    """
    Serializer for ChatConversation
    """
    message_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatConversation
        fields = [
            'id', 'title', 'is_archived', 'is_pinned', 'tags',
            'message_count', 'created_at', 'updated_at', 'last_message_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_message_at']
    
    @extend_schema_field(serializers.IntegerField)
    def get_message_count(self, obj) -> int:
        return obj.messages.count()


class ChatMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for ChatMessage
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = ChatMessage
        fields = [
            'id', 'conversation', 'user', 'user_email', 'message_type',
            'content', 'metadata', 'tokens_used', 'response_time_ms',
            'is_helpful', 'rating', 'status', 'kafka_message_id', 'agent_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'user_email', 'created_at', 'updated_at']


class ChatMessageCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating chat messages (from user)
    """
    class Meta:
        model = ChatMessage
        fields = ['content']


class UserSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for UserSession
    """
    is_current = serializers.SerializerMethodField()
    
    class Meta:
        model = UserSession
        fields = [
            'id', 'device_type', 'device_name', 'ip_address',
            'is_active', 'is_current', 'created_at', 'last_activity_at', 'expires_at'
        ]
        read_only_fields = ['id', 'created_at', 'last_activity_at']
    
    @extend_schema_field(serializers.BooleanField)
    def get_is_current(self, obj) -> bool:
        request = self.context.get('request')
        if request and hasattr(request, 'auth'):
            # Check if this session matches the current token
            return obj.session_token == str(request.auth)
        return False


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for password reset request
    """
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        if not CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user found with this email address.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for password reset confirmation
    """
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    new_password2 = serializers.CharField(write_only=True, required=True, label="Confirm New Password")
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs


class EmailVerificationSerializer(serializers.Serializer):
    """
    Serializer for email verification
    """
    token = serializers.CharField(required=True, help_text='Verification token from email')


class ChatbotMessageSerializer(serializers.Serializer):
    """
    Serializer for chatbot test endpoint
    """
    message = serializers.CharField(required=True, help_text='Message to send to the chatbot')


class UserSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for UserSettings
    """
    class Meta:
        model = UserSettings
        fields = [
            'drawdown',
            'beta',
            'hurdle_rate',
            'sector_exposure_limits',
            'whitelist',
            'blacklist',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_drawdown(self, value):
        """Validate drawdown is between 0 and 100"""
        if value < 0 or value > 100:
            raise serializers.ValidationError("Drawdown must be between 0 and 100")
        return value
    
    def validate_beta(self, value):
        """Validate beta is reasonable"""
        if value < -5 or value > 5:
            raise serializers.ValidationError("Beta must be between -5 and 5")
        return value
    
    def validate_hurdle_rate(self, value):
        """Validate hurdle rate is reasonable"""
        if value < -100 or value > 1000:
            raise serializers.ValidationError("Hurdle rate must be between -100 and 1000")
        return value
    
    def validate_sector_exposure_limits(self, value):
        """Validate sector exposure limits structure"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Sector exposure limits must be a valid JSON object")
        
        # Validate each sector limit is a number
        for sector, limit in value.items():
            try:
                limit_float = float(limit)
                if limit_float < 0 or limit_float > 100:
                    raise serializers.ValidationError(f"Sector '{sector}' limit must be between 0 and 100")
            except (ValueError, TypeError):
                raise serializers.ValidationError(f"Sector '{sector}' limit must be a number")
        
        return value
    
    def validate_whitelist(self, value):
        """Validate whitelist structure"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Whitelist must be a valid JSON array")
        
        for domain in value:
            if not isinstance(domain, str):
                raise serializers.ValidationError("All whitelist entries must be strings")
        
        return value
    
    def validate_blacklist(self, value):
        """Validate blacklist structure"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Blacklist must be a valid JSON array")
        
        for domain in value:
            if not isinstance(domain, str):
                raise serializers.ValidationError("All blacklist entries must be strings")
        
        return value
