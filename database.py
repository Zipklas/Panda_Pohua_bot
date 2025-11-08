import sqlite3
from cryptography.fernet import Fernet

import os

KEY_FILE = "secret.key"

# Если ключ не существует — создаём
if not os.path.exists(KEY_FILE):
    from cryptography.fernet import Fernet
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as key_file:
        key_file.write(key)
else:
    with open(KEY_FILE, "rb") as key_file:
        key = key_file.read()

cipher = Fernet(key)

def init_db():
    conn = sqlite3.connect("bot.db")
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            content TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def save_message(chat_id, content):
    encrypted = cipher.encrypt(content.encode('utf-8'))
    conn = sqlite3.connect("bot.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO messages (chat_id, content) VALUES (?, ?)", (chat_id, encrypted))
    conn.commit()
    conn.close()

def get_messages(chat_id):
    conn = sqlite3.connect("bot.db")
    cur = conn.cursor()
    cur.execute("SELECT content FROM messages WHERE chat_id=?", (chat_id,))
    rows = cur.fetchall()
    conn.close()
    return [cipher.decrypt(row[0]).decode('utf-8') for row in rows]