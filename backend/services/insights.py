PROBLEM_RECOMMENDATIONS = {
    "packaging": "Проверить упаковку товара и качество защиты при доставке",
    "delivery": "Проверить сроки и надежность логистики",
    "quality": "Проверить качество товара, процент брака и соответствие описанию",
    "price": "Проверить ценовое позиционирование товара",
    "usability": "Улучшить инструкцию, описание или удобство использования",
    "support": "Улучшить скорость и качество ответов поддержки",
}

ASPECT_NAMES = {
    "quality": "качеством товара",
    "delivery": "доставкой",
    "packaging": "упаковкой",
    "price": "ценой",
    "usability": "удобством использования",
    "support": "поддержкой",
}


def generate_insights(stats: dict, problems: dict) -> dict:
    """Build simple business insights from sentiment stats and top problems."""
    negative_percentage = float(stats.get("negative_percentage", 0.0))
    risk_level = calculate_risk_level(negative_percentage)
    problem_rows = problems.get("problems", [])

    if problem_rows:
        top_problem = problem_rows[0]
        aspect = top_problem["aspect"]
        aspect_name = ASPECT_NAMES.get(aspect, aspect)
        summary = (
            f"Основная проблема товара связана с {aspect_name}: "
            f"{top_problem['count']} негативных упоминаний "
            f"({top_problem['percentage']}%). Общая доля негативных отзывов: "
            f"{negative_percentage}%."
        )
    else:
        summary = (
            "Явных повторяющихся негативных аспектов пока не найдено. "
            f"Общая доля негативных отзывов: {negative_percentage}%."
        )

    recommendations = build_recommendations(problem_rows, risk_level)

    return {
        "summary": summary,
        "recommendations": recommendations,
        "risk_level": risk_level,
    }


def calculate_risk_level(negative_percentage: float) -> str:
    """Classify business risk from the share of negative reviews."""
    if negative_percentage > 40:
        return "high"
    if negative_percentage >= 20:
        return "medium"
    return "low"


def build_recommendations(problem_rows: list[dict], risk_level: str) -> list[str]:
    """Choose recommendations for the most frequent negative aspects."""
    recommendations = [
        PROBLEM_RECOMMENDATIONS[row["aspect"]]
        for row in problem_rows
        if row["aspect"] in PROBLEM_RECOMMENDATIONS
    ]

    if not recommendations:
        if risk_level == "low":
            return ["Продолжать мониторинг отзывов и проверять новые негативные сигналы"]
        return ["Провести ручной разбор негативных отзывов без явной аспектной причины"]

    return recommendations
