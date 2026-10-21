from datetime import datetime, timezone


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def conversation(row):
    return {"id": row["id"], "titulo": row["title"],
            "criado_em": row["created_at"], "atualizado_em": row["updated_at"]}


def message(row):
    return {"id": row["id"], "papel": row["role"],
            "conteudo": row["content"], "criado_em": row["created_at"]}


class ConversationRepository:
    def __init__(self, database):
        self.database = database

    def create(self, user_id, title):
        now = timestamp()
        with self.database.connect() as db:
            cursor = db.execute("""
                INSERT INTO conversations(user_id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """, (user_id, title, now, now))
            return {"id": cursor.lastrowid, "titulo": title,
                    "criado_em": now, "atualizado_em": now}

    def list(self, user_id):
        with self.database.connect() as db:
            rows = db.execute("""
                SELECT * FROM conversations WHERE user_id = ? ORDER BY updated_at DESC, id DESC
            """, (user_id,)).fetchall()
            return [conversation(row) for row in rows]

    def get(self, user_id, conversation_id):
        with self.database.connect() as db:
            row = db.execute("SELECT * FROM conversations WHERE id = ? AND user_id = ?",
                             (conversation_id, user_id)).fetchone()
            if not row:
                return None
            rows = db.execute("SELECT * FROM messages WHERE conversation_id = ? ORDER BY id",
                              (conversation_id,)).fetchall()
            return {**conversation(row), "mensagens": [message(item) for item in rows]}

    def append_pair(self, user_id, conversation_id, content, answer):
        now = timestamp()
        with self.database.connect() as db:
            # A escrita e a checagem de dono compartilham a mesma transação.
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM conversations WHERE id = ? AND user_id = ?",
                             (conversation_id, user_id)).fetchone()
            if not row:
                return None
            first = db.execute("SELECT 1 FROM messages WHERE conversation_id = ? LIMIT 1",
                               (conversation_id,)).fetchone() is None
            items = []
            for role, text in (("user", content), ("assistant", answer)):
                cursor = db.execute("""
                    INSERT INTO messages(conversation_id, role, content, created_at)
                    VALUES (?, ?, ?, ?)
                """, (conversation_id, role, text, now))
                items.append({"id": cursor.lastrowid, "papel": role,
                              "conteudo": text, "criado_em": now})
            title = content[:60] if first and row["title"] == "Nova conversa" else row["title"]
            db.execute("UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
                       (title, now, conversation_id))
            return items
