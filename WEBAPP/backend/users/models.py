from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class CustomUser(AbstractUser):
    """
    Custom User model extending Django's AbstractUser
    Only essential fields included
    """
    # Email is required and unique
    email = models.EmailField(unique=True)
    
    # Optional profile fields
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    
    # Email verification
    email_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.email


class UserProfile(models.Model):
    """
    Extended user profile for app-specific settings
    """
    SUBSCRIPTION_TIERS = [
        ('free', 'Free'),
        ('basic', 'Basic'),
        ('premium', 'Premium'),
    ]
    
    SUBSCRIPTION_STATUS = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('trial', 'Trial'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    
    # Subscription
    subscription_tier = models.CharField(max_length=20, choices=SUBSCRIPTION_TIERS, default='free')
    subscription_status = models.CharField(max_length=20, choices=SUBSCRIPTION_STATUS, default='active')
    subscription_start_date = models.DateTimeField(blank=True, null=True)
    subscription_end_date = models.DateTimeField(blank=True, null=True)
    
    # Stock Preferences (stored as JSON)
    favorite_stocks = models.JSONField(default=list, blank=True)
    watchlist = models.JSONField(default=list, blank=True)
    
    # Chat Preferences
    notifications_enabled = models.BooleanField(default=True)
    
    # Usage tracking
    total_queries = models.IntegerField(default=0)
    queries_this_month = models.IntegerField(default=0)
    last_query_at = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
    
    def __str__(self):
        return f"Profile of {self.user.email}"


class ChatConversation(models.Model):
    """
    Chat conversation for organizing messages
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=255, default='New Conversation')
    
    # Organization
    is_archived = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    tags = models.JSONField(default=list, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'chat_conversations'
        ordering = ['-last_message_at']
        indexes = [
            models.Index(fields=['user', '-last_message_at']),
            models.Index(fields=['user', 'is_archived']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"


class ChatMessage(models.Model):
    """
    Individual chat messages
    """
    MESSAGE_TYPES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]
    
    MESSAGE_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    conversation = models.ForeignKey(ChatConversation, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='messages')
    
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES)
    content = models.TextField()
    
    # Kafka integration fields
    kafka_message_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    status = models.CharField(max_length=20, choices=MESSAGE_STATUS, default='completed')
    agent_name = models.CharField(max_length=100, blank=True, null=True)
    
    # Metadata (stocks mentioned, sentiment, etc.)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Analytics (optional)
    tokens_used = models.IntegerField(default=0, blank=True)
    response_time_ms = models.IntegerField(default=0, blank=True)
    
    # Feedback (optional)
    is_helpful = models.BooleanField(default=True, blank=True, null=True)
    rating = models.IntegerField(blank=True, null=True)  # 1-5 stars
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chat_messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.message_type}: {self.content[:50]}..."


class UserSession(models.Model):
    """
    Track active user sessions for security
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sessions')
    
    session_token = models.CharField(max_length=255, unique=True)
    refresh_token = models.CharField(max_length=255, unique=True, blank=True, null=True)
    
    # Device info
    device_type = models.CharField(max_length=50, blank=True, null=True)
    device_name = models.CharField(max_length=100, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    
    # Session state
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField()
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_sessions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['session_token']),
        ]
    
    def __str__(self):
        return f"Session for {self.user.email}"
    
    def is_expired(self):
        return timezone.now() > self.expires_at


class EmailVerificationToken(models.Model):
    """
    Tokens for email verification
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='verification_tokens')
    token = models.CharField(max_length=255, unique=True)
    email = models.EmailField()
    
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'email_verification_tokens'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Verification token for {self.email}"
    
    def is_expired(self):
        return timezone.now() > self.expires_at


class PasswordResetToken(models.Model):
    """
    Tokens for password reset
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=255, unique=True)
    
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'password_reset_tokens'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Password reset token for {self.user.email}"
    
    def is_expired(self):
        return timezone.now() > self.expires_at


