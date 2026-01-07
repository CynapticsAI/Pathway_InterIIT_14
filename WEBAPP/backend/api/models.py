from django.db import models
from django.utils import timezone
from django.conf import settings


class MarketBreadth(models.Model):
    """
    Market breadth data from Kafka topic: market_breadth
    Tracks advancing, declining, and unchanged stocks
    """
    timestamp = models.DateTimeField(db_index=True)
    advancing_stocks = models.IntegerField()
    declining_stocks = models.IntegerField()
    unchanged_stocks = models.IntegerField()
    total_stocks = models.IntegerField()
    advance_decline_line = models.IntegerField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "Market Breadth Data"
        indexes = [
            models.Index(fields=['-timestamp']),
        ]
    
    def __str__(self):
        return f"Market Breadth at {self.timestamp}"


class StockTick(models.Model):
    """
    Raw stock tick data from Kafka topic: stock_data
    Real-time price and volume updates
    """
    symbol = models.CharField(max_length=10, db_index=True)
    price = models.DecimalField(max_digits=12, decimal_places=4)
    volume = models.DecimalField(max_digits=20, decimal_places=2)
    timestamp = models.DateTimeField(db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "Stock Ticks"
        indexes = [
            models.Index(fields=['symbol', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.symbol} @ {self.price} ({self.timestamp})"


class PnLData(models.Model):
    """
    Profit and Loss data from Kafka topic: pnl
    Portfolio P&L calculations
    """
    timestamp = models.DateTimeField(db_index=True)
    total_pnl = models.DecimalField(max_digits=20, decimal_places=2)
    
    # Store additional data as JSON
    details = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "P&L Data"
        indexes = [
            models.Index(fields=['-timestamp']),
        ]
    
    def __str__(self):
        return f"P&L: {self.total_pnl} at {self.timestamp}"


class SarimaxForecast(models.Model):
    """
    SARIMAX forecast data from Kafka topic: sarimax_forecast
    Time series predictions for stocks
    """
    symbol = models.CharField(max_length=10, db_index=True)
    timestamp = models.DateTimeField(db_index=True)
    
    # Forecast data stored as JSON
    forecast_data = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "SARIMAX Forecasts"
        indexes = [
            models.Index(fields=['symbol', '-timestamp']),
        ]
    
    def __str__(self):
        return f"SARIMAX Forecast for {self.symbol} at {self.timestamp}"


class VolumeSpike(models.Model):
    """
    Volume spike detection data from Kafka topic: spike_detector
    Alerts for unusual volume activity
    """
    symbol = models.CharField(max_length=10, db_index=True)
    timestamp = models.DateTimeField(db_index=True)
    
    # Spike detection data
    spike_data = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "Volume Spikes"
        indexes = [
            models.Index(fields=['symbol', '-timestamp']),
        ]
    
    def __str__(self):
        return f"Volume Spike: {self.symbol} at {self.timestamp}"


class NewsData(models.Model):
    """
    News data from Kafka topic: news
    Financial news and sentiment analysis
    """
    timestamp = models.DateTimeField(db_index=True)
    
    # News content and metadata
    news_data = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "News Data"
        indexes = [
            models.Index(fields=['-timestamp']),
        ]
    
    def __str__(self):
        return f"News at {self.timestamp}"


class Portfolio(models.Model):
    """
    Portfolio model - One portfolio per user
    Container for user's stock holdings
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='portfolio'
    )
    name = models.CharField(max_length=255, default='My Portfolio')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Portfolios"
    
    def __str__(self):
        return f"{self.user.username}'s Portfolio"
    
    @property
    def total_stocks(self):
        """Return count of stocks in portfolio"""
        return self.stocks.count()


class Stock(models.Model):
    """
    Stock model - Many stocks belong to one portfolio
    Represents individual stock holdings with quantity and cost basis
    """
    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.CASCADE,
        related_name='stocks'
    )
    symbol = models.CharField(max_length=10, db_index=True)
    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        help_text="Number of shares owned (supports fractional shares)"
    )
    cost_basis = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Average purchase price per share"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['symbol']
        verbose_name_plural = "Stocks"
        constraints = [
            models.UniqueConstraint(
                fields=['portfolio', 'symbol'],
                name='unique_portfolio_symbol'
            )
        ]
        indexes = [
            models.Index(fields=['portfolio', 'symbol']),
            models.Index(fields=['symbol']),
        ]
    
    def __str__(self):
        return f"{self.symbol} ({self.quantity} shares)"
    
    @property
    def total_cost(self):
        """Calculate total investment cost"""
        if self.quantity is None or self.cost_basis is None:
            return None
        return self.quantity * self.cost_basis


class Notification(models.Model):
    """
    Notification model for storing user alerts
    Tracks news and volume spike notifications for stocks in user portfolios
    """
    NOTIFICATION_TYPES = [
        ('NEWS', 'News Alert'),
        ('VOLUME_SPIKE', 'Volume Spike Alert'),
    ]
    
    STATUS_CHOICES = [
        ('UNREAD', 'Unread'),
        ('READ', 'Read'),
        ('ARCHIVED', 'Archived'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        db_index=True
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        db_index=True
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='UNREAD',
        db_index=True
    )
    
    # Stock information
    symbol = models.CharField(max_length=10, db_index=True)
    
    # Notification content
    title = models.CharField(max_length=255)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)  # Store full news/spike data
    
    # Timestamps
    timestamp = models.DateTimeField(db_index=True)  # Event timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Priority/Urgency
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='MEDIUM'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Notifications"
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['symbol', '-timestamp']),
            models.Index(fields=['user', 'notification_type', 'status']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} for {self.user.username}: {self.symbol}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if self.status == 'UNREAD':
            self.status = 'READ'
            self.read_at = timezone.now()
            self.save(update_fields=['status', 'read_at'])
    
    def mark_as_unread(self):
        """Mark notification as unread"""
        if self.status == 'READ':
            self.status = 'UNREAD'
            self.read_at = None
            self.save(update_fields=['status', 'read_at'])
    
    def archive(self):
        """Archive notification"""
        self.status = 'ARCHIVED'
        self.save(update_fields=['status'])


class NotificationPreference(models.Model):
    """
    User notification preferences
    Controls which types of notifications users want to receive
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    
    # Enable/disable notification types
    news_alerts_enabled = models.BooleanField(default=True)
    volume_spike_alerts_enabled = models.BooleanField(default=True)
    
    # Thresholds
    min_volume_spike_threshold = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=50.0,
        help_text="Minimum volume spike percentage to trigger notification (e.g., 50.0 for 50%)"
    )
    
    # Notification delivery settings
    web_notifications_enabled = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Notification Preferences"
    
    def __str__(self):
        return f"Notification Preferences for {self.user.username}"

