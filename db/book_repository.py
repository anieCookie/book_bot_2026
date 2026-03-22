import uuid
import os
import aiosqlite

from config import DB_PATH, BOOKS_DIR


async def check_book_exists(normalized_title):

    async with aiosqlite.connect(DB_PATH) as db:

        async with db.execute(
            "SELECT id FROM books WHERE normalized_title=?",
            (normalized_title,)
        ) as cur:

            return await cur.fetchone() is not None


async def add_book_to_db(title, normalized_title):

    book_uuid = str(uuid.uuid4())
    path = os.path.join(BOOKS_DIR, f"{book_uuid}.txt")

    async with aiosqlite.connect(DB_PATH) as db:

        cur = await db.execute(
            "INSERT INTO books (uuid,title,normalized_title,file_path) VALUES (?,?,?,?)",
            (book_uuid, title, normalized_title, path)
        )

        await db.commit()

        return cur.lastrowid, book_uuid, path


async def add_paragraph_to_db(book_id, part, chapter, idx, start, end, qid):

    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute(
            """
            INSERT INTO paragraphs
            (book_id,part_number,chapter_number,paragraph_index,char_start,char_end,qdrant_point_id)
            VALUES (?,?,?,?,?,?,?)
            """,
            (book_id, part, chapter, idx, start, end, qid)
        )

        await db.commit()


async def get_all_books():

    async with aiosqlite.connect(DB_PATH) as db:

        async with db.execute("SELECT title FROM books") as cur:

            rows = await cur.fetchall()

            return [r[0] for r in rows]
