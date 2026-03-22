import os
import uuid
import asyncio

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup

from search_engine import find_relevant_chunks, format_citations
from keyboards import start_keyboard, main_menu_kb, back_menu_kb, cancel_kb

from ai_generators import generate
from context import ContexManager

from db.book_repository import (
    add_book_to_db,
    check_book_exists,
    add_paragraph_to_db,
    get_all_books
)

from search.embeddings import get_embedding

from search.qdrant_service import add_to_qdrant

from text.text_utils import (
    normalize_title,
    split_text_to_paragraphs
)

from text.file_utils import read_file

user_router = Router()
context_mgr = ContexManager()


class AddBookStates(StatesGroup):
    waiting_for_file = State()
    waiting_for_title = State()


class SearchStates(StatesGroup):
    waiting_for_query = State()


class QAStates(StatesGroup):
    waiting_for_question = State()


class LibraryState(StatesGroup):
    viewing = State()


async def delete_messages(*messages):
    for msg in messages:
        if msg:
            try:
                await msg.delete()
            except Exception:
                pass


@user_router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        f"👋 Привет, <b>{message.from_user.first_name}</b>!\n"
        f"Я бот-библиотекарь. Нажми кнопку <b>Меню</b>, чтобы начать.",
        reply_markup=start_keyboard,
        parse_mode="HTML"
    )


@user_router.message(F.text == "Меню")
async def show_menu(message: Message):
    await message.answer("📚 Главное меню", reply_markup=main_menu_kb)


@user_router.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await delete_messages(callback.message)


@user_router.callback_query(F.data == "back_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    current_state = await state.get_state()
    await state.clear()

    if current_state == LibraryState.viewing.state:
        await callback.message.edit_text("📚 Главное меню", reply_markup=main_menu_kb)
        return

    await callback.message.answer("📚 Главное меню", reply_markup=main_menu_kb)


@user_router.callback_query(F.data == "library")
async def library_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(LibraryState.viewing)

    books = await get_all_books()

    if not books:
        text = "📭 Библиотека пуста"
    else:
        book_list = "\n".join([f"📗 {book}" for book in books])
        text = f"📚 <b>Моя библиотека:</b>\n\n{book_list}"

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_menu_kb)


@user_router.callback_query(F.data == "add_book")
async def add_book_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(AddBookStates.waiting_for_file)

    await callback.message.answer(
        "📤 Отправьте книгу в формате txt-файла",
        reply_markup=cancel_kb
    )


@user_router.message(F.document, AddBookStates.waiting_for_file)
async def receive_file(message: Message, state: FSMContext):
    doc = message.document

    if not doc.file_name.endswith(".txt"):
        await message.answer("❌ Нужен файл формата .txt")
        return

    if doc.file_size > 10_000_000:
        await message.answer("❌ Файл слишком большой (макс. 10 МБ)")
        return

    file_info = await message.bot.get_file(doc.file_id)
    temp_path = f"temp_{uuid.uuid4()}.txt"
    await message.bot.download_file(file_info.file_path, temp_path)

    await message.answer("✏️ Введите название книги")
    await state.update_data(temp_file=temp_path)
    await state.set_state(AddBookStates.waiting_for_title)


@user_router.message(AddBookStates.waiting_for_title)
async def receive_title(message: Message, state: FSMContext):
    title = message.text
    normalized = normalize_title(title)

    data = await state.get_data()
    temp_file = data["temp_file"]

    if await check_book_exists(normalized):
        os.remove(temp_file)
        await state.clear()
        await message.answer("⚠️ Книга уже есть в библиотеке", reply_markup=back_menu_kb)
        return

    book_id, book_uuid, path = await add_book_to_db(title, normalized)
    os.rename(temp_file, path)

    status_msg = await message.answer("📖 Начинаю обработку книги...")
    timer_msg = await message.answer("⏳")
    await state.clear()

    task = asyncio.create_task(process_book(
        book_id,
        book_uuid,
        title,
        path,
        message.chat.id,
        message.bot,
        status_msg,
        timer_msg
    ))


async def process_book(book_id, book_uuid, title, path, chat_id, bot, status_msg, timer_msg):
    text = read_file(path)
    paragraphs = split_text_to_paragraphs(text)

    for idx, para in enumerate(paragraphs):
        compressed = para["text"][:400]
        embedding = get_embedding(compressed)
        pid = str(uuid.uuid4())

        payload = {
            "book_id": book_id,
            "book_uuid": book_uuid,
            "book_title": title,
            "chapter_number": 0,
            "paragraph_index": idx,
            "char_start": para["char_start"],
            "char_end": para["char_end"]
        }

        add_to_qdrant(pid, embedding, payload)
        await add_paragraph_to_db(
            book_id, 0, 0, idx,
            para["char_start"], para["char_end"], pid
        )

    await delete_messages(status_msg, timer_msg)
    await bot.send_message(
        chat_id,
        f"✅ Книга «{title}» обработана!",
        reply_markup=back_menu_kb
    )


@user_router.callback_query(F.data == "search")
async def search_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(SearchStates.waiting_for_query)

    await callback.message.answer(
        "🔍 Введите запрос для поиска цитат",
        reply_markup=cancel_kb
    )


@user_router.message(SearchStates.waiting_for_query)
async def search(message: Message, state: FSMContext):
    query = message.text
    await state.clear()

    timer_msg = await message.answer("⏳")

    top_chunks = find_relevant_chunks(query, limit=5)
    if not top_chunks:
        await delete_messages(timer_msg)
        await message.answer("😕 Подходящих цитат не найдено", reply_markup=back_menu_kb)
        return

    ans = "📚 <b>Найденные цитаты:</b>\n\n" + format_citations(top_chunks)

    await delete_messages(timer_msg)
    await message.answer(ans, parse_mode="HTML", reply_markup=back_menu_kb)


@user_router.callback_query(F.data == "qa")
async def qa_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(QAStates.waiting_for_question)

    await callback.message.answer(
        "❓ Введите ваш вопрос",
        reply_markup=cancel_kb
    )


@user_router.message(QAStates.waiting_for_question)
async def process_question(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_question = message.text
    await state.clear()

    timer_msg = await message.answer("⏳")

    top_chunks = find_relevant_chunks(user_question, limit=10)
    if not top_chunks:
        await delete_messages(timer_msg)
        await message.answer(
            "😕 К сожалению, подходящей информации нет в моей базе",
            reply_markup=back_menu_kb
        )
        return

    citations_text = format_citations(top_chunks)
    user_message = {
        'role': 'user',
        'content': f"Вопрос: {user_question}\n\nИспользуй только эти цитаты:\n{citations_text}"
    }

    context_mgr.add_message(user_id, user_message)
    messages = context_mgr.get_context(user_id)

    answer = await generate(messages)
    context_mgr.add_message(user_id, {'role': 'assistant', 'content': answer})

    await delete_messages(timer_msg)
    await message.answer(answer, parse_mode="Markdown", reply_markup=back_menu_kb)
