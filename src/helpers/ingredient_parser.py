import logging

def parse_ingredients(ingredients_str: str) -> list[str]:
    ingredients = [ing.strip() for ing in ingredients_str.split(',')]
    logging.info(f"Parsed ingredients: {ingredients}")
    return ingredients
