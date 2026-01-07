"""
Volume Spike WebSocket Consumer
Broadcasts real-time volume spike alerts to connected clients
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer


class VolumeSpikeConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for volume spike data.
    Endpoint: ws://localhost:8000/ws/volume-spikes/
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.group_name = 'volume_spikes'
        
        # Join the volume spikes group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        print(f"✅ Client connected to volume_spikes WebSocket")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave the volume spikes group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        print(f"❌ Client disconnected from volume_spikes WebSocket (code: {close_code})")
    
    async def receive(self, text_data):
        """Handle incoming messages from WebSocket client"""
        pass
    
    async def volume_spike_update(self, event):
        """
        Receive message from channel layer and send to WebSocket
        """
        data = event['data']
        
        # Send the data to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'volume_spike',
            'data': data
        }))
