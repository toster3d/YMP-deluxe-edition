class UserPlanManager:
    def __init__(self, db):
        self.db = db

    def add_plan(self, user_id, date):
        """Add a new user plan for a specific date."""
        self.db.execute(
            "INSERT INTO userPlan (user_id, date) VALUES (?, ?)",
            user_id,
            date
        )

    def update_meal(self, user_id, date, meal_name, meal_value):
        """Update a specific meal for a user on a specific date."""
        if meal_name is None:
            raise ValueError("meal_name cannot be None")
        self.db.execute(
            f"UPDATE userPlan SET {meal_name} = ? WHERE user_id = ? AND date = ?",
            meal_value,
            user_id,
            date
        )

    def get_plans(self, user_id, date):
        """Get all plans for a user on a specific date."""
        return self.db.execute(
            "SELECT * FROM userPlan WHERE user_id = ? AND date = ?",
            user_id,
            date
        )

    def create_or_update_plan(self, user_id, selected_date, user_plan, meal_name):
        """Create a new plan or update an existing meal for the user on the selected date."""
        existing_plan = self.get_plans(user_id, selected_date)
        if not existing_plan:
            self.add_plan(user_id, selected_date)
        self.update_meal(user_id, selected_date, user_plan, meal_name)

    def get_user_meals(self, user_id, date):
        """Get all meals for a user on a specific date."""
        return self.db.execute(
            "SELECT breakfast, lunch, dinner, dessert FROM userPlan WHERE user_id = ? AND date = ?",
            user_id,
            date
        )

    def get_user_recipes(self, user_id):
        """Get all recipes for a user."""
        return self.db.execute(
            "SELECT mealName FROM Recipes1 WHERE user_id = ?",
            user_id
        )