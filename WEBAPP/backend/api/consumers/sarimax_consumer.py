"""
SARIMAX Forecast WebSocket Consumer
Broadcasts real-time SARIMAX forecast data to connected clients
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer


class SarimaxConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for SARIMAX forecast data.
    Endpoint: ws://localhost:8000/ws/sarimax-forecast/
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.group_name = 'sarimax_forecast'
        
        # Join the SARIMAX forecast group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        print(f"✅ Client connected to sarimax_forecast WebSocket")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave the SARIMAX forecast group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        print(f"❌ Client disconnected from sarimax_forecast WebSocket (code: {close_code})")
    
    async def receive(self, text_data):
        """Handle incoming messages from WebSocket client"""
        pass
    
    async def sarimax_update(self, event):
        """
        Receive message from channel layer and send to WebSocket
        """
        data = event['data']
        
        # Send the data to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'sarimax_forecast',
            'data': data
        }))
