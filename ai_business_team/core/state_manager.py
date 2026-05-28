import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class StateManager:
    """Persists all business and agent state to SQLite + JSON files."""

    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.db_path = self.base_dir / "team.db"
        self.businesses_dir = self.base_dir / "businesses"
        self.outputs_dir = self.base_dir / "outputs"
        self.businesses_dir.mkdir(exist_ok=True)
        self.outputs_dir.mkdir(exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS businesses (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    niche TEXT NOT NULL,
                    model TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'ideation',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    data_path TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS agent_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    agent TEXT NOT NULL,
                    business_id TEXT,
                    task TEXT NOT NULL,
                    output_summary TEXT,
                    tokens_used INTEGER DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    business_id TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    recorded_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    agent TEXT NOT NULL,
                    business_id TEXT,
                    task TEXT NOT NULL,
                    priority INTEGER DEFAULT 5,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    completed_at TEXT
                );
            """)

    def create_business(self, name: str, niche: str, model: str, description: str) -> Dict:
        business_id = str(uuid.uuid4())[:8]
        now = datetime.utcnow().isoformat()
        data = {
            "id": business_id, "name": name, "niche": niche, "model": model,
            "description": description, "status": "ideation",
            "created_at": now, "updated_at": now,
            "business_plan": None, "website": None,
            "products": [], "content_pieces": [],
            "revenue": 0.0, "expenses": 0.0,
            "metrics": {}, "growth_experiments": [], "next_actions": []
        }
        data_path = self.businesses_dir / f"{business_id}.json"
        data_path.write_text(json.dumps(data, indent=2))
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO businesses VALUES (?,?,?,?,?,?,?,?)",
                (business_id, name, niche, model, "ideation", now, now, str(data_path))
            )
        return data

    def get_business(self, business_id: str) -> Optional[Dict]:
        data_path = self.businesses_dir / f"{business_id}.json"
        if not data_path.exists():
            return None
        return json.loads(data_path.read_text())

    def update_business(self, business_id: str, updates: Dict) -> Optional[Dict]:
        data = self.get_business(business_id)
        if not data:
            return None
        data.update(updates)
        data["updated_at"] = datetime.utcnow().isoformat()
        data_path = self.businesses_dir / f"{business_id}.json"
        data_path.write_text(json.dumps(data, indent=2))
        if "status" in updates:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE businesses SET status=?, updated_at=? WHERE id=?",
                    (updates["status"], data["updated_at"], business_id)
                )
        return data

    def list_businesses(self) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT id, name, niche, model, status FROM businesses ORDER BY created_at DESC"
            ).fetchall()
        results = []
        for row in rows:
            data = self.get_business(row[0]) or {}
            data.update({"id": row[0], "name": row[1], "niche": row[2], "model": row[3], "status": row[4]})
            results.append(data)
        return results

    def log_agent_activity(self, agent: str, task: str, output_summary: str,
                           business_id: str = None, tokens_used: int = 0):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO agent_log (timestamp, agent, business_id, task, output_summary, tokens_used) VALUES (?,?,?,?,?,?)",
                (datetime.utcnow().isoformat(), agent, business_id, task[:500], output_summary[:1000], tokens_used)
            )

    def get_agent_log(self, limit: int = 50) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT timestamp, agent, business_id, task, output_summary, tokens_used FROM agent_log ORDER BY id DESC LIMIT ?",
                (limit,)
            ).fetchall()
        return [
            {"timestamp": r[0], "agent": r[1], "business_id": r[2],
             "task": r[3], "summary": r[4], "tokens": r[5]}
            for r in rows
        ]

    def log_metric(self, business_id: str, metric_name: str, value: float):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO metrics VALUES (NULL,?,?,?,?)",
                (business_id, metric_name, value, datetime.utcnow().isoformat())
            )
        data = self.get_business(business_id)
        if data:
            metrics = data.get("metrics", {})
            metrics[metric_name] = value
            self.update_business(business_id, {"metrics": metrics})

    def save_output(self, business_id: str, output_type: str, filename: str, content: str) -> str:
        output_dir = self.outputs_dir / business_id / output_type
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / filename
        output_path.write_text(content)
        return str(output_path)

    def add_task(self, agent: str, task: str, business_id: str = None, priority: int = 5) -> str:
        task_id = str(uuid.uuid4())[:8]
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?)",
                (task_id, agent, business_id, task, priority, "pending", datetime.utcnow().isoformat(), None)
            )
        return task_id

    def get_pending_tasks(self, agent: str = None) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            if agent:
                rows = conn.execute(
                    "SELECT id, agent, business_id, task, priority FROM tasks WHERE status='pending' AND agent=? ORDER BY priority DESC",
                    (agent,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, agent, business_id, task, priority FROM tasks WHERE status='pending' ORDER BY priority DESC"
                ).fetchall()
        return [{"id": r[0], "agent": r[1], "business_id": r[2], "task": r[3], "priority": r[4]} for r in rows]

    def complete_task(self, task_id: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE tasks SET status='completed', completed_at=? WHERE id=?",
                (datetime.utcnow().isoformat(), task_id)
            )
