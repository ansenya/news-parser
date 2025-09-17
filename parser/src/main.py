import logging
import os
import sqlite3
import time

import pyrogram
from pyrogram import Client, filters
from message_service import save_news
from utils import parse_proxy_url

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
CHANNEL = os.getenv("CHANNEL", "bbbreaking")  # по дефолту парсим "Раньше всех. Ну почти"

SESSION_NAME = "parser" if os.getenv("APP_ENV") == "prod" else "/app/sessions/parser.session"

app = Client(SESSION_NAME,
             api_id=API_ID,
             api_hash=API_HASH,
             app_version="news",
             system_version="",
             sleep_threshold=60,
             proxy=parse_proxy_url(os.getenv("PROXY_URL")), )

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

last_reaction = 0
REACTION_COOLDOWN = 3  # секунды между реакциями


async def safe_react(message, emoji):
    global last_reaction
    now = time.time()
    if now - last_reaction > REACTION_COOLDOWN:
        await message.react(emoji)
        last_reaction = now


@app.on_message(filters.chat(CHANNEL))
async def handle_new_message(client, message: pyrogram.types.Message):
    try:
        await save_news(message)
        await safe_react(message, "👌")
    except sqlite3.IntegrityError:
        await safe_react(message, "🗿")
    except RuntimeError as e:
        logger.warning(f"Не получилось получить категорию: {e}")
        await safe_react(message, "👎")
    except Exception as e:
        logger.error(f"Неизвестная ошибка: {e}")
        await safe_react(message, "👎")


if __name__ == "__main__":
    print("Parser started. Listening for new messages...")
    app.run()
