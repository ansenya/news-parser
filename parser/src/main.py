import os
import random
import asyncio
from pyrogram import Client, filters

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
CHANNEL = os.getenv("CHANNEL", "bbbreaking")  # по дефолту парсим "Раньше всех. Ну почти"
BOT_USERNAME = os.getenv("BOT_USERNAME", "@newsdudebot")

app = Client("parser", api_id=API_ID, api_hash=API_HASH)


@app.on_message(filters.chat(CHANNEL))
async def handle_new_message(client, message):
    if message.text:
        delay = random.randint(10, 30)
        print(f"[DELAY] Ждём {delay} секунд перед пересылкой...")
        await asyncio.sleep(delay)
        await message.forward(BOT_USERNAME)


if __name__ == "__main__":
    print("Parser started. Listening for new messages...")
    app.run()
