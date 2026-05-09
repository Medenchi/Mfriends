import json
from collections import defaultdict

from fastapi import WebSocket


class RealtimeManager:
    def __init__(self) -> None:
        self._users: dict[int, set[WebSocket]] = defaultdict(set)
        self._chats: dict[int, set[WebSocket]] = defaultdict(set)

    async def connect(self, websocket: WebSocket, user_id: int) -> None:
        await websocket.accept()
        self._users[user_id].add(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int) -> None:
        self._users[user_id].discard(websocket)
        for sockets in self._chats.values():
            sockets.discard(websocket)

    def join_chat(self, websocket: WebSocket, chat_id: int) -> None:
        self._chats[chat_id].add(websocket)

    async def send_to_user(self, user_id: int, payload: dict) -> None:
        disconnected: list[WebSocket] = []
        for websocket in self._users[user_id]:
            try:
                await websocket.send_text(json.dumps(payload))
            except RuntimeError:
                disconnected.append(websocket)
        for websocket in disconnected:
            self._users[user_id].discard(websocket)

    async def send_to_chat(self, chat_id: int, payload: dict) -> None:
        disconnected: list[WebSocket] = []
        for websocket in self._chats[chat_id]:
            try:
                await websocket.send_text(json.dumps(payload))
            except RuntimeError:
                disconnected.append(websocket)
        for websocket in disconnected:
            self._chats[chat_id].discard(websocket)


manager = RealtimeManager()
