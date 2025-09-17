import math
import time
from random import random, randint

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

import llm

app = FastAPI()


class NewsItem(BaseModel):
    text: str
    date: str


class ClassificationRequest(BaseModel):
    news_items: List[NewsItem]


class ClassificationResponse(BaseModel):
    categories: List[str]  # ['внутренняя', 'внешняя', ...]


class SummaryRequest(BaseModel):
    news_items: List[NewsItem]
    category: str


class SummaryResponse(BaseModel):
    summary: str


@app.post("/classify_news")
async def classify_news(request: ClassificationRequest):
    categories = []
    for news in request.news_items:
        category = await llm.classify(news.text)
        categories.append(category)

    return ClassificationResponse(categories=categories)


@app.post("/generate_summary")
async def generate_summary(request: SummaryRequest):
    """Сгенерировать сводку для новостей категории"""
    # Фильтруем новости по категории (на случай если пришли все)
    # filtered_news = [news for news in request.news_items
    #                  if await llm.classify(news.text) == request.category]

    # Генерируем сводку
    summary = await llm.generate_summary(request.news_items, request.category)

    return SummaryResponse(summary=summary)
