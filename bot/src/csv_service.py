from aiogram.types import BufferedInputFile, Message
from utils import news_to_csv_file
from db import get_news_by_week, get_summary_by_week, CATEGORY_INNER, CATEGORY_OUTER
from typing import Optional, List, Tuple


async def handle_data_command(
        message: Message,
        data_type: str,  # 'news' или 'summary'
        category: Optional[str] = None
):
    """
    Универсальный обработчик для новостей и сводок
    """
    # Выбираем функцию для получения данных
    if data_type == 'news':
        data_func = get_news_by_week
        data_name = 'новостей'
        base_filename = "news"
    else:
        data_func = get_summary_by_week
        data_name = 'сводок'
        base_filename = "summary"

    # Получаем данные
    data = data_func(category=category)

    if not data:
        category_text = get_category_display_name(category)
        await message.answer(f'{data_name.capitalize()} {category_text} за прошедшую неделю нет.')
        return

    # Создаем CSV файл
    filename = generate_filename(base_filename, category)
    csv_buffer = news_to_csv_file(data, filename)

    # Формируем caption
    category_text = get_category_display_name(category)
    record_count = f" ({len(data)} записей)" if data_type == 'news' else ""
    caption = f"{category_text.capitalize()} {data_name} за прошедшую неделю{record_count}"

    # Отправляем файл
    csv_file = BufferedInputFile(csv_buffer.getvalue(), filename)
    await message.answer_document(document=csv_file, caption=caption)


def get_category_display_name(category: Optional[str]) -> str:
    """Получить отображаемое имя категории"""
    category_map = {
        CATEGORY_INNER: "внутренние",
        CATEGORY_OUTER: "внешние",
        None: "все"
    }
    return category_map.get(category, "все")


def generate_filename(base_name: str, category: Optional[str]) -> str:
    """Сгенерировать имя файла в зависимости от категории"""
    suffix_map = {
        CATEGORY_INNER: "_internal",
        CATEGORY_OUTER: "_external",
        None: ""
    }
    suffix = suffix_map.get(category, "")
    return f"{base_name}_last_week{suffix}.csv"
