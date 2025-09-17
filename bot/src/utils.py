import asyncio
import csv
import os
from io import BytesIO, TextIOWrapper
from typing import List

import aiohttp

BASE_URL = os.getenv("API_BASE_URL") or "http://127.0.0.1:8000"
CATEGORY_SEMAPHORE = asyncio.Semaphore(5)


def news_to_csv_file(rows, filename="news.csv"):
    buffer = BytesIO()

    # Создаем writer с правильной кодировкой
    wrapper = TextIOWrapper(buffer, encoding='utf-8', newline='')
    writer = csv.writer(wrapper)

    # Записываем заголовок
    writer.writerow(['Date', 'Text', 'Category'])

    # Записываем данные
    for row in rows:
        writer.writerow(row)

    # Важно: отключаем wrapper чтобы буфер был чистым
    wrapper.detach()
    buffer.seek(0)
    buffer.name = filename

    return buffer


async def get_category(text, date):
    async with CATEGORY_SEMAPHORE:
        data = {
            "news_items": [
                {
                    "text": text,
                    "date": date.isoformat(),
                }
            ],
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{BASE_URL}/classify_news", json=data) as response:
                if response.status != 200:
                    raise RuntimeError(await response.text())
                resp_json = await response.json()
                return resp_json["categories"][0]


async def get_summary(news: List, category: str):
    data = {
        "news_items": news,
        "category": category,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BASE_URL}/generate_summary", json=data) as response:
            if response.status != 200:
                raise RuntimeError(await response.text())
            resp_json = await response.json()
            return resp_json["summary"]
