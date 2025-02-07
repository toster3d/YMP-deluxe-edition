from datetime import date as date_type

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from extensions import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_name: Mapped[str] = mapped_column(nullable=False)
    hash: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False)
    recipes: Mapped[list["Recipe"]] = relationship("Recipe", back_populates="user")
    user_plans: Mapped[list["UserPlan"]] = relationship(
        "UserPlan", back_populates="user"
    )

    def __repr__(self) -> str:
        return f"<User {self.user_name}>"


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    meal_name: Mapped[str] = mapped_column(nullable=False)
    meal_type: Mapped[str] = mapped_column(
        String(20), 
        CheckConstraint("meal_type IN ('breakfast', 'lunch', 'dinner', 'dessert')")
    )
    ingredients: Mapped[str] = mapped_column(Text)
    instructions: Mapped[str] = mapped_column(Text)

    user: Mapped[User] = relationship("User", back_populates="recipes")

    def __repr__(self) -> str:
        return f"<Recipe {self.meal_name}>"


class UserPlan(Base):
    __tablename__ = "user_plan"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    date: Mapped[date_type] = mapped_column(nullable=False)
    breakfast: Mapped[str | None] = mapped_column(String(50), nullable=True)
    lunch: Mapped[str | None] = mapped_column(String(50), nullable=True)
    dinner: Mapped[str | None] = mapped_column(String(50), nullable=True)
    dessert: Mapped[str | None] = mapped_column(String(50), nullable=True)

    user: Mapped[User] = relationship("User", back_populates="user_plans")

    def __repr__(self) -> str:
        return f"<UserPlan {self.date} for User ID {self.user_id}>"
