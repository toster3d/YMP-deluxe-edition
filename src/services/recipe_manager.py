import logging

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RecipeManager:
    """
    A class to manage recipes for users.
    This class provides methods to interact with the recipe database,
    including adding, updating, deleting, and retrieving recipes.
    """

    def __init__(self, db):
        """
        Initialize the RecipeManager with a database connection.

        Args:
            db: The database connection object.
        """
        self.db = db

    def get_recepes_list(self, user_id):
        """
        Retrieve a list of recipes for the specified user.

        Args:
            user_id (int): The ID of the user.

        Returns:
            list: A list of dictionaries containing recipe information.
        """
        return self.db.execute(
            "SELECT id, mealName, mealType FROM Recipes1 WHERE user_id = :user_id "
            "ORDER BY mealName COLLATE NOCASE ASC",
            user_id=user_id
        )

    def get_recipes(self, user_id):
        """
        Return all recipes for the specified user.

        Args:
            user_id (int): The ID of the user.

        Returns:
            list: A list of dictionaries containing full recipe information.
        """
        return self.db.execute(
            "SELECT * FROM Recipes1 WHERE user_id = :user_id",
            user_id=user_id
        )

    def get_recipe_by_id(self, recipe_id, user_id):
        """
        Return a recipe with the given ID for the specified user.

        Args:
            recipe_id (int): The ID of the recipe.
            user_id (int): The ID of the user.

        Returns:
            dict: A dictionary containing recipe information, or None if not found.
        """
        recipe = self.db.execute(
            "SELECT * FROM Recipes1 WHERE id = :recipe_id AND user_id = :user_id",
            recipe_id=recipe_id,
            user_id=user_id
        )
        return recipe[0] if recipe else None

    def get_recipe_by_name(self, user_id, meal_name):
        """
        Return a recipe with the given name for the specified user.

        Args:
            user_id (int): The ID of the user.
            meal_name (str): The name of the meal.

        Returns:
            dict: A dictionary containing recipe information, or None if not found.
        """
        recipe = self.db.execute(
            "SELECT * FROM Recipes1 WHERE user_id = :user_id AND mealName = :meal_name",
            user_id=user_id,
            meal_name=meal_name
        )
        return recipe[0] if recipe else None

    def add_recipe(self, user_id, meal_name, meal_type, ingredients, instructions):
        """
        Add a new recipe for the specified user.

        Args:
            user_id (int): The ID of the user.
            meal_name (str): The name of the meal.
            meal_type (str): The type of the meal.
            ingredients (str): The ingredients of the recipe.
            instructions (str): The cooking instructions.
        """
        self.db.execute(
            "INSERT INTO Recipes1(user_id, mealName, mealType, ingredients, instructions) "
            "VALUES(:user_id, :mealName, :mealType, :ingredients, :instructions)",
            user_id=user_id,
            mealName=meal_name,
            mealType=meal_type,
            ingredients=ingredients,
            instructions=instructions
        )
        logger.info("Recipe was added!")

    def update_recipe(self, recipe_id, user_id, meal_name, meal_type, ingredients, instructions):
        """
        Update an existing recipe for the specified user.

        Args:
            recipe_id (int): The ID of the recipe to update.
            user_id (int): The ID of the user.
            meal_name (str): The updated name of the meal.
            meal_type (str): The updated type of the meal.
            ingredients (str): The updated ingredients of the recipe.
            instructions (str): The updated cooking instructions.
        """
        self.db.execute(
            "UPDATE Recipes1 SET mealName = :mealName, mealType = :mealType, "
            "ingredients = :ingredients, instructions = :instructions "
            "WHERE id = :recipe_id AND user_id = :user_id",
            recipe_id=recipe_id,
            user_id=user_id,
            mealName=meal_name,
            mealType=meal_type,
            ingredients=ingredients,
            instructions=instructions
        )

    def delete_recipe(self, recipe_id, user_id):
        """
        Delete a recipe for the specified user.

        Args:
            recipe_id (int): The ID of the recipe to delete.
            user_id (int): The ID of the user.
        """
        self.db.execute(
            "DELETE FROM Recipes1 WHERE id = :recipe_id AND user_id = :user_id",
            recipe_id=recipe_id,
            user_id=user_id
        )
        logger.info("Your recipe was successfully deleted!")

    def get_recipes_ordered_by_meal_type(self, user_id):
        """
        Return all recipes for the specified user, ordered by meal type.

        Args:
            user_id (int): The ID of the user.

        Returns:
            list: A list of dictionaries containing recipe information, ordered by meal type.
        """
        return self.db.execute(
            "SELECT * FROM Recipes1 WHERE user_id = :user_id ORDER BY mealType",
            user_id=user_id
        )

    def get_ingredients_by_meal_name(self, user_id, meal):
        """
        Return ingredients for a given meal name for the specified user.

        Args:
            user_id (int): The ID of the user.
            meal (str): The name of the meal.

        Returns:
            str: The ingredients of the recipe, or None if not found.
        """
        recipe = self.db.execute(
            "SELECT ingredients FROM Recipes1 WHERE user_id = :user_id AND mealName = :meal_name",
            user_id=user_id,
            meal_name=meal
        )
        return recipe[0]['ingredients'] if recipe else None

    def get_meal_names(self, user_id):
        """
        Return all meal names for the specified user.

        Args:
            user_id (int): The ID of the user.

        Returns:
            list: A list of meal names.
        """
        meals = self.db.execute(
            "SELECT mealName FROM Recipes1 WHERE user_id = :user_id",
            user_id=user_id
        )
        return [meal['mealName'] for meal in meals]
