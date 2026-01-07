#!/usr/bin/env python3
"""
Test P&L WebSocket Connection
"""
import asyncio
import websockets
import json

async def test_pnl_websocket():
    uri = "ws://localhost:8000/ws/pnl/"
    
    print(f"🔌 Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to P&L WebSocket!")
            print("⏳ Waiting for messages...\n")
            
            message_count = 0
            async for message in websocket:
                message_count += 1
                data = json.loads(message)
                
                print(f"📊 Message #{message_count}:")
                print(json.dumps(data, indent=2))
                print("-" * 60)
                
                # Stop after 10 messages for testing
                if message_count >= 10:
                    print("\n✅ Received 10 messages, test complete!")
                    break
                    
    except websockets.exceptions.ConnectionClosed:
        print("❌ Connection closed by server")
    except ConnectionRefusedError:
        print("❌ Connection refused. Is Django server running?")
        print("   Start with: daphne -b 0.0.0.0 -p 8000 config.asgi:application")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("P&L WebSocket Test Client")
    print("=" * 60)
    asyncio.run(test_pnl_websocket())
