def parse_ingredients(ingredients_string: str) -> list[str]:
    """
    Parse a string of ingredients into a list of individual ingredients.

    Args:
        ingredients_string (str): A string containing ingredients,
                                  typically separated by newlines.

    Returns:
        List[str]: A list of individual ingredients, with leading and
                   trailing whitespace removed.

    Example:
        >>> parse_ingredients("flour\n  sugar \nsalt  ")
        ['flour', 'sugar', 'salt']
    """
    return [ing.strip() for ing in ingredients_string.split("\n") if ing.strip()]
