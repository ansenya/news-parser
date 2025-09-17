import asyncio
import sqlite3

from aiogram.types import Message
from utils import get_category

from zoneinfo import ZoneInfo
import db

db_lock = asyncio.Lock()


async def save_news(message: Message):
    text = message.text or message.caption
    if db.news_exists(text):
        raise sqlite3.IntegrityError
    date = message.forward_origin.date.astimezone(ZoneInfo('Europe/Moscow'))
    category = await get_category(text, date)
    async with db_lock:
        db.save_news(date, text, category)
