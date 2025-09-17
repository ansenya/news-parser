from aiogram.types import Message
from utils import get_category

from zoneinfo import ZoneInfo
import db


async def save_news(message: Message):
    text = message.text or message.caption
    date = message.forward_origin.date.astimezone(ZoneInfo('Europe/Moscow'))
    category = await get_category(text, date)
    db.save_news(date, text, category)
