import asyncio
import logging
import os
import sqlite3
import sys
from html import escape

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReactionTypeEmoji

from csv_service import handle_data_command
from message_service import save_news
from db import CATEGORY_INNER, CATEGORY_OUTER, init_db

TOKEN = os.getenv("BOT_TOKEN")

dp = Dispatcher()


@dp.message(CommandStart())
async def handle_start(message: Message) -> None:
    await message.answer(
        f"Команды:\n/summary\n/summary internal\n/summary external\n\n/news\n/news internal\n/news external")


@dp.message(Command('summary'))
async def handle_summary(message: Message):
    args = message.text.split()

    category = None
    if len(args) > 1:
        arg = args[1].lower()
        if arg in ['inner', 'внутренние', 'internal']:
            category = CATEGORY_INNER
        elif arg in ['outer', 'внешние', 'external']:
            category = CATEGORY_OUTER

    await handle_data_command(message, 'summary', category)


@dp.message(Command('news'))
async def handle_csv(message: Message):
    args = message.text.split()

    category = None
    if len(args) > 1:
        arg = args[1].lower()
        if arg in ['inner', 'внутренние', 'internal']:
            category = CATEGORY_INNER
        elif arg in ['outer', 'внешние', 'external']:
            category = CATEGORY_OUTER

    await handle_data_command(message, 'news', category)


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
