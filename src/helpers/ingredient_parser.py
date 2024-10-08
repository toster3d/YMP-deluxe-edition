def parse_ingredients(ingredients_string: str) -> list[str]:
    return [ing.strip() for ing in ingredients_string.split("\n") if ing.strip()]
