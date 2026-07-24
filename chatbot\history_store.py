from dataclasses import dataclass
from threading import Lock
from typing import Dict, List


@dataclass
class ChatTurn:
    prompt: str
    response: str
    success: bool


class InMemoryChatHistoryStore:
    """Thread-safe in-memory store for per-user chat history."""

    def __init__(self) -> None:
        self._store: Dict[str, List[ChatTurn]] = {}
        self._lock = Lock()

    def append(self, user_id: str, turn: ChatTurn) -> None:
        with self._lock:
            if user_id not in self._store:
                self._store[user_id] = []
            self._store[user_id].append(turn)

    def get_recent(self, user_id: str, limit: int) -> List[ChatTurn]:
        with self._lock:
            turns = self._store.get(user_id, [])
            return list(turns[-limit:])

    def get_all(self, user_id: str) -> List[ChatTurn]:
        with self._lock:
            return list(self._store.get(user_id, []))

    def clear(self, user_id: str) -> int:
        with self._lock:
            cleared = len(self._store.get(user_id, []))
            self._store[user_id] = []
            return cleared
