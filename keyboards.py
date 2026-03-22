from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)

start_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Меню")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

main_menu_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📚 Добавить книгу", callback_data="add_book")],
        [InlineKeyboardButton(text="🔍 Поиск цитат", callback_data="search")],
        [InlineKeyboardButton(text="❓ Ответы на вопросы", callback_data="qa")],
        [InlineKeyboardButton(text="📖 Моя библиотека", callback_data="library")]
    ]
)

back_menu_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Вернуться в меню", callback_data="back_menu")]
    ]
)

cancel_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
    ]
)