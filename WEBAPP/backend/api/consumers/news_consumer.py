"""
News WebSocket Consumer
Broadcasts real-time news data to connected clients
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer


class NewsConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for news data.
    Endpoint: ws://localhost:8000/ws/news/
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.group_name = 'news_updates'
        
        # Join the news updates group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        print(f"✅ Client connected to news WebSocket")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave the news updates group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        print(f"❌ Client disconnected from news WebSocket (code: {close_code})")
    
    async def receive(self, text_data):
        """Handle incoming messages from WebSocket client"""
        pass
    
    async def news_update(self, event):
        """
        Receive message from channel layer and send to WebSocket
        """
        data = event['data']
        
        # Send the data to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'news',
            'data': data
        }))
