from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from django.db import transaction
import requests
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from users.serializers import ChatbotMessageSerializer
from config import settings
from .models import (
    StockTick, SarimaxForecast, NewsData, VolumeSpike, 
    Portfolio, Stock, Notification, NotificationPreference
)
from .serializers import (
    StockTickSerializer, SarimaxForecastSerializer, NewsDataSerializer, 
    VolumeSpikeSerializer, PortfolioSerializer, StockSerializer, BulkStockUploadSerializer,
    NotificationSerializer, NotificationListSerializer, NotificationPreferenceSerializer,
    MarkNotificationReadSerializer
)
from .services import NotificationService
from django.utils import timezone
from datetime import timedelta

# Create your views here.

# DEV VIEW JUST FOR TESTING THE CHATBOT INTEGRATION
@extend_schema(
    tags=['Chatbot'],
    summary='Test chatbot integration',
    description='''
    Development endpoint for testing the chatbot API integration.
    
    **GET**: Returns instructions
    **POST**: Send a message to the chatbot and get response
    
    **Note:** This is a test endpoint. For production, use the chat conversations API.
    ''',
    request=ChatbotMessageSerializer,
    responses={
        200: OpenApiTypes.OBJECT,
    },
    examples=[
        OpenApiExample(
            'Test Message',
            description='Send a test message to the chatbot',
            value={'message': 'What is the price of AAPL?'},
            request_only=True,
        ),
    ]
)
class ChatbotTestView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        # Fetch the API chatbot
        return Response({"message": "Send a POST request with 'message' to test the chatbot."})
    
    def post(self, request):
        user_message = request.data.get("message", "")
        return Response({"note": "Chatbot integration pending", "message": user_message})
        # Send the message to the chatbot API
        res = requests.post(settings.CHATBOT_URL, json={"message": user_message})
        data = res.json()
        return Response(data)


@extend_schema(
    tags=['Stock Data'],
    summary='Get historical stock ticks',
    description='Fetch historical stock tick data for a specific symbol',
    parameters=[
        OpenApiParameter(
            name='symbol',
            type=str,
            location=OpenApiParameter.QUERY,
            description='Stock symbol (e.g., NVDA, AAPL)',
            required=True
        ),
        OpenApiParameter(
            name='limit',
            type=int,
            location=OpenApiParameter.QUERY,
            description='Number of records to return (default: 100, max: 500)',
            required=False
        ),
    ],
    responses={200: StockTickSerializer(many=True)}
)
class StockTickHistoryView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        symbol = request.query_params.get('symbol')
        limit = int(request.query_params.get('limit', 100))
        
        if not symbol:
            return Response({'error': 'Symbol parameter is required'}, status=400)
        
        # Limit to max 500 records
        limit = min(limit, 500)
        
        # Get most recent ticks for the symbol
        ticks = StockTick.objects.filter(symbol=symbol).order_by('-timestamp')[:limit]
        
        # Reverse to get chronological order
        ticks = reversed(ticks)
        
        serializer = StockTickSerializer(ticks, many=True)
        return Response(serializer.data)


@extend_schema(
    tags=['Stock Data'],
    summary='Get historical SARIMAX forecasts',
    description='Fetch historical SARIMAX forecast data for a specific symbol',
    parameters=[
        OpenApiParameter(
            name='symbol',
            type=str,
            location=OpenApiParameter.QUERY,
            description='Stock symbol (e.g., NVDA, AAPL)',
            required=True
        ),
        OpenApiParameter(
            name='limit',
            type=int,
            location=OpenApiParameter.QUERY,
            description='Number of records to return (default: 100, max: 500)',
            required=False
        ),
    ],
    responses={200: SarimaxForecastSerializer(many=True)}
)
class SarimaxForecastHistoryView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        symbol = request.query_params.get('symbol')
        limit = int(request.query_params.get('limit', 100))
        
        if not symbol:
            return Response({'error': 'Symbol parameter is required'}, status=400)
        
        # Limit to max 500 records
        limit = min(limit, 500)
        
        # Get most recent forecasts for the symbol
        forecasts = SarimaxForecast.objects.filter(symbol=symbol).order_by('-timestamp')[:limit]
        
        # Reverse to get chronological order
        forecasts = reversed(forecasts)
        
        serializer = SarimaxForecastSerializer(forecasts, many=True)
        return Response(serializer.data)


