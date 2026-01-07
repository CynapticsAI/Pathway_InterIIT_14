#!/usr/bin/env python
"""
Test Email Notification System

This script tests the email notification system by creating sample notifications
and sending emails.

Usage:
    python test_email_notifications.py
"""

import os
import django
import sys

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from api.models import Portfolio, Stock, Notification
from api.services import NotificationService
from api.email_service import EmailNotificationService

User = get_user_model()


def test_email_system():
    """Test the email notification system"""
    
    print("=" * 70)
    print("EMAIL NOTIFICATION SYSTEM TEST")
    print("=" * 70)
    
    # 1. Get or create test user
    print("\n1. Setting up test user...")
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✅ Created test user: {user.username}")
    else:
        print(f"✅ Using existing user: {user.username}")
    
    print(f"   - Email: {user.email}")
    
    # 2. Create portfolio and stock
    print("\n2. Setting up portfolio...")
    portfolio, _ = Portfolio.objects.get_or_create(user=user)
    stock, created = Stock.objects.get_or_create(
        portfolio=portfolio,
        symbol='AAPL',
        defaults={
            'quantity': 10,
            'cost_basis': 150.00
        }
    )
    if created:
        print(f"✅ Added AAPL to portfolio")
    else:
        print(f"✅ AAPL already in portfolio")
    
    # 3. Test News Notification Email
    print("\n3. Testing News Notification Email...")
    news_data = {
        'headline': 'Apple Announces Revolutionary New Product Line',
        'sentiment': 'positive',
        'source': 'Reuters',
        'url': 'https://example.com/apple-news',
        'summary': 'Apple Inc. has unveiled a groundbreaking new product that could reshape the industry.',
    }
    
    try:
        notifications = NotificationService.create_news_notification(news_data, 'AAPL')
        if notifications:
            print(f"✅ Created {len(notifications)} news notification(s)")
            print(f"   - Title: {notifications[0].title}")
            print(f"   - Type: {notifications[0].notification_type}")
            print(f"   - Priority: {notifications[0].priority}")
            print(f"   ✉️  Email sent to: {user.email}")
        else:
            print("⚠️  No notifications created (user may not have AAPL in portfolio)")
    except Exception as e:
        print(f"❌ Error creating news notification: {e}")
    
    # 4. Test Volume Spike Notification Email
    print("\n4. Testing Volume Spike Notification Email...")
    spike_data = {
        'spike_percentage': 125.5,
        'current_volume': 50000000,
        'average_volume': 22000000,
        'volume_ratio': 2.27,
        'current_price': 178.50,
        'price_change_percentage': 3.25,
    }
    
    try:
        notifications = NotificationService.create_volume_spike_notification(spike_data, 'AAPL')
        if notifications:
            print(f"✅ Created {len(notifications)} volume spike notification(s)")
            print(f"   - Title: {notifications[0].title}")
            print(f"   - Type: {notifications[0].notification_type}")
            print(f"   - Priority: {notifications[0].priority}")
            print(f"   ✉️  Email sent to: {user.email}")
        else:
            print("⚠️  No notifications created (user may not have AAPL in portfolio)")
    except Exception as e:
        print(f"❌ Error creating volume spike notification: {e}")
    
    # 5. Test Direct Email Sending
    print("\n5. Testing Direct Email Service...")
    notification = Notification.objects.create(
        user=user,
        notification_type='NEWS',
        symbol='TSLA',
        title='Tesla Stock Surges on Strong Delivery Numbers',
        message='Tesla reported record vehicle deliveries, beating analyst expectations.',
        data={
            'headline': 'Tesla Reports Record Q4 Deliveries',
            'sentiment': 'very_positive',
            'source': 'Bloomberg',
        },
        timestamp=timezone.now(),
        priority='HIGH',
        status='UNREAD'
    )
    
    try:
        success = EmailNotificationService.send_notification_email(notification, user)
        if success:
            print(f"✅ Direct email sent successfully")
            print(f"   - Notification ID: {notification.id}")
            print(f"   - Subject: 📰 News Alert: TSLA")
        else:
            print(f"❌ Failed to send email")
    except Exception as e:
        print(f"❌ Error sending email: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"✅ User: {user.username} ({user.email})")
    print(f"✅ Portfolio: {portfolio.stocks.count()} stock(s)")
    print(f"✅ Total Notifications: {Notification.objects.filter(user=user).count()}")
    print("\n📧 EMAIL CONFIGURATION:")
    print(f"   Backend: Console (emails printed to terminal)")
    print(f"   From: noreply@pway-stock.com")
    print(f"   To: {user.email}")
    print("\n💡 TIP: Check your terminal output for the email HTML content!")
    print("💡 For production, configure SMTP settings in settings.py")
    print("\n" + "=" * 70)


if __name__ == '__main__':
    test_email_system()
