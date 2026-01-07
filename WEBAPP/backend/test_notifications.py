"""
Test script for the notification system

This script tests:
1. Creating a notification
2. REST API endpoints
3. WebSocket connectivity (manual test)
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from api.models import Portfolio, Stock, Notification
from api.services import NotificationService
from datetime import datetime
from django.utils import timezone

User = get_user_model()

def test_notification_system():
    """Test the notification system"""
    
    print("=" * 60)
    print("NOTIFICATION SYSTEM TEST")
    print("=" * 60)
    
    # 1. Get or create a test user
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
        print(f"✅ Using existing test user: {user.username}")
    
    # 2. Get or create portfolio for the user
    print("\n2. Setting up test portfolio...")
    portfolio, created = Portfolio.objects.get_or_create(
        user=user,
        defaults={'name': 'Test Portfolio'}
    )
    print(f"✅ Portfolio: {portfolio.name}")
    
    # 3. Add test stocks to portfolio
    print("\n3. Adding test stocks to portfolio...")
    test_symbols = ['AAPL', 'GOOGL', 'MSFT']
    for symbol in test_symbols:
        stock, created = Stock.objects.get_or_create(
            portfolio=portfolio,
            symbol=symbol,
            defaults={
                'quantity': 10,
                'cost_basis': 100.00
            }
        )
        status_text = "Added" if created else "Already exists"
        print(f"   {status_text}: {symbol}")
    
    print(f"✅ Portfolio has {portfolio.stocks.count()} stocks")
    
    # 4. Test creating a news notification
    print("\n4. Testing news notification creation...")
    news_data = {
        'headline': 'Apple Announces New Product Line',
        'sentiment': 'positive',
        'source': 'Test News',
        'url': 'https://example.com/news/1',
        'summary': 'Apple has announced an exciting new product lineup.',
        'timestamp': timezone.now().isoformat(),
    }
    
    notifications = NotificationService.create_news_notification(news_data, 'AAPL')
    print(f"✅ Created {len(notifications)} news notification(s)")
    
    if notifications:
        notif = notifications[0]
        print(f"   - ID: {notif.id}")
        print(f"   - User: {notif.user.username}")
        print(f"   - Type: {notif.notification_type}")
        print(f"   - Symbol: {notif.symbol}")
        print(f"   - Title: {notif.title}")
        print(f"   - Priority: {notif.priority}")
        print(f"   - Status: {notif.status}")
    
    # 5. Test creating a volume spike notification
    print("\n5. Testing volume spike notification creation...")
    spike_data = {
        'symbol': 'GOOGL',
        'spike_percentage': 75.5,
        'current_volume': 1500000,
        'average_volume': 850000,
        'price_change_percentage': 2.3,
        'current_price': 142.50,
        'timestamp': timezone.now().isoformat(),
    }
    
    notifications = NotificationService.create_volume_spike_notification(spike_data, 'GOOGL')
    print(f"✅ Created {len(notifications)} volume spike notification(s)")
    
    if notifications:
        notif = notifications[0]
        print(f"   - ID: {notif.id}")
        print(f"   - User: {notif.user.username}")
        print(f"   - Type: {notif.notification_type}")
        print(f"   - Symbol: {notif.symbol}")
        print(f"   - Title: {notif.title}")
        print(f"   - Message: {notif.message}")
        print(f"   - Priority: {notif.priority}")
    
    # 6. Test NotificationService methods
    print("\n6. Testing NotificationService methods...")
    unread_count = NotificationService.get_unread_count(user)
    print(f"✅ Unread notifications: {unread_count}")
    
    # 7. List all notifications for the user
    print("\n7. Listing all notifications for the user...")
    all_notifications = Notification.objects.filter(user=user).order_by('-created_at')
    print(f"✅ Total notifications: {all_notifications.count()}")
    
    for i, notif in enumerate(all_notifications[:5], 1):
        print(f"   {i}. [{notif.notification_type}] {notif.symbol}: {notif.title} ({notif.status})")
    
    # 8. Test marking notifications as read
    print("\n8. Testing mark as read...")
    if all_notifications.filter(status='UNREAD').exists():
        first_unread = all_notifications.filter(status='UNREAD').first()
        print(f"   Marking notification {first_unread.id} as read...")
        first_unread.mark_as_read()
        print(f"✅ Notification marked as read")
        print(f"   New unread count: {NotificationService.get_unread_count(user)}")
    
    # 9. Display API endpoints
    print("\n9. API Endpoints (for manual testing):")
    print("   =" * 30)
    print("   GET    /api/notifications/                    - List notifications")
    print("   GET    /api/notifications/unread_count/       - Get unread count")
    print("   GET    /api/notifications/recent/             - Get recent notifications")
    print("   GET    /api/notifications/{id}/               - Get notification detail")
    print("   POST   /api/notifications/{id}/mark_read/     - Mark as read")
    print("   POST   /api/notifications/mark_all_read/      - Mark all as read")
    print("   DELETE /api/notifications/{id}/               - Archive notification")
    print("   GET    /api/notification-preferences/me/      - Get preferences")
    print("   PATCH  /api/notification-preferences/{id}/    - Update preferences")
    
    # 10. Display WebSocket endpoint
    print("\n10. WebSocket Endpoint:")
    print("   =" * 30)
    print("   ws://localhost:8000/ws/notifications/")
    print("   (Requires authentication)")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST COMPLETE!")
    print("=" * 60)
    print(f"✅ Test user: {user.username}")
    print(f"✅ Portfolio stocks: {portfolio.stocks.count()}")
    print(f"✅ Total notifications: {all_notifications.count()}")
    print(f"✅ Unread notifications: {NotificationService.get_unread_count(user)}")
    print("\nNext Steps:")
    print("1. Start the Django server: python manage.py runserver")
    print("2. Test REST API endpoints using curl or Postman")
    print("3. Test WebSocket connection from frontend")
    print("4. Start Kafka consumers to test real-time notifications")
    print("=" * 60)


if __name__ == '__main__':
    try:
        test_notification_system()
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
