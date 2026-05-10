import asyncio
import json
import os
import jwt
import websockets

JWT_PUBLIC_KEY_PATH = os.getenv("JWT_PUBLIC_KEY_PATH", "/app/jwt_public_key.pem")
HOST = os.getenv("GATEWAY_HOST", "0.0.0.0")
PORT = int(os.getenv("GATEWAY_PORT", "8765"))

with open(JWT_PUBLIC_KEY_PATH) as f:
    PUBLIC_KEY = f.read()

async def handler(websocket):
    token = None
    try:
        async for message in websocket:
            data = json.loads(message)
            if data.get("type") == "auth":
                token = data.get("token")
                try:
                    payload = jwt.decode(token, PUBLIC_KEY, algorithms=["RS256"])
                    await websocket.send(json.dumps({"type": "auth_ok", "user_id": payload.get("user_id")}))
                except jwt.InvalidTokenError:
                    await websocket.send(json.dumps({"type": "auth_error", "message": "Invalid token"}))
                    return
            elif token is None:
                await websocket.send(json.dumps({"type": "error", "message": "Authenticate first"}))
            else:
                result = {"type": "pong", "data": data}
                await websocket.send(json.dumps(result))
    except websockets.exceptions.ConnectionClosed:
        pass

async def main():
    async with websockets.serve(handler, HOST, PORT):
        print(f"Gateway listening on {HOST}:{PORT}")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