@extend_schema(
    tags=['Stock Data'],
    summary='Get historical news data',
    description='Fetch historical news data',
    parameters=[
        OpenApiParameter(
            name='limit',
            type=int,
            location=OpenApiParameter.QUERY,
            description='Number of records to return (default: 50, max: 200)',
            required=False
        ),
    ],
    responses={200: NewsDataSerializer(many=True)}
)
class NewsDataHistoryView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        limit = int(request.query_params.get('limit', 50))
        
        # Limit to max 200 records
        limit = min(limit, 200)
        
        # Get most recent news
        news = NewsData.objects.all().order_by('-timestamp')[:limit]
        
        # Reverse to get chronological order
        news = reversed(news)
        
        serializer = NewsDataSerializer(news, many=True)
        return Response(serializer.data)


@extend_schema(
    tags=['Stock Data'],
    summary='Get historical volume spikes',
    description='Fetch historical volume spike data for a specific symbol',
    parameters=[
        OpenApiParameter(
            name='symbol',
            type=str,
            location=OpenApiParameter.QUERY,
            description='Stock symbol (e.g., NVDA, AAPL)',
            required=False
        ),
        OpenApiParameter(
            name='limit',
            type=int,
            location=OpenApiParameter.QUERY,
            description='Number of records to return (default: 100, max: 500)',
            required=False
        ),
    ],
    responses={200: VolumeSpikeSerializer(many=True)}
)
class VolumeSpikeHistoryView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        symbol = request.query_params.get('symbol')
        limit = int(request.query_params.get('limit', 100))
        
        # Limit to max 500 records
        limit = min(limit, 500)
        
        # Get volume spikes, optionally filtered by symbol
        if symbol:
            spikes = VolumeSpike.objects.filter(symbol=symbol).order_by('-timestamp')[:limit]
        else:
            spikes = VolumeSpike.objects.all().order_by('-timestamp')[:limit]
        
        # Reverse to get chronological order
        spikes = reversed(spikes)
        
        serializer = VolumeSpikeSerializer(spikes, many=True)
        return Response(serializer.data)


