import json
import sqlite3
import uuid
from datetime import datetime
from typing import Dict, List, Optional


class MessageBus:
    """SQLite-backed message queue for inter-agent communication."""

    def __init__(self, db_path: str = "team.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    from_agent TEXT NOT NULL,
                    to_agent TEXT,
                    message TEXT NOT NULL,
                    payload TEXT,
                    read INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)

    def publish(self, from_agent: str, to_agent: Optional[str], message: str, payload: Dict = None) -> str:
        msg_id = str(uuid.uuid4())[:8]
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO messages VALUES (?,?,?,?,?,?,?)",
                (msg_id, from_agent, to_agent, message, json.dumps(payload or {}), 0, datetime.utcnow().isoformat())
            )
        return msg_id

    def consume(self, agent_name: str) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT id, from_agent, message, payload, created_at FROM messages "
                "WHERE (to_agent=? OR to_agent IS NULL) AND read=0 ORDER BY created_at ASC",
                (agent_name,)
            ).fetchall()
            if rows:
                ids = [r[0] for r in rows]
                conn.execute(f"UPDATE messages SET read=1 WHERE id IN ({','.join('?'*len(ids))})", ids)
        return [
            {"id": r[0], "from": r[1], "message": r[2],
             "payload": json.loads(r[3]), "timestamp": r[4]}
            for r in rows
        ]

    def broadcast(self, from_agent: str, message: str, payload: Dict = None) -> str:
        return self.publish(from_agent, None, message, payload)

    def get_all_messages(self, limit: int = 100) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT from_agent, to_agent, message, payload, created_at FROM messages ORDER BY created_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
        return [
            {"from": r[0], "to": r[1], "message": r[2],
             "payload": json.loads(r[3]), "timestamp": r[4]}
            for r in rows
        ]
