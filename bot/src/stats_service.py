from aiogram.types import Message

import db


async def handle_stats_command(message: Message):
    stats = db.get_news_count_by_weekday()

    data = ""
    for stat in stats:
        data += f"{stat[0]}: {stat[1]}\n"

    await message.answer(data)
