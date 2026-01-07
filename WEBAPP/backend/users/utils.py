import secrets
import hashlib
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings


def generate_token(length=32):
    """
    Generate a secure random token
    """
    return secrets.token_urlsafe(length)


def generate_verification_token(user):
    """
    Generate a unique verification token based on user data
    """
    timestamp = str(timezone.now().timestamp())
    raw_token = f"{user.email}{user.id}{timestamp}{secrets.token_urlsafe(16)}"
    return hashlib.sha256(raw_token.encode()).hexdigest()


def get_token_expiry(hours=24):
    """
    Get expiry datetime for tokens
    """
    return timezone.now() + timedelta(hours=hours)


def send_verification_email(user, token):
    """
    Send email verification email
    """
    verification_link = f"{settings.FRONTEND_URL}/verify-email?token={token}" if hasattr(settings, 'FRONTEND_URL') else f"http://localhost:3000/verify-email?token={token}"
    
    subject = 'Verify your email - Pway Stock'
    message = f"""
    Hi {user.first_name or user.username},
    
    Thank you for registering with Pway Stock!
    
    Please verify your email address by clicking the link below:
    {verification_link}
    
    This link will expire in 24 hours.
    
    If you didn't create an account, please ignore this email.
    
    Best regards,
    Pway Stock Team
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


def send_password_reset_email(user, token):
    """
    Send password reset email
    """
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}" if hasattr(settings, 'FRONTEND_URL') else f"http://localhost:3000/reset-password?token={token}"
    
    subject = 'Reset your password - Pway Stock'
    message = f"""
    Hi {user.first_name or user.username},
    
    We received a request to reset your password.
    
    Click the link below to reset your password:
    {reset_link}
    
    This link will expire in 1 hour.
    
    If you didn't request a password reset, please ignore this email.
    
    Best regards,
    Pway Stock Team
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


def get_client_ip(request):
    """
    Get client IP address from request
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_device_info(request):
    """
    Extract device information from request
    """
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    device_type = 'desktop'
    if 'mobile' in user_agent.lower():
        device_type = 'mobile'
    elif 'tablet' in user_agent.lower():
        device_type = 'tablet'
    
    return {
        'device_type': device_type,
        'user_agent': user_agent,
        'ip_address': get_client_ip(request)
    }


def create_user_session(user, request, access_token, refresh_token=None):
    """
    Create a new user session
    """
    from .models import UserSession
    
    device_info = get_device_info(request)
    
    session = UserSession.objects.create(
        user=user,
        session_token=str(access_token),
        refresh_token=str(refresh_token) if refresh_token else None,
        device_type=device_info['device_type'],
        ip_address=device_info['ip_address'],
        user_agent=device_info['user_agent'],
        expires_at=get_token_expiry(hours=1)  # Access token expiry
    )
    
    return session


def log_user_activity(user, activity_type, request, additional_data=None):
    """
    Log user activity
    """
    from .models import UserActivity
    
    activity_data = additional_data or {}
    device_info = get_device_info(request)
    
    UserActivity.objects.create(
        user=user,
        activity_type=activity_type,
        activity_data=activity_data,
        ip_address=device_info['ip_address'],
        user_agent=device_info['user_agent']
    )
