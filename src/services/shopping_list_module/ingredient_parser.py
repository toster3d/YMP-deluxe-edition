from typing import List


class IngredientParser:
    """
    A utility class for parsing ingredient strings into a list of ingredients.
    """

    @staticmethod
    def parse_ingredients(ingredients_string: str) -> List[str]:
        """
        Parse a string of ingredients into a list of individual ingredients.

        Args:
            ingredients_string (str): A string containing ingredients,
                                      typically separated by newlines.

        Returns:
            List[str]: A list of individual ingredients, with leading and
                       trailing whitespace removed.

        Example:
            >>> IngredientParser.parse_ingredients("flour\n  sugar \nsalt  ")
            ['flour', 'sugar', 'salt']
        """
        return [ing.strip() for ing in ingredients_string.split("\n") if ing.strip()]
