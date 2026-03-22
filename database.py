import aiosqlite
from config import DB_PATH


async def init_db():

    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE,
            title TEXT,
            normalized_title TEXT UNIQUE,
            file_path TEXT
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS paragraphs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER,
            part_number INTEGER,
            chapter_number INTEGER,
            paragraph_index INTEGER,
            char_start INTEGER,
            char_end INTEGER,
            qdrant_point_id TEXT
        )
        """)

        await db.commit()