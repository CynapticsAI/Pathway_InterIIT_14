from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import (
    CustomUser, UserProfile, ChatConversation, ChatMessage,
    UserSession, EmailVerificationToken, PasswordResetToken, UserActivity, UserSettings
)


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    """
    Admin configuration for CustomUser
    """
    list_display = ('email', 'username', 'first_name', 'last_name', 'email_verified', 'is_active', 'created_at')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'email_verified', 'created_at')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'bio', 'profile_picture')}),
        ('Email Verification', {'fields': ('email_verified', 'email_verified_at')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'date_joined', 'last_login')
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin configuration for UserProfile
    """
    list_display = ('user', 'subscription_tier', 'subscription_status', 'total_queries', 'queries_this_month', 'created_at')
    list_filter = ('subscription_tier', 'subscription_status', 'notifications_enabled')
    search_fields = ('user__email', 'user__username')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Subscription', {'fields': ('subscription_tier', 'subscription_status', 'subscription_start_date', 'subscription_end_date')}),
        ('Preferences', {'fields': ('favorite_stocks', 'watchlist', 'notifications_enabled')}),
        ('Usage', {'fields': ('total_queries', 'queries_this_month', 'last_query_at')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ChatConversation)
class ChatConversationAdmin(admin.ModelAdmin):
    """
    Admin configuration for ChatConversation
    """
    list_display = ('title', 'user', 'is_pinned', 'is_archived', 'message_count', 'last_message_at', 'created_at')
    list_filter = ('is_archived', 'is_pinned', 'created_at')
    search_fields = ('title', 'user__email', 'user__username')
    ordering = ('-last_message_at',)
    
    readonly_fields = ('created_at', 'updated_at')
    
    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    """
    Admin configuration for ChatMessage
    """
    list_display = ('short_content', 'message_type', 'user', 'conversation', 'rating', 'created_at')
    list_filter = ('message_type', 'is_helpful', 'created_at')
    search_fields = ('content', 'user__email', 'conversation__title')
    ordering = ('-created_at',)
    
    readonly_fields = ('created_at', 'updated_at')
    
    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    short_content.short_description = 'Content'


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """
    Admin configuration for UserSession
    """
    list_display = ('user', 'device_type', 'ip_address', 'is_active', 'status_badge', 'created_at', 'expires_at')
    list_filter = ('is_active', 'device_type', 'created_at')
    search_fields = ('user__email', 'ip_address', 'device_name')
    ordering = ('-created_at',)
    
    readonly_fields = ('created_at', 'last_activity_at')
    
    def status_badge(self, obj):
        if obj.is_expired():
            color = 'red'
            status = 'Expired'
        elif obj.is_active:
            color = 'green'
            status = 'Active'
        else:
            color = 'gray'
            status = 'Inactive'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, status
        )
    status_badge.short_description = 'Status'


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    """
    Admin configuration for EmailVerificationToken
    """
    list_display = ('email', 'user', 'is_used', 'status_badge', 'created_at', 'expires_at')
    list_filter = ('is_used', 'created_at')
    search_fields = ('email', 'user__email', 'token')
    ordering = ('-created_at',)
    
    readonly_fields = ('created_at',)
    
    def status_badge(self, obj):
        if obj.is_used:
            color = 'gray'
            status = 'Used'
        elif obj.is_expired():
            color = 'red'
            status = 'Expired'
        else:
            color = 'green'
            status = 'Valid'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, status
        )
    status_badge.short_description = 'Status'


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    """
    Admin configuration for PasswordResetToken
    """
    list_display = ('user', 'is_used', 'status_badge', 'created_at', 'expires_at')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__email', 'token')
    ordering = ('-created_at',)
    
    readonly_fields = ('created_at',)
    
    def status_badge(self, obj):
        if obj.is_used:
            color = 'gray'
            status = 'Used'
        elif obj.is_expired():
            color = 'red'
            status = 'Expired'
        else:
            color = 'green'
            status = 'Valid'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, status
        )
    status_badge.short_description = 'Status'


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    """
    Admin configuration for UserActivity
    """
    list_display = ('user', 'activity_type', 'ip_address', 'timestamp')
    list_filter = ('activity_type', 'timestamp')
    search_fields = ('user__email', 'ip_address')
    ordering = ('-timestamp',)
    
    readonly_fields = ('timestamp',)


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    """
    Admin configuration for UserSettings
    """
    list_display = ('user', 'drawdown', 'beta', 'hurdle_rate', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__email', 'user__username')
    ordering = ('-updated_at',)
    
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Risk Parameters', {
            'fields': ('drawdown', 'beta', 'hurdle_rate'),
            'description': 'Risk management and performance metrics'
        }),
        ('Sector Limits', {
            'fields': ('sector_exposure_limits',),
            'description': 'Maximum exposure percentage per sector',
            'classes': ('collapse',)
        }),
        ('Domain Filters', {
            'fields': ('whitelist', 'blacklist'),
            'description': 'Allowed and blocked domains for news sources',
            'classes': ('collapse',)
        }),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ('created_at', 'updated_at')

