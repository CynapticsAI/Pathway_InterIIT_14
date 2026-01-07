"""
Stock Tick WebSocket Consumer
Broadcasts real-time stock tick data to connected clients
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer


class StockTickConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for stock tick data.
    Endpoint: ws://localhost:8000/ws/stock-ticks/
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.group_name = 'stock_ticks'
        
        # Join the stock ticks group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        print(f"✅ Client connected to stock_ticks WebSocket")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave the stock ticks group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        print(f"❌ Client disconnected from stock_ticks WebSocket (code: {close_code})")
    
    async def receive(self, text_data):
        """Handle incoming messages from WebSocket client"""
        pass
    
    async def stock_tick_update(self, event):
        """
        Receive message from channel layer and send to WebSocket
        """
        data = event['data']
        
        # Send the data to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'stock_tick',
            'data': data
        }))
