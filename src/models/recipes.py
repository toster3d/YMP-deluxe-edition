from datetime import date as date_type

from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from extensions import Base
from resources.pydantic_schemas import VALID_MEAL_TYPES, MealType


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
    meal_type: Mapped[MealType] = mapped_column(
        SQLAlchemyEnum(
            *VALID_MEAL_TYPES,
            name="meal_type_enum",
            create_type=True,
            native_enum=True,
            validate_strings=True
        ),
        nullable=False
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
