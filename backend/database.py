import sqlite3
import json
import os
from datetime import datetime
from contextlib import contextmanager
from pathlib import Path


class SQLiteDB:
    def __init__(self, db_path: str = "./project_agent.db"):
        self.db_path = db_path
        self.init_db()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    path TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    title TEXT,
                    model TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workplans (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    tasks TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    workplan_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    priority INTEGER,
                    assigned_agent TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (workplan_id) REFERENCES workplans(id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS patches (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    applied BOOLEAN DEFAULT 0,
                    created_at TEXT NOT NULL,
                    applied_at TEXT,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS file_operations (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    content TEXT,
                    status TEXT DEFAULT 'pending',
                    result TEXT,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                )
            """)

    def dict_from_row(self, row):
        if row is None:
            return None
        return dict(row)

    def query(self, sql: str, params: tuple = ()):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return [self.dict_from_row(row) for row in cursor.fetchall()]

    def query_one(self, sql: str, params: tuple = ()):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            row = cursor.fetchone()
            return self.dict_from_row(row)

    def execute(self, sql: str, params: tuple = ()):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return cursor.lastrowid

    def insert(self, table: str, data: dict):
        keys = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        sql = f"INSERT INTO {table} ({keys}) VALUES ({placeholders})"
        return self.execute(sql, tuple(data.values()))

    def update(self, table: str, data: dict, where: str, where_params: tuple):
        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        sql = f"UPDATE {table} SET {set_clause} WHERE {where}"
        params = tuple(list(data.values()) + list(where_params))
        return self.execute(sql, params)

    def delete(self, table: str, where: str, where_params: tuple):
        sql = f"DELETE FROM {table} WHERE {where}"
        return self.execute(sql, where_params)

    def create_project(self, id: str, name: str, path: str):
        now = datetime.utcnow().isoformat()
        return self.insert("projects", {
            "id": id,
            "name": name,
            "path": path,
            "created_at": now,
            "updated_at": now
        })

    def get_projects(self):
        return self.query("SELECT * FROM projects ORDER BY created_at DESC")

    def get_project(self, id: str):
        return self.query_one("SELECT * FROM projects WHERE id = ?", (id,))

    def create_conversation(self, id: str, project_id: str, title: str, model: str):
        now = datetime.utcnow().isoformat()
        return self.insert("conversations", {
            "id": id,
            "project_id": project_id,
            "title": title,
            "model": model,
            "created_at": now,
            "updated_at": now
        })

    def get_conversations(self, project_id: str):
        return self.query(
            "SELECT * FROM conversations WHERE project_id = ? ORDER BY created_at DESC",
            (project_id,)
        )

    def get_conversation(self, id: str):
        return self.query_one("SELECT * FROM conversations WHERE id = ?", (id,))

    def create_message(self, id: str, conversation_id: str, role: str, content: str):
        now = datetime.utcnow().isoformat()
        return self.insert("messages", {
            "id": id,
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "created_at": now
        })

    def get_messages(self, conversation_id: str):
        return self.query(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
            (conversation_id,)
        )

    def create_workplan(self, id: str, conversation_id: str, title: str, description: str, tasks: list):
        now = datetime.utcnow().isoformat()
        return self.insert("workplans", {
            "id": id,
            "conversation_id": conversation_id,
            "title": title,
            "description": description,
            "tasks": json.dumps(tasks),
            "created_at": now,
            "updated_at": now
        })

    def get_workplans(self, conversation_id: str):
        workplans = self.query(
            "SELECT * FROM workplans WHERE conversation_id = ? ORDER BY created_at DESC",
            (conversation_id,)
        )
        for wp in workplans:
            wp["tasks"] = json.loads(wp["tasks"]) if wp["tasks"] else []
        return workplans

    def create_patch(self, id: str, conversation_id: str, content: str):
        now = datetime.utcnow().isoformat()
        return self.insert("patches", {
            "id": id,
            "conversation_id": conversation_id,
            "content": content,
            "created_at": now
        })

    def get_patches(self, conversation_id: str):
        return self.query(
            "SELECT * FROM patches WHERE conversation_id = ? ORDER BY created_at DESC",
            (conversation_id,)
        )

    def create_file_operation(self, id: str, project_id: str, operation: str, file_path: str, content: str = None):
        now = datetime.utcnow().isoformat()
        return self.insert("file_operations", {
            "id": id,
            "project_id": project_id,
            "operation": operation,
            "file_path": file_path,
            "content": content,
            "created_at": now
        })

    def update_file_operation(self, id: str, status: str, result: str = None):
        now = datetime.utcnow().isoformat()
        return self.update(
            "file_operations",
            {"status": status, "result": result, "completed_at": now},
            "id = ?",
            (id,)
        )

    def get_file_operations(self, project_id: str):
        return self.query(
            "SELECT * FROM file_operations WHERE project_id = ? ORDER BY created_at DESC",
            (project_id,)
        )
