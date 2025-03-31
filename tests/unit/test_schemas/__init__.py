"""Test schemas for the application."""

from .test_recipe import TestRecipeSchema
from .test_register import TestRegisterSchema
from .test_shopping_list import (
    TestDateRangeSchema,
    TestShoppingListRangeResponse,
    TestShoppingListResponse,
)
from .test_token import TestTokenResponse
from .test_user_plan import (
    TestPlanSchema,
    TestScheduleResponse,
    TestUserPlanSchema,
)

__all__ = [
    "TestRecipeSchema",  # Recipe Schema Tests
    "TestRegisterSchema",  # Register Schema Tests
    "TestShoppingListResponse",  # Shopping List Schema Tests
    "TestShoppingListRangeResponse",
    "TestDateRangeSchema",
    "TestTokenResponse",  # Token Schema Tests
    "TestUserPlanSchema",  # User Plan Schema Tests
    "TestPlanSchema",
    "TestScheduleResponse",
]