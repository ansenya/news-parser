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
from stats_service import handle_stats_command
from db import CATEGORY_INNER, CATEGORY_OUTER, init_db

TOKEN = os.getenv("BOT_TOKEN")

dp = Dispatcher()


@dp.message(CommandStart())
async def handle_start(message: Message) -> None:
    await message.answer(
        "Доступные команды:\n\n"
        "/summary - сводка (пока в разработке, может работать некорректно)\n"
        "/summary_internal - внутренняя сводка (в разработке)\n"
        "/summary_external - внешняя сводка (в разработке)\n\n"
        "/news - новости\n"
        "/news_internal - внутренние новости\n"
        "/news_external - внешние новости\n\n"
        "/stats - статистика по дням и новостям"
    )


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


@dp.message(Command('summary_internal'))
async def handle_summary(message: Message):
    await handle_data_command(message, 'summary', CATEGORY_INNER)


@dp.message(Command('summary_external'))
async def handle_summary(message: Message):
    await handle_data_command(message, 'summary', CATEGORY_OUTER)


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


@dp.message(Command('news_internal'))
async def handle_csv(message: Message):
    await handle_data_command(message, 'news', CATEGORY_INNER)


@dp.message(Command('news_external'))
async def handle_csv(message: Message):
    await handle_data_command(message, 'news', CATEGORY_OUTER)


@dp.message(Command('stats'))
async def handle_stats(message: Message):
    await handle_stats_command(message)


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
