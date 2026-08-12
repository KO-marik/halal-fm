import aiosqlite

DB_NAME = "music_bot.db"

async def init_db():
    """Инициализация таблиц базы данных"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tracks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                performer TEXT NOT NULL,
                file_path TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY,
                is_loop INTEGER DEFAULT 0,
                current_track_id INTEGER DEFAULT NULL,
                active_chat_id INTEGER DEFAULT NULL
            )
        """)
        await db.execute("INSERT OR IGNORE INTO settings (id, is_loop) VALUES (1, 0)")
        await db.commit()

async def add_track(title: str, performer: str, file_path: str) -> int:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "INSERT INTO tracks (title, performer, file_path) VALUES (?, ?, ?)",
            (title, performer, file_path)
        )
        await db.commit()
        return cursor.lastrowid

async def get_all_tracks():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM tracks ORDER BY id DESC") as cursor:
            return await cursor.fetchall()

async def get_track(track_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM tracks WHERE id = ?", (track_id,)) as cursor:
            return await cursor.fetchone()

async def delete_track(track_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM tracks WHERE id = ?", (track_id,))
        await db.commit()

async def toggle_loop():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE settings SET is_loop = NOT is_loop WHERE id = 1")
        await db.commit()
        async with db.execute("SELECT is_loop FROM settings WHERE id = 1") as cursor:
            res = await cursor.fetchone()
            return bool(res[0])

async def get_settings():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM settings WHERE id = 1") as cursor:
            return await cursor.fetchone()

async def set_active_play(track_id: int, chat_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE settings SET current_track_id = ?, active_chat_id = ? WHERE id = 1", (track_id, chat_id))
        await db.commit()
