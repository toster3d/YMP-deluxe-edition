from typing import Any

import pytest
from fastapi import HTTPException

from src.jwt_utils import create_access_token, verify_jwt


def test_create_and_verify_jwt() -> None:
    # Arrange
    user_id: int = 1
    username: str = "testuser"
    
    # Act
    token: str = create_access_token(user_id, username)
    payload: dict[str, Any] = verify_jwt(token)
    
    # Assert
    assert payload["sub"] == str(user_id)
    assert payload["username"] == username

def test_verify_expired_jwt() -> None:
    # Arrange
    # user_id: int = 1
    # username: str = "testuser"
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        verify_jwt("expired.token.here")
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail in ["Token has expired", "Invalid token"] 