@extend_schema(
    tags=['Portfolio'],
    summary='Get user portfolio',
    description='Get the authenticated user\'s portfolio with all stock holdings',
    responses={200: PortfolioSerializer}
)
class PortfolioView(APIView):
    """
    Get user's portfolio
    Auto-creates portfolio if it doesn't exist
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Get or create portfolio for user
        portfolio, created = Portfolio.objects.get_or_create(
            user=request.user,
            defaults={'name': f"{request.user.username}'s Portfolio"}
        )
        
        serializer = PortfolioSerializer(portfolio)
        return Response(serializer.data)


@extend_schema(
    tags=['Portfolio'],
    summary='Manage portfolio stocks',
    description='Add, update, delete, or list stocks in user\'s portfolio',
    responses={200: StockSerializer(many=True)}
)
class PortfolioStocksViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing stocks in user's portfolio
    Supports CRUD operations and bulk upload
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = StockSerializer
    lookup_field = 'symbol'
    
    def get_queryset(self):
        """Get stocks for the authenticated user's portfolio"""
        portfolio, created = Portfolio.objects.get_or_create(
            user=self.request.user,
            defaults={'name': f"{self.request.user.username}'s Portfolio"}
        )
        return Stock.objects.filter(portfolio=portfolio)
    
    def perform_create(self, serializer):
        """Create stock in user's portfolio"""
        portfolio, created = Portfolio.objects.get_or_create(
            user=self.request.user,
            defaults={'name': f"{self.request.user.username}'s Portfolio"}
        )
        
        # Check if stock already exists
        symbol = serializer.validated_data['symbol']
        existing_stock = Stock.objects.filter(portfolio=portfolio, symbol=symbol).first()
        
        if existing_stock:
            # Update existing stock
            existing_stock.quantity = serializer.validated_data['quantity']
            existing_stock.cost_basis = serializer.validated_data['cost_basis']
            existing_stock.save()
            return Response(
                StockSerializer(existing_stock).data,
                status=status.HTTP_200_OK
            )
        else:
            # Create new stock
            serializer.save(portfolio=portfolio)
    
    def perform_update(self, serializer):
        """Update stock in user's portfolio"""
        serializer.save()
    
    def destroy(self, request, *args, **kwargs):
        """Delete stock from portfolio"""
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(
                {'message': f'Stock {instance.symbol} removed from portfolio'},
                status=status.HTTP_204_NO_CONTENT
            )
        except Stock.DoesNotExist:
            return Response(
                {'error': 'Stock not found in portfolio'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @extend_schema(
        tags=['Portfolio'],
        summary='Bulk upload stocks',
        description='Upload multiple stocks at once (e.g., from CSV)',
        request=BulkStockUploadSerializer,
        responses={200: OpenApiTypes.OBJECT}
    )
    @action(detail=False, methods=['post'])
    def bulk_upload(self, request):
        """
        Bulk upload stocks to portfolio
        Expects JSON: {"stocks": [{"symbol": "NVDA", "quantity": 50, "cost_basis": 85.00}, ...]}
        """
        serializer = BulkStockUploadSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Get or create portfolio
        portfolio, created = Portfolio.objects.get_or_create(
            user=request.user,
            defaults={'name': f"{request.user.username}'s Portfolio"}
        )
        
        stocks_data = serializer.validated_data['stocks']
        created_count = 0
        updated_count = 0
        errors = []
        
        with transaction.atomic():
            for stock_data in stocks_data:
                symbol = stock_data['symbol'].upper().strip()
                quantity = float(stock_data['quantity'])
                cost_basis = float(stock_data['cost_basis'])
                
                try:
                    # Update or create stock
                    stock, created = Stock.objects.update_or_create(
                        portfolio=portfolio,
                        symbol=symbol,
                        defaults={
                            'quantity': quantity,
                            'cost_basis': cost_basis
                        }
                    )
                    
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                        
                except Exception as e:
                    errors.append({'symbol': symbol, 'error': str(e)})
        
        return Response({
            'message': 'Bulk upload completed',
            'created': created_count,
            'updated': updated_count,
            'errors': errors,
            'total_processed': created_count + updated_count
        }, status=status.HTTP_200_OK)
    
    @extend_schema(
        tags=['Portfolio'],
        summary='Get portfolio summary',
        description='Get summary statistics of portfolio (without real-time prices)',
        responses={200: OpenApiTypes.OBJECT}
    )
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get portfolio summary
        Returns total stocks count and total invested amount
        Frontend will calculate live P&L with real-time prices
        """
        portfolio, created = Portfolio.objects.get_or_create(
            user=request.user,
            defaults={'name': f"{request.user.username}'s Portfolio"}
        )
        
        stocks = Stock.objects.filter(portfolio=portfolio)
        
        total_invested = sum(
            float(stock.quantity * stock.cost_basis)
            for stock in stocks
        )
        
        summary_data = {
            'portfolio_id': portfolio.id,
            'portfolio_name': portfolio.name,
            'total_stocks': stocks.count(),
            'total_invested': round(total_invested, 2),
            'stocks': StockSerializer(stocks, many=True).data
        }
        
        return Response(summary_data)


class NotificationPagination(PageNumberPagination):
    """Custom pagination for notifications"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@extend_schema(tags=['Notifications'])
class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing notifications
    
    Provides endpoints for:
    - Listing user notifications (with filters)
    - Retrieving notification details
    - Marking notifications as read/unread
    - Deleting/archiving notifications
    - Getting unread count
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = NotificationPagination
    
    def get_queryset(self):
        """Return notifications for the authenticated user only"""
        user = self.request.user
        queryset = Notification.objects.filter(user=user)
        
        # Filter by status
        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param.upper())
        
        # Filter by type
        type_param = self.request.query_params.get('type', None)
        if type_param:
            queryset = queryset.filter(notification_type=type_param.upper())
        
        # Filter by symbol
        symbol_param = self.request.query_params.get('symbol', None)
        if symbol_param:
            queryset = queryset.filter(symbol=symbol_param.upper())
        
        # Filter by priority
        priority_param = self.request.query_params.get('priority', None)
        if priority_param:
            queryset = queryset.filter(priority=priority_param.upper())
        
        return queryset.select_related('user').order_by('-created_at')
    
    def get_serializer_class(self):
        """Use lightweight serializer for list view"""
        if self.action == 'list':
            return NotificationListSerializer
        return NotificationSerializer
    
    @extend_schema(
        summary='List user notifications',
        description='Get all notifications for the authenticated user with optional filters',
        parameters=[
            OpenApiParameter(
                name='status',
                type=str,
                description='Filter by status: UNREAD, READ, ARCHIVED',
                required=False
            ),
            OpenApiParameter(
                name='type',
                type=str,
                description='Filter by type: NEWS, VOLUME_SPIKE',
                required=False
            ),
            OpenApiParameter(
                name='symbol',
                type=str,
                description='Filter by stock symbol',
                required=False
            ),
            OpenApiParameter(
                name='priority',
                type=str,
                description='Filter by priority: LOW, MEDIUM, HIGH',
                required=False
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        """List notifications with filters"""
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        summary='Get notification details',
        description='Retrieve detailed information about a specific notification'
    )
    def retrieve(self, request, *args, **kwargs):
        """Get single notification"""
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        summary='Delete notification',
        description='Delete a notification (actually archives it)'
    )
    def destroy(self, request, *args, **kwargs):
        """Archive notification instead of deleting"""
        notification = self.get_object()
        notification.archive()
        return Response(
            {'message': 'Notification archived successfully'},
            status=status.HTTP_204_NO_CONTENT
        )
    
    @extend_schema(
        summary='Get unread notifications count',
        description='Get count of unread notifications for the authenticated user',
        responses={200: OpenApiTypes.OBJECT}
    )
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = NotificationService.get_unread_count(request.user)
        return Response({'unread_count': count})
    
    @extend_schema(
        summary='Mark notification as read',
        description='Mark a specific notification as read',
        responses={200: OpenApiTypes.OBJECT}
    )
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a notification as read"""
        notification = self.get_object()
        notification.mark_as_read()
        return Response({
            'message': 'Notification marked as read',
            'notification': NotificationSerializer(notification).data
        })
    
    @extend_schema(
        summary='Mark notification as unread',
        description='Mark a specific notification as unread',
        responses={200: OpenApiTypes.OBJECT}
    )
    @action(detail=True, methods=['post'])
    def mark_unread(self, request, pk=None):
        """Mark a notification as unread"""
        notification = self.get_object()
        notification.mark_as_unread()
        return Response({
            'message': 'Notification marked as unread',
            'notification': NotificationSerializer(notification).data
        })
    
    @extend_schema(
        summary='Mark all notifications as read',
        description='Mark all unread notifications as read for the authenticated user',
        request=MarkNotificationReadSerializer,
        responses={200: OpenApiTypes.OBJECT}
    )
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        serializer = MarkNotificationReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        notification_ids = serializer.validated_data.get('notification_ids', None)
        
        if notification_ids:
            # Mark specific notifications as read
            notifications = Notification.objects.filter(
                id__in=notification_ids,
                user=request.user,
                status='UNREAD'
            )
            count = 0
            for notification in notifications:
                notification.mark_as_read()
                count += 1
        else:
            # Mark all as read
            count = NotificationService.mark_all_as_read(request.user)
        
        return Response({
            'message': f'{count} notification(s) marked as read',
            'count': count
        })
    
    @extend_schema(
        summary='Get recent notifications',
        description='Get the most recent 10 unread notifications',
        responses={200: NotificationListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent unread notifications (for dropdown)"""
        notifications = Notification.objects.filter(
            user=request.user,
            status='UNREAD'
        ).select_related('user').order_by('-created_at')[:10]
        
        serializer = NotificationListSerializer(notifications, many=True)
        return Response({
            'notifications': serializer.data,
            'total_unread': NotificationService.get_unread_count(request.user)
        })


@extend_schema(tags=['Notifications'])
class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing notification preferences
    
    Provides endpoints for:
    - Getting user notification preferences
    - Updating notification preferences
    """
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'put', 'patch']
    
    def get_queryset(self):
        """Return preferences for the authenticated user only"""
        return NotificationPreference.objects.filter(user=self.request.user)
    
    def get_object(self):
        """Get or create notification preferences for user"""
        obj, created = NotificationPreference.objects.get_or_create(
            user=self.request.user
        )
        return obj
    
    @extend_schema(
        summary='Get notification preferences',
        description='Get notification preferences for the authenticated user'
    )
    def retrieve(self, request, *args, **kwargs):
        """Get user's notification preferences"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @extend_schema(
        summary='Update notification preferences',
        description='Update notification preferences for the authenticated user'
    )
    def update(self, request, *args, **kwargs):
        """Update notification preferences"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's preferences (convenience endpoint)"""
        return self.retrieve(request)
