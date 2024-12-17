from datetime import datetime, timezone
from typing import Any

import jwt
from fastapi import HTTPException, status

from config import get_settings

settings = get_settings()

def create_access_token(user_id: int, username: str) -> str:
    """
    Create a JWT access token for the user.
    
    Args:
        user_id: User's ID from database
        username: User's username
        
    Returns:
        str: JWT access token
        
    Raises:
        HTTPException: If token creation fails
    """
    expires_delta = settings.jwt_access_token_expires
    expire = datetime.now(timezone.utc) + expires_delta

    to_encode = {
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "sub": str(user_id),
        "username": username,
        "type": "access",
        "jti": f"{user_id}-{int(datetime.now(timezone.utc).timestamp())}"
    }
    
    try:
        token = jwt.encode(
            to_encode,
            settings.jwt_secret_key.get_secret_value(),
            algorithm=settings.jwt_algorithm
        )
        return token if isinstance(token, str) else token.decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create access token: {str(e)}")

def verify_jwt(token: str) -> dict[str, Any]:
    """
    Verify a JWT token and return the payload.
    
    Args:
        token: JWT token to verify
        
    Returns:
        dict: Decoded payload of the token
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key.get_secret_value(), algorithms=[settings.jwt_algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
