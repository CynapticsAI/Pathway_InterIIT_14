from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ChatbotTestView, 
    StockTickHistoryView, 
    SarimaxForecastHistoryView,
    NewsDataHistoryView,
    VolumeSpikeHistoryView,
    PortfolioView,
    PortfolioStocksViewSet,
    NotificationViewSet,
    NotificationPreferenceViewSet,
)

app_name = 'api'

# Create router for ViewSets
router = DefaultRouter()
router.register(r'portfolio/stocks', PortfolioStocksViewSet, basename='portfolio-stocks')
router.register(r'notifications', NotificationViewSet, basename='notifications')
router.register(r'notification-preferences', NotificationPreferenceViewSet, basename='notification-preferences')

urlpatterns = [
    # Existing chatbot test endpoint
    path('chatbot/', ChatbotTestView.as_view(), name='chatbot-test'),
    
    # Stock data endpoints
    path('stock-ticks/', StockTickHistoryView.as_view(), name='stock-ticks-history'),
    path('sarimax-forecasts/', SarimaxForecastHistoryView.as_view(), name='sarimax-forecasts-history'),
    path('news/', NewsDataHistoryView.as_view(), name='news-history'),
    path('volume-spikes/', VolumeSpikeHistoryView.as_view(), name='volume-spikes-history'),
    
    # Portfolio endpoints
    path('portfolio/', PortfolioView.as_view(), name='portfolio'),
    
    # Include router URLs (for portfolio stocks CRUD, notifications, and preferences)
    path('', include(router.urls)),
]
