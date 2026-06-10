import asyncio
import websockets
import json
import uuid

async def test_openclaw():
    uri = "ws://127.0.0.1:18789"
    token = "63c37b514ddec59dcc754c874bcc9ad5a307a4cdd2604a67"
    
    print(f"Connecting to OpenClaw at {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected! Waiting for challenge...")
            challenge_msg = await websocket.recv()
            challenge = json.loads(challenge_msg)
            print(f"< Received: {challenge}")
            
            if challenge.get("event") == "connect.challenge":
                nonce = challenge["payload"]["nonce"]
                reply = {
                    "type": "command", # or event
                    "command": "connect.reply", 
                    "payload": {
                        "token": token,
                        "nonce": nonce
                    }
                }
                # Sometimes the structure is action: authenticate
                auth_req = {
                    "type": "authenticate",
                    "token": token
                }
                await websocket.send(json.dumps(auth_req))
                print(f"> Sent auth: {auth_req}")

                response = await websocket.recv()
                print(f"< Received: {response}")
                
                # Now try to ask for something
                request = {
                    "type": "agent.task",
                    "payload": {
                        "text": "Hello OpenClaw! Please navigate to example.com and tell me the title."
                    }
                }
                await websocket.send(json.dumps(request))
                print(f"> Sent task: {request}")
                
                while True:
                    update = await websocket.recv()
                    print(f"< Received back: {update}")
                    
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test_openclaw())
