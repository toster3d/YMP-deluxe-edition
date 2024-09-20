from flask import flash


class RecipeManager:
    def __init__(self, db, user_id):
        self.db = db
        self.user_id = user_id

    def get_recepes_list(self):
        """
        Retrieves a list of recipes for the current user.

        This method executes a SQL query to select the id, mealName, and mealType
        from the Recipes1 table for the current user. The results are ordered
        alphabetically by mealName, ignoring case.

        Returns:
            A list of dictionaries, where each dictionary represents a recipe
            with 'id', 'mealName', and 'mealType' keys.
        """
        return self.db.execute(
            "SELECT id, mealName, mealType FROM Recipes1 WHERE user_id = :user_id "
            "ORDER BY mealName COLLATE NOCASE ASC",
            user_id=self.user_id
        )

    def get_recipes(self):
        """Returns all recipes for the current user"""
        return self.db.execute(
            "SELECT * FROM Recipes1 WHERE user_id = :user_id",
            user_id=self.user_id
        )

    def get_recipe_by_id(self, recipe_id, db):
        """Returns a recipe with the given ID for the current user"""
        recipe = db.execute(
            "SELECT * FROM Recipes1 WHERE id = :recipe_id AND user_id = :user_id",
            recipe_id=recipe_id,
            user_id=self.user_id
        )
        return recipe[0] if recipe else None

    def add_recipe(self, meal_name, meal_type, ingredients, instructions):
        """Adds a new recipe for the current user"""
        self.db.execute(
            "INSERT INTO Recipes1(user_id, mealName, mealType, ingredients, instructions) "
            "VALUES(:user_id, :mealName, :mealType, :ingredients, :instructions)",
            user_id=self.user_id,
            mealName=meal_name,
            mealType=meal_type,
            ingredients=ingredients,
            instructions=instructions
        )
        flash("Recipe was added!")

    def update_recipe(self, recipe_id, meal_name, meal_type, ingredients, instructions):
        """Updates an existing recipe for the current user"""
        self.db.execute(
            "UPDATE Recipes1 SET mealName = :mealName, mealType = :mealType, "
            "ingredients = :ingredients, instructions = :instructions WHERE id = :recipe_id",
            recipe_id=recipe_id,
            mealName=meal_name,
            mealType=meal_type,
            ingredients=ingredients,
            instructions=instructions
        )

    def delete_recipe(self, recipe_id):
        """Deletes a recipe for the current user"""
        self.db.execute(
            "DELETE FROM Recipes1 WHERE id = :recipe_id AND user_id = :user_id",
            recipe_id=recipe_id,
            user_id=self.user_id
        )
        flash("Your recipe was successfully deleted!")

    def get_recipes_ordered_by_meal_type(self):
        """Returns all recipes for the current user, ordered by meal type"""
        return self.db.execute(
            "SELECT * FROM Recipes1 WHERE user_id = :user_id ORDER BY mealType",
            user_id=self.user_id
        )

    def get_ingredients_by_meal_name(self, meal):
        """Returns ingredients for a given meal name for the current user"""
        recipe = self.db.execute(
            "SELECT ingredients FROM Recipes1 WHERE user_id = :user_id AND mealName = :meal_name",
            user_id=self.user_id,
            meal_name=meal
        )
        return recipe[0]['ingredients'] if recipe else None

    def get_meal_names(self):
        """Returns all meal names for the current user"""
        meals = self.db.execute(
            "SELECT mealName FROM Recipes1 WHERE user_id = :user_id",
            user_id=self.user_id
        )
        return [meal['mealName'] for meal in meals]
