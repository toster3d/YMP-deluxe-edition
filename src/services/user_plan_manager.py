from datetime import datetime
from abc import ABC, abstractmethod




class AbstractUserPlanManager(ABC):
    @abstractmethod
    def add_plan(self, user_id: int, date: datetime): ...

    def sth_else(self): ...



class SqliteUserPlanManager(AbstractUserPlanManager):
    """
    A class to manage user meal plans.

    This class provides methods for adding, updating, and retrieving user meal plans
    from the database.
    """

    def __init__(self, db):
        """
        Initialize the UserPlanManager with a database connection.

        Args:
            db: The database connection object.
        """
        self.db = db

    def add_plan(self, user_id, date):
        """
        Add a new user plan for a specific date.

        Args:
            user_id (int): The ID of the user.
            date (str): The date for the plan.
        """
        self.db.execute(
            "INSERT INTO userPlan (user_id, date) VALUES (?, ?)",
            user_id,
            date
        )
            
    def update_meal(self, user_id, date, meal_name, meal_value):
        """
        Update a specific meal for a user on a specific date.

        Args:
            user_id (int): The ID of the user.
            date (str): The date of the meal.
            meal_name (str): The name of the meal (e.g., 'breakfast', 'lunch').
            meal_value (str): The value to set for the meal.

        Raises:
            ValueError: If meal_name is None.
        """
        if meal_name is None:
            raise ValueError("meal_name cannot be None")
        self.db.execute(
            f"UPDATE userPlan SET {meal_name} = ? WHERE user_id = ? AND date = ?",
            meal_value,
            user_id,
            date
        )

    def get_plans(self, user_id: int, date: datetime):
        """
        Get all plans for a user on a specific date.

        Args:
            user_id (int): The ID of the user.
            date (str): The date to retrieve plans for.

        Returns:
            list: A list of dictionaries containing the user's plans.
        """
        # plans = self.db.execute(
        #     "SELECT * FROM userPlan WHERE user_id = ? AND date = ?",
        #     user_id,
        #     date
        # )
        
        # if not plans:
        #     return []
        
        # return plans

    def create_or_update_plan(self, user_id, selected_date, user_plan, meal_name):
        """
        Create a new plan or update an existing meal for the user on the selected date.

        Args:
            user_id (int): The ID of the user.
            selected_date (str): The date for the plan.
            user_plan (str): The meal plan to update.
            meal_name (str): The name of the meal to update.
        """
        existing_plan = self.get_plans(user_id, selected_date)
        if not existing_plan:
            self.add_plan(user_id, selected_date)
        self.update_meal(user_id, selected_date, user_plan, meal_name)

    def get_user_meals(self, user_id, date):
        """
        Get all meals for a user on a specific date.

        Args:
            user_id (int): The ID of the user.
            date (str): The date to retrieve meals for.

        Returns:
            list: A list of dictionaries containing the user's meals.
        """
        return self.db.execute(
            "SELECT breakfast, lunch, dinner, dessert FROM userPlan WHERE user_id = ? AND date = ?",
            user_id,
            date
        )

    def get_user_recipes(self, user_id):
        """
        Get all recipes for a user.

        Args:
            user_id (int): The ID of the user.

        Returns:
            list: A list of dictionaries containing the user's recipes.
        """
        return self.db.execute(
            "SELECT mealName FROM Recipes1 WHERE user_id = ?",
            user_id
        )