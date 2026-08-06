import sqlite3
from dataclasses import dataclass
from pathlib import Path
from threading import Lock


@dataclass
class ChatTurn:
    prompt: str
    response: str
    success: bool


class InMemoryChatHistoryStore:
    """Thread-safe in-memory store for per-user chat history."""

    def __init__(self) -> None:
        self._store: dict[str, list[ChatTurn]] = {}
        self._lock = Lock()

    def append(self, user_id: str, turn: ChatTurn) -> None:
        with self._lock:
            if user_id not in self._store:
                self._store[user_id] = []
            self._store[user_id].append(turn)

    def get_recent(self, user_id: str, limit: int) -> list[ChatTurn]:
        with self._lock:
            turns = self._store.get(user_id, [])
            return list(turns[-limit:])

    def get_all(self, user_id: str) -> list[ChatTurn]:
        with self._lock:
            return list(self._store.get(user_id, []))

    def clear(self, user_id: str) -> int:
        with self._lock:
            cleared = len(self._store.get(user_id, []))
            self._store[user_id] = []
            return cleared


class SqliteChatHistoryStore:
    """Thread-safe SQLite-backed store for per-user chat history."""

    def __init__(self, db_path: str) -> None:
        self._lock = Lock()
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                prompt TEXT NOT NULL,
                response TEXT NOT NULL,
                success INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        self._conn.commit()

    def append(self, user_id: str, turn: ChatTurn) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO chat_history (user_id, prompt, response, success) VALUES (?, ?, ?, ?)",
                (user_id, turn.prompt, turn.response, int(turn.success)),
            )
            self._conn.commit()

    def get_recent(self, user_id: str, limit: int) -> list[ChatTurn]:
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT prompt, response, success
                FROM chat_history
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()
        rows = list(reversed(rows))
        return [
            ChatTurn(prompt=row[0], response=row[1], success=bool(row[2]))
            for row in rows
        ]

    def get_all(self, user_id: str) -> list[ChatTurn]:
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT prompt, response, success
                FROM chat_history
                WHERE user_id = ?
                ORDER BY id ASC
                """,
                (user_id,),
            ).fetchall()
        return [
            ChatTurn(prompt=row[0], response=row[1], success=bool(row[2]))
            for row in rows
        ]

    def clear(self, user_id: str) -> int:
        with self._lock:
            row = self._conn.execute(
                "SELECT COUNT(*) FROM chat_history WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            cleared = int(row[0]) if row else 0
            self._conn.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
            self._conn.commit()
        return cleared

    def list_user_ids(self) -> list[str]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT DISTINCT user_id FROM chat_history ORDER BY user_id ASC"
            ).fetchall()
        return [str(row[0]) for row in rows]

    def list_recent_records(self, limit: int = 200) -> list[dict]:
        safe_limit = max(1, min(1000, int(limit)))
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT user_id, prompt, response, success, created_at
                FROM chat_history
                ORDER BY id DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()
        return [
            {
                "user_id": str(row[0]),
                "prompt": str(row[1]),
                "response": str(row[2]),
                "success": bool(row[3]),
                "created_at": str(row[4]),
            }
            for row in rows
        ]
