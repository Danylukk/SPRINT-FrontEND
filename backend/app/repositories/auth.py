import sqlite3


class AuthRepository:
    def __init__(self, database):
        self.database = database

    def create_user(self, username, password_hash):
        try:
            with self.database.connect() as db:
                cursor = db.execute(
                    "INSERT INTO users(username, password_hash) VALUES (?, ?)",
                    (username, password_hash),
                )
                return {"id": cursor.lastrowid, "usuario": username}
        except sqlite3.IntegrityError:
            return None

    def find_user(self, username):
        with self.database.connect() as db:
            row = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            return dict(row) if row else None

    def create_session(self, digest, user_id, expires_at):
        with self.database.connect() as db:
            db.execute("INSERT INTO sessions VALUES (?, ?, ?)", (digest, user_id, expires_at))

    def find_session(self, digest, now):
        with self.database.connect() as db:
            row = db.execute("""
                SELECT u.id, u.username AS usuario FROM sessions s
                JOIN users u ON u.id = s.user_id
                WHERE s.token_hash = ? AND s.expires_at > ?
            """, (digest, now)).fetchone()
            return dict(row) if row else None

    def delete_session(self, digest):
        with self.database.connect() as db:
            db.execute("DELETE FROM sessions WHERE token_hash = ?", (digest,))
