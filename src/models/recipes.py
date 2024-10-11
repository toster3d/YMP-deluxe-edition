from src.extensions import db
from datetime import date

class User(db.Model):  # type: ignore
    __tablename__ = 'users'
    
    id: int = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_name: str = db.Column(db.String, nullable=False)
    hash: str = db.Column(db.String, nullable=False)
    email: str = db.Column(db.String, nullable=False)

    def __repr__(self) -> str:
        return f'<User {self.user_name}>'

class Recipe(db.Model):  # type: ignore
    __tablename__ = 'recipes'
    
    id: int = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    meal_name: str = db.Column(db.String, nullable=False)
    meal_type: str = db.Column(db.String, nullable=False)
    ingredients: str = db.Column(db.Text)
    instructions: str = db.Column(db.Text)

    def __repr__(self) -> str:
        return f'<Recipe {self.meal_name}>'

class UserPlan(db.Model):  # type: ignore
    __tablename__ = 'user_plan'
    
    id: int = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date: date = db.Column(db.Date, nullable=False)
    breakfast: str = db.Column(db.String(255))
    lunch: str = db.Column(db.String(255))
    dinner: str = db.Column(db.String(255))
    dessert: str = db.Column(db.String(255))

    def __repr__(self) -> str:
        return f'<UserPlan {self.date} for User ID {self.user_id}>'