class UserActivity(models.Model):
    """
    Log user activities for analytics and security
    """
    ACTIVITY_TYPES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('query', 'Query'),
        ('chat', 'Chat'),
        ('chart_view', 'Chart View'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    activity_data = models.JSONField(default=dict, blank=True)
    
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_activities'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['activity_type', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.activity_type}"


def get_default_whitelist():
    """Default whitelist domains"""
    return [
        "sec.gov",
        "irs.gov",
        "yahoo.com",
        "bloomberg.com",
        "reuters.com",
        "cnbc.com",
        "marketwatch.com",
        "investopedia.com",
        "ft.com",
        "morningstar.com",
        "nasdaq.com",
        "nyse.com",
        "stlouisfed.org",
        "bea.gov",
        "home.treasury.gov",
        "spglobal.com",
        "moodys.com",
        "koyfin.com",
        "tickertape.in"
    ]


def get_default_blacklist():
    """Default blacklist domains"""
    return []


def get_default_sector_limits():
    """Default sector exposure limits"""
    return {
        "technology": 30.0,
        "healthcare": 20.0,
        "financial": 20.0,
        "consumer": 15.0,
        "industrial": 15.0,
        "energy": 10.0,
        "utilities": 10.0,
        "real_estate": 10.0,
        "materials": 10.0,
        "communication": 15.0,
        "consumer_staples": 15.0
    }


class UserSettings(models.Model):
    """
    User-specific risk management and configuration settings
    OneToOne relationship with CustomUser
    """
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='settings',
        primary_key=True
    )
    
    # Risk Management Parameters (Percentages)
    drawdown = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=20.0,
        help_text="Maximum acceptable drawdown percentage (e.g., 20.0 for 20%)"
    )
    beta = models.DecimalField(
        max_digits=4, 
        decimal_places=2, 
        default=1.0,
        help_text="Portfolio beta relative to market (e.g., 1.0 for market neutral)"
    )
    hurdle_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=8.0,
        help_text="Minimum acceptable return rate percentage (e.g., 8.0 for 8%)"
    )
    
    # Sector Exposure Limits (JSON)
    sector_exposure_limits = models.JSONField(
        default=get_default_sector_limits,
        help_text="Maximum exposure percentage per sector"
    )
    
    # Domain Whitelists/Blacklists (JSON)
    whitelist = models.JSONField(
        default=get_default_whitelist,
        help_text="Allowed domains for news and data sources"
    )
    blacklist = models.JSONField(
        default=get_default_blacklist,
        help_text="Blocked domains for news and data sources"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_settings'
        verbose_name = 'User Settings'
        verbose_name_plural = 'User Settings'
    
    def __str__(self):
        return f"Settings for {self.user.email}"
    
    def clean(self):
        """Validate settings values"""
        from django.core.exceptions import ValidationError
        
        # Validate drawdown (0-100%)
        if self.drawdown < 0 or self.drawdown > 100:
            raise ValidationError({'drawdown': 'Drawdown must be between 0 and 100'})
        
        # Validate beta (typically -5 to 5)
        if self.beta < -5 or self.beta > 5:
            raise ValidationError({'beta': 'Beta must be between -5 and 5'})
        
        # Validate hurdle rate (-100 to 1000%)
        if self.hurdle_rate < -100 or self.hurdle_rate > 1000:
            raise ValidationError({'hurdle_rate': 'Hurdle rate must be between -100 and 1000'})
        
        # Validate sector limits are dictionaries
        if not isinstance(self.sector_exposure_limits, dict):
            raise ValidationError({'sector_exposure_limits': 'Must be a valid JSON object'})
        
        # Validate whitelist and blacklist are lists
        if not isinstance(self.whitelist, list):
            raise ValidationError({'whitelist': 'Must be a valid JSON array'})
        if not isinstance(self.blacklist, list):
            raise ValidationError({'blacklist': 'Must be a valid JSON array'})
