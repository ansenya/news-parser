import asyncio
import logging
import os
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from html import escape

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReactionTypeEmoji, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from csv_service import handle_csv_command
from message_service import save_news
from db import init_db

TOKEN = os.getenv("BOT_TOKEN")

dp = Dispatcher()
news_type_russian = {
    "all": "новости всех политик",
    "internal": "новости внутренней политики",
    "external": "новости внешней политики",
}
tz_moscow = timezone(timedelta(hours=3))


@dp.message(CommandStart())
async def handle_start(message: Message) -> None:
    await message.answer(
        "/csv - скачать новости в формате csv"
    )


@dp.message(Command('csv'))
async def handle_csv(message: Message):
    from_date = (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7)).astimezone(
        tz_moscow)
    to_date = datetime.today().replace(hour=23, minute=59, second=59, microsecond=9999).astimezone(tz_moscow)
    news_type = 'all'  # all/internal/external

    keyboard = build_keyboard(from_date, to_date, news_type)

    await message.answer(
        "Скачать новости в формате csv:\n"
        f"С даты: {from_date}\n"
        f"До даты: {to_date}\n"
        f"Тип новостей: {news_type_russian[news_type]}\n\n"
        "📥 Скачать — получить CSV\n"
        "🔄 Тип — поменять фильтр (all/internal/external)\n"
        "⏪⏩ From — изменить начальную дату\n"
        "⏪⏩ To — изменить конечную дату",
        reply_markup=keyboard
    )


@dp.callback_query()
async def callbacks_handler(callback: CallbackQuery):
    data = callback.data.split()
    cmd = data[0]

    from_date = datetime.fromisoformat(data[1]).astimezone(tz_moscow)
    to_date = datetime.fromisoformat(data[2]).replace(hour=23, minute=59, second=59, microsecond=999999).astimezone(
        tz_moscow)
    news_type = data[3]

    if cmd == "download":
        await handle_csv_command(callback, news_type, from_date, to_date)
    elif cmd == "change_type":
        new_type = {
            "all": "internal",
            "internal": "external",
            "external": "all",
        }[news_type]

        keyboard = build_keyboard(from_date, to_date, new_type)

        await callback.message.edit_text(
            "Скачать новости в формате csv:\n"
            f"С даты: {from_date}\n"
            f"До даты: {to_date}\n"
            f"Тип новостей: {news_type_russian[new_type]}\n\n"
            "📥 Скачать — получить CSV\n"
            "🔄 Тип — поменять фильтр (all/internal/external)\n"
            "⏪⏩ From — изменить начальную дату\n"
            "⏪⏩ To — изменить конечную дату",
            reply_markup=keyboard
        )
    elif cmd in ("decrease_from_date", "increase_from_date",
                 "decrease_to_date", "increase_to_date"):
        if cmd == "decrease_from_date":
            from_date = from_date - timedelta(days=1)
        elif cmd == "increase_from_date":
            from_date = from_date + timedelta(days=1)
        elif cmd == "decrease_to_date":
            to_date = to_date - timedelta(days=1)
        elif cmd == "increase_to_date":
            to_date = to_date + timedelta(days=1)

        keyboard = build_keyboard(from_date, to_date, news_type)

        await callback.message.edit_text(
            "Скачать новости в формате csv:\n"
            f"С даты: {from_date}\n"
            f"До даты: {to_date}\n"
            f"Тип новостей: \n\n"
            "📥 Скачать — получить CSV\n"
            "🔄 Тип — поменять фильтр (all/internal/external)\n"
            "⏪⏩ From — изменить начальную дату\n"
            "⏪⏩ To — изменить конечную дату",
            reply_markup=keyboard
        )

        # обязательно подтверждаем callback (иначе "часики")
    await callback.answer()


def build_keyboard(from_date: datetime, to_date: datetime, news_type: str):
    from_date = from_date.date().isoformat()
    to_date = to_date.date().isoformat()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📥 Скачать",
                    callback_data=f"download {from_date} {to_date} {news_type}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Поменять тип",
                    callback_data=f"change_type {from_date} {to_date} {news_type}"
                )
            ],
            [
                InlineKeyboardButton(text="⏪ From -",
                                     callback_data=f"decrease_from_date {from_date} {to_date} {news_type}"),
                InlineKeyboardButton(text="From + ⏩",
                                     callback_data=f"increase_from_date {from_date} {to_date} {news_type}"),
            ],
            [
                InlineKeyboardButton(text="⏪ To -",
                                     callback_data=f"decrease_to_date {from_date} {to_date} {news_type}"),
                InlineKeyboardButton(text="To + ⏩",
                                     callback_data=f"increase_to_date {from_date} {to_date} {news_type}"),
            ],
        ]
    )


@dp.message()
async def handle_message(message: Message):
    if message.forward_origin.chat.username == "bbbreaking":
        try:
            await save_news(message)
            await message.react([ReactionTypeEmoji(emoji="👌")])
        except sqlite3.IntegrityError:
            await message.react([ReactionTypeEmoji(emoji="🗿")])
        except RuntimeError as e:
            error_msg = escape(str(e))
            await message.reply(f"Не получилось получить категорию: {error_msg}",
                                disable_notification=True)
        except Exception as e:
            error_msg = escape(str(e))
            await message.reply(f'Неизвестная ошибка: {error_msg}',
                                disable_notification=True)


async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    init_db()
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
