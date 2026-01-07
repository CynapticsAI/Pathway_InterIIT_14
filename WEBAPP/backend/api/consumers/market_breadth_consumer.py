"""
Market Breadth WebSocket Consumer
Broadcasts real-time market breadth data to connected clients
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer


class MarketBreadthConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for market breadth data.
    Endpoint: ws://localhost:8000/ws/market-breadth/
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.group_name = 'market_breadth'
        
        # Join the market breadth group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        print(f"✅ Client connected to market_breadth WebSocket")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave the market breadth group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        print(f"❌ Client disconnected from market_breadth WebSocket (code: {close_code})")
    
    async def receive(self, text_data):
        """
        Handle incoming messages from WebSocket client
        (Not typically used for this read-only stream, but included for completeness)
        """
        pass
    
    async def market_breadth_update(self, event):
        """
        Receive message from channel layer and send to WebSocket
        This method name matches the 'type' key in channel_layer.group_send()
        """
        # Extract the data from the event
        data = event['data']
        
        # Send the data to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'market_breadth',
            'data': data
        }))
