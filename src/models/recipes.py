from extensions import db
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey
from datetime import date as date_type

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_name: Mapped[str] = mapped_column(nullable=False)
    hash: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False)
    # a one-to-many relationship with Recipe
    recipes: Mapped[list["Recipe"]] = relationship("Recipe", back_populates="user")
    user_plans: Mapped[list["UserPlan"]] = relationship("UserPlan", back_populates="user")

    def __repr__(self) -> str:
        return f'<User {self.user_name}>'

class Recipe(Base):
    __tablename__ = 'recipes'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    meal_name: Mapped[str] = mapped_column(nullable=False)
    meal_type: Mapped[str] = mapped_column(nullable=False)
    ingredients: Mapped[str] = mapped_column(db.Text)
    instructions: Mapped[str] = mapped_column(db.Text)

    # a many-to-one relationship with User
    user: Mapped[User] = relationship("User", back_populates="recipes")

    def __repr__(self) -> str:
        return f'<Recipe {self.meal_name}>'

class UserPlan(Base): 
    __tablename__ = 'user_plan'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    date: Mapped[date_type] = mapped_column(nullable=False) 
    breakfast: Mapped[str] = mapped_column(String(50))
    lunch: Mapped[str] = mapped_column(String(50))
    dinner: Mapped[str] = mapped_column(String(50))
    dessert: Mapped[str] = mapped_column(String(50))

    # a many-to-one relationship with User
    user: Mapped[User] = relationship("User", back_populates="user_plans")

    def __repr__(self) -> str:
        return f'<UserPlan {self.date} for User ID {self.user_id}>'
