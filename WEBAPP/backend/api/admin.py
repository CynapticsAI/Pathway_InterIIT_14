from django.contrib import admin
from .models import (
    MarketBreadth,
    StockTick,
    PnLData,
    SarimaxForecast,
    VolumeSpike,
    NewsData,
    Portfolio,
    Stock,
    Notification,
    NotificationPreference,
)


@admin.register(MarketBreadth)
class MarketBreadthAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'advancing_stocks', 'declining_stocks', 'unchanged_stocks', 'total_stocks', 'advance_decline_line']
    list_filter = ['timestamp']
    search_fields = ['timestamp']
    ordering = ['-timestamp']


@admin.register(StockTick)
class StockTickAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'price', 'volume', 'timestamp', 'created_at']
    list_filter = ['symbol', 'timestamp']
    search_fields = ['symbol']
    ordering = ['-timestamp']


@admin.register(PnLData)
class PnLDataAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'total_pnl', 'created_at']
    list_filter = ['timestamp']
    ordering = ['-timestamp']


@admin.register(SarimaxForecast)
class SarimaxForecastAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'timestamp', 'created_at']
    list_filter = ['symbol', 'timestamp']
    search_fields = ['symbol']
    ordering = ['-timestamp']


@admin.register(VolumeSpike)
class VolumeSpikeAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'timestamp', 'created_at']
    list_filter = ['symbol', 'timestamp']
    search_fields = ['symbol']
    ordering = ['-timestamp']


@admin.register(NewsData)
class NewsDataAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'created_at']
    list_filter = ['timestamp']
    ordering = ['-timestamp']


class StockInline(admin.TabularInline):
    """Inline display of stocks within portfolio admin"""
    model = Stock
    extra = 1
    fields = ['symbol', 'quantity', 'cost_basis', 'total_cost']
    readonly_fields = ['total_cost']


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'total_stocks', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username', 'user__email', 'name']
    readonly_fields = ['total_stocks', 'created_at', 'updated_at']
    ordering = ['-created_at']
    inlines = [StockInline]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'portfolio', 'quantity', 'cost_basis', 'total_cost', 'created_at', 'updated_at']
    list_filter = ['symbol', 'created_at', 'updated_at']
    search_fields = ['symbol', 'portfolio__user__username', 'portfolio__user__email']
    readonly_fields = ['total_cost', 'created_at', 'updated_at']
    ordering = ['portfolio', 'symbol']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('portfolio__user')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'notification_type', 'symbol', 'title', 'status', 'priority', 'created_at']
    list_filter = ['notification_type', 'status', 'priority', 'created_at']
    search_fields = ['user__username', 'user__email', 'symbol', 'title', 'message']
    readonly_fields = ['created_at', 'read_at']
    ordering = ['-created_at']
    list_per_page = 50
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'notification_type', 'symbol', 'status', 'priority')
        }),
        ('Content', {
            'fields': ('title', 'message', 'data')
        }),
        ('Timestamps', {
            'fields': ('timestamp', 'created_at', 'read_at')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')
    
    actions = ['mark_as_read', 'mark_as_unread', 'archive_notifications']
    
    def mark_as_read(self, request, queryset):
        """Bulk action to mark notifications as read"""
        count = 0
        for notification in queryset.filter(status='UNREAD'):
            notification.mark_as_read()
            count += 1
        self.message_user(request, f'{count} notification(s) marked as read.')
    mark_as_read.short_description = "Mark selected as read"
    
    def mark_as_unread(self, request, queryset):
        """Bulk action to mark notifications as unread"""
        count = 0
        for notification in queryset.filter(status='READ'):
            notification.mark_as_unread()
            count += 1
        self.message_user(request, f'{count} notification(s) marked as unread.')
    mark_as_unread.short_description = "Mark selected as unread"
    
    def archive_notifications(self, request, queryset):
        """Bulk action to archive notifications"""
        count = 0
        for notification in queryset:
            notification.archive()
            count += 1
        self.message_user(request, f'{count} notification(s) archived.')
    archive_notifications.short_description = "Archive selected notifications"


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = [
        'user', 
        'news_alerts_enabled', 
        'volume_spike_alerts_enabled', 
        'min_volume_spike_threshold',
        'web_notifications_enabled',
        'updated_at'
    ]
    list_filter = ['news_alerts_enabled', 'volume_spike_alerts_enabled', 'web_notifications_enabled']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['user']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')
