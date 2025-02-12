import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from models.recipes import User
from settings import get_test_settings

settings = get_test_settings()

@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create test user."""
    from models.recipes import User
    from services.user_auth_manager import hash_password
    
    user = User(
        email=settings.TEST_USER_EMAIL,
        user_name=settings.TEST_USER_NAME,
        hash=hash_password(settings.TEST_USER_PASSWORD)
    )
    db_session.add(user)
    await db_session.commit()
    return user
