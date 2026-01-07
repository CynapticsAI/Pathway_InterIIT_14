from rest_framework import serializers
from .models import (
    StockTick, SarimaxForecast, NewsData, VolumeSpike, 
    Portfolio, Stock, Notification, NotificationPreference
)


class StockTickSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockTick
        fields = ['symbol', 'price', 'volume', 'timestamp']


class SarimaxForecastSerializer(serializers.ModelSerializer):
    class Meta:
        model = SarimaxForecast
        fields = ['symbol', 'timestamp', 'forecast_data']


class NewsDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsData
        fields = ['timestamp', 'news_data']


class VolumeSpikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VolumeSpike
        fields = ['symbol', 'timestamp', 'spike_data']


class StockSerializer(serializers.ModelSerializer):
    """
    Serializer for Stock model
    Handles individual stock holdings in a portfolio
    """
    total_cost = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
        read_only=True,
        help_text="Total investment cost (quantity * cost_basis)"
    )
    
    class Meta:
        model = Stock
        fields = [
            'id',
            'symbol',
            'quantity',
            'cost_basis',
            'total_cost',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_symbol(self, value):
        """Ensure symbol is uppercase"""
        return value.upper().strip()
    
    def validate_quantity(self, value):
        """Ensure quantity is positive"""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0")
        return value
    
    def validate_cost_basis(self, value):
        """Ensure cost basis is positive"""
        if value <= 0:
            raise serializers.ValidationError("Cost basis must be greater than 0")
        return value


class PortfolioSerializer(serializers.ModelSerializer):
    """
    Serializer for Portfolio model
    Includes nested stocks data
    """
    stocks = StockSerializer(many=True, read_only=True)
    total_stocks = serializers.IntegerField(read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Portfolio
        fields = [
            'id',
            'user_email',
            'username',
            'name',
            'total_stocks',
            'stocks',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BulkStockUploadSerializer(serializers.Serializer):
    """
    Serializer for bulk CSV upload
    Expects array of stocks with symbol, quantity, cost_basis
    """
    stocks = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False
    )
    
    def validate_stocks(self, value):
        """Validate each stock entry"""
        for stock in value:
            if 'symbol' not in stock:
                raise serializers.ValidationError("Each stock must have a 'symbol'")
            if 'quantity' not in stock:
                raise serializers.ValidationError("Each stock must have a 'quantity'")
            if 'cost_basis' not in stock:
                raise serializers.ValidationError("Each stock must have a 'cost_basis'")
            
            # Validate types
            try:
                float(stock['quantity'])
                float(stock['cost_basis'])
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    f"Invalid number format for {stock.get('symbol', 'unknown')}"
                )
            
            if float(stock['quantity']) <= 0:
                raise serializers.ValidationError(
                    f"Quantity must be positive for {stock['symbol']}"
                )
            if float(stock['cost_basis']) <= 0:
                raise serializers.ValidationError(
                    f"Cost basis must be positive for {stock['symbol']}"
                )
        
        return value


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for Notification model
    Handles notification data with full details
    """
    username = serializers.CharField(source='user.username', read_only=True)
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'username',
            'notification_type',
            'status',
            'symbol',
            'title',
            'message',
            'data',
            'timestamp',
            'created_at',
            'read_at',
            'priority',
            'time_ago',
        ]
        read_only_fields = [
            'id', 
            'username', 
            'created_at', 
            'read_at', 
            'time_ago'
        ]
    
    def get_time_ago(self, obj):
        """Calculate human-readable time ago"""
        from django.utils.timesince import timesince
        return timesince(obj.created_at)


class NotificationListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for notification lists
    Excludes heavy data field
    """
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'status',
            'symbol',
            'title',
            'message',
            'timestamp',
            'created_at',
            'priority',
            'time_ago',
        ]
        read_only_fields = fields
    
    def get_time_ago(self, obj):
        """Calculate human-readable time ago"""
        from django.utils.timesince import timesince
        return timesince(obj.created_at)


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for NotificationPreference model
    Handles user notification settings
    """
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = NotificationPreference
        fields = [
            'id',
            'username',
            'news_alerts_enabled',
            'volume_spike_alerts_enabled',
            'min_volume_spike_threshold',
            'web_notifications_enabled',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'username', 'created_at', 'updated_at']
    
    def validate_min_volume_spike_threshold(self, value):
        """Ensure threshold is reasonable"""
        if value < 0 or value > 1000:
            raise serializers.ValidationError(
                "Threshold must be between 0 and 1000 percent"
            )
        return value


class MarkNotificationReadSerializer(serializers.Serializer):
    """
    Serializer for marking notifications as read
    """
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        required=False,
        help_text="List of notification IDs to mark as read (optional for single notification)"
    )

