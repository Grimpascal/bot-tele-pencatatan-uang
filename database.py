import sqlite3
import os

DB_PATH = os.getenv("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "users.db"))

def init_db():
    """Menginisialisasi database SQLite dan membuat tabel jika belum ada."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_sheets (
            user_id INTEGER PRIMARY KEY,
            spreadsheet_id TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def get_user_sheet(user_id):
    """Mendapatkan spreadsheet_id berdasarkan user_id Telegram."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT spreadsheet_id FROM user_sheets WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def set_user_sheet(user_id, spreadsheet_id):
    """Menyimpan atau memperbarui spreadsheet_id untuk user_id tertentu."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_sheets (user_id, spreadsheet_id)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET spreadsheet_id = excluded.spreadsheet_id
    """, (user_id, spreadsheet_id))
    conn.commit()
    conn.close()
