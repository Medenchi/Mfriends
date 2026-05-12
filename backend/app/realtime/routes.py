import json

from backend.app.core.security import decode_token
from backend.app.realtime.manager import manager
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token", "")
    subject = decode_token(token)
    if not subject:
        await websocket.close(code=4401)
        return
    user_id = int(subject)
    await manager.connect(websocket, user_id)
    try:
        while True:
            raw = await websocket.receive_text()
            message = json.loads(raw)
            event = message.get("event")
            if event == "chat.join":
                manager.join_chat(websocket, int(message["chat_id"]))
            elif event == "chat.message":
                await manager.send_to_chat(
                    int(message["chat_id"]),
                    {
                        "event": "chat.message",
                        "chat_id": int(message["chat_id"]),
                        "from": user_id,
                        "body": message.get("body", ""),
                    },
                )
            elif event == "chat.typing":
                await manager.send_to_chat(
                    int(message["chat_id"]),
                    {
                        "event": "chat.typing",
                        "chat_id": int(message["chat_id"]),
                        "from": user_id,
                        "is_typing": bool(message.get("is_typing", True)),
                    },
                )
            elif event in {"webrtc.offer", "webrtc.answer", "webrtc.ice"}:
                await manager.send_to_user(
                    int(message["to_user_id"]),
                    {
                        "event": event,
                        "from_user_id": user_id,
                        "call_id": message.get("call_id"),
                        "payload": message.get("payload"),
                    },
                )
            elif event == "presence.ping":
                await websocket.send_json({"event": "presence.pong"})
    except (WebSocketDisconnect, json.JSONDecodeError, KeyError, ValueError):
        manager.disconnect(websocket, user_id)
