import os

import httpx
from openai import AsyncOpenAI

CATEGORY_INNER = "внутренняя"
CATEGORY_OUTER = "внешняя"


async def classify(text):
    async with AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            http_client=httpx.AsyncClient(proxy=os.getenv("PROXY_URL")),
    ) as client:
        response = await client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Ты помощник для классификации новостей. "
                               "Ты определяешь относится ли новость к внутренней политике или ко внешней. "
                               "Новости Российские. "
                               "Отвечай только одно слово без любых других знаков и/или форматов: `внутренняя` или `внешняя`.",
                },
                {
                    "role": "user",
                    "content": text,
                }
            ],
            model="gpt-4o-mini",
        )
        return response.choices[0].message.content


async def generate_summary(filtered_news, category):
    async with AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            http_client=httpx.AsyncClient(proxy=os.getenv("PROXY_URL")),
    ) as client:
        if category == CATEGORY_INNER:
            category_rus = "внутренней"
        else:
            category_rus = "внешней"
        messages = [
            {
                "role": "system",
                "content": f"Ты генерируешь сводку новостей {category_rus} политики. "
                           "Пиши настолько кратко, насколько можно писать не теряя детали. "
                           f"Презентация на тему {category_rus} политики за прошедшую неделю, сводки новостей должно хватить на несколько слайдов и 5 минут времени."
            }
        ]
        for news in filtered_news:
            messages.append({"role": "user", "content": news.text})
        response = await client.chat.completions.create(
            messages=messages,
            model="gpt-4o-mini",
        )
        return response.choices[0].message.content
