from db import get_news_by_week, get_summary_by_week, CATEGORY_INNER, CATEGORY_OUTER
from utils import get_summary


def generate_summary(category: str, year: int = None, week: int = None):
    summary = get_summary_by_week(year, week, category)
    if summary:
        return "Сводка уже создана"

    news = get_news_by_week(year, week, category)
    if not news:
        raise RuntimeError("Новостей нет - сделать сводку не на чем")

    summary = get_summary([{"date": element[0], "text": element[1]} for element in news], category)

    return summary


if __name__ == "__main__":
    result = generate_summary(CATEGORY_INNER)
    print(result)
