"""
P&L WebSocket Consumer
Broadcasts real-time P&L data to connected clients
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer


class PnLConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for P&L data.
    Endpoint: ws://localhost:8000/ws/pnl/
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.group_name = 'pnl_updates'
        
        # Join the P&L group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        print(f"✅ Client connected to pnl WebSocket")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave the P&L group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        print(f"❌ Client disconnected from pnl WebSocket (code: {close_code})")
    
    async def receive(self, text_data):
        """Handle incoming messages from WebSocket client"""
        pass
    
    async def pnl_update(self, event):
        """
        Receive message from channel layer and send to WebSocket
        """
        data = event['data']
        
        # Send the data to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'pnl',
            'data': data
        }))
