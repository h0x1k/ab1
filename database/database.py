import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

DB_NAME = "users.db"


def init_db():
    """Создание таблиц, если их нет."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_id INTEGER UNIQUE,
        username TEXT,
        full_name TEXT,
        sub_end_date DATE,
        enabled BOOLEAN DEFAULT TRUE
    );

    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    );

    CREATE TABLE IF NOT EXISTS channels (
        id INTEGER PRIMARY KEY,
        title TEXT,
        status BOOLEAN DEFAULT FALSE
    );

    CREATE TABLE IF NOT EXISTS matches (
        id INTEGER PRIMARY KEY,
        date DATETIME
    );                   
    """)

    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?);", ("frequency", "60"))
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?);", ("dates", "15:00-20:00"))
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?);", ("diff", "0.2"))
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?);", ("pinnacle_koef_interval", "0:100"))
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?);", ("others_koef_interval", "0:100"))
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?);", ("timezone", "Europe/Kyiv"))
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?);", ("parsing", "False"))
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?);", ("analytics", "False"))
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?);", ("football", "False"))
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?);", ("basketball", "False"))
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?);", ("tennis", "False"))
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?);", ("hockey", "False"))
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?);", ("volleyball", "False"))
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?);", ("dota2", "False"))
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?);", ("cs", "False"))
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?);", ("last_date", ""))
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?);", ("last_num", "0"))

    conn.commit()
    conn.close()


def add_user(tg_id, username, full_name):
    """Добавление нового пользователя."""
    timezone = get_settings_value("timezone")
    now = datetime.now(ZoneInfo(timezone)).date()

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("INSERT OR IGNORE INTO users (tg_id, username, full_name, sub_end_date) VALUES (?, ?, ?, ?)", (tg_id, username, full_name, now))
    conn.commit()
    conn.close()


def get_allowed_users():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT tg_id FROM users WHERE enabled = True")
        result = cursor.fetchall()
        if result is None:
            return []
        users = [row[0] for row in result]
        allowed_users = []
        for user in users:
            if get_user_days(user) > 0:
                allowed_users.append(user)
    return allowed_users
    

def get_user_days(tg_id):
    """Получить количество дней подписки у пользователя."""
    timezone = get_settings_value("timezone")
    now = datetime.now(ZoneInfo(timezone)).date()
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT sub_end_date FROM users WHERE tg_id = ?", (tg_id,))
        query = cursor.fetchone()
        result = 0
        if query and query[0]:
            end_date = datetime.fromisoformat(query[0]).date()
            result = (end_date - now).days
        return result if result > 0 else 0


def update_subscription(tg_id, days):
    """Выдача подписки пользователю (увеличение дней)."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET sub_end_date = DATE(sub_end_date, ?) WHERE tg_id = ?", (f"+{days} days", tg_id))
        conn.commit()


def update_enabled(tg_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Сначала получаем текущее значение
    cursor.execute("SELECT enabled FROM users WHERE tg_id = ?", (tg_id,))
    # Получаем текущее значение (0 или 1)
    current_enabled = cursor.fetchone()[0]

    # Инвертируем значение и обновляем
    new_enabled = 1 if current_enabled == 0 else 0
    cursor.execute(
        "UPDATE users SET enabled = ? WHERE tg_id = ?",
        (new_enabled, tg_id)
    )

    conn.commit()
    conn.close()

    return new_enabled  # Возвращаем новое значение (1 или 0)
    

def remove_subscription(tg_id):
    """Убираем подписку"""
    timezone = get_settings_value("timezone")
    now = datetime.now(ZoneInfo(timezone)).date()
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET sub_end_date = ? WHERE tg_id = ?", (now, tg_id))
        conn.commit()

def update_settings(key: str, value: str):
    """Обновляем настройки"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET value = ? WHERE key = ?", (value, key))
    conn.commit()
    conn.close()

def get_settings_value(key: str):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT value FROM settings WHERE key = ?", (key,))
        result = cursor.fetchone()
        if result is None:
            return None
    return result[0]

def add_channel(channel):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO channels (id, title) VALUES (?, ?)", channel)
    conn.commit()
    conn.close()

def get_channels_list():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM channels")
    result = cursor.fetchall()
    conn.commit()
    conn.close()
    return result

def get_allowed_channels():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM channels WHERE status = True")
        result = cursor.fetchall()
        if result is None:
            return []
    return [row[0] for row in result]

def udpate_channels(channel_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    result = cursor.execute(f"SELECT status FROM channels WHERE id = {channel_id}").fetchone()[0]
    cursor.execute(f"UPDATE channels SET status = {not result} WHERE id = {channel_id}")
    conn.commit()
    conn.close()

def delete_channel(channel_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM channels WHERE id = {channel_id}")
    conn.commit()
    conn.close()

def add_match(match_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO matches (id, date) VALUES (?, datetime('now'))", (match_id,))
    conn.commit()
    conn.close()

def get_matches():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM matches WHERE date < datetime('now', '-1 day')")
        conn.commit()
        cursor.execute("SELECT id FROM matches")
        result = cursor.fetchall()
        if result is None:
            return []
    return [row[0] for row in result]