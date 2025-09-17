import asyncio
import os
from typing import Dict, Optional
from urllib.parse import unquote, urlparse

import aiohttp

BASE_URL = os.getenv("API_BASE_URL") or "http://127.0.0.1:8000"
CATEGORY_SEMAPHORE = asyncio.Semaphore(5)


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


def parse_proxy_url(proxy_url: str) -> Dict[str, Optional[str]]:
    """
    Разбирает proxy URL в словарь с параметрами прокси.

    Args:
        proxy_url: URL прокси в формате scheme://[username:password@]hostname:port

    Returns:
        Словарь с параметрами прокси:
        {
            "scheme": "socks5" или "http",
            "hostname": "хост",
            "port": "порт",
            "username": "логин" или None,
            "password": "пароль" или None
        }

    Raises:
        ValueError: Если URL имеет неверный формат
    """
    try:
        parsed = urlparse(proxy_url)

        if not parsed.scheme:
            raise ValueError("Proxy URL должен содержать схему (socks5:// или http://)")

        if not parsed.hostname:
            raise ValueError("Proxy URL должен содержать hostname")

        if not parsed.port:
            raise ValueError("Proxy URL должен содержать порт")

        # Получаем логин и пароль из URL
        username = parsed.username
        password = parsed.password

        # Декодируем username и password если они закодированы
        if username:
            username = unquote(username) if '%' in username else username
        if password:
            password = unquote(password) if '%' in password else password

        return {
            "scheme": parsed.scheme,
            "hostname": parsed.hostname,
            "port": str(parsed.port),
            "username": username,
            "password": password
        }

    except Exception as e:
        raise ValueError(f"Неверный формат proxy URL: {e}")
