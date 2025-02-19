import json
from typing import Any

import pytest
from pydantic import ValidationError

from src.resources.pydantic_schemas import TokenResponse


class TestTokenResponse:
    def test_valid(self) -> None:
        """Test valid TokenResponse creation."""
        token = TokenResponse(
            access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            token_type="bearer"
        )
        
        assert token.access_token == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        assert token.token_type == "bearer"

    def test_default_token_type(self) -> None:
        """Test TokenResponse with default token_type."""
        token = TokenResponse(access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")  # type: ignore
        
        assert token.access_token == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        assert token.token_type == "bearer"

    @pytest.mark.parametrize(
        "invalid_data,expected_error",
        [
            (
                {},
                "Field required"
            ),
            (
                {"access_token": 123},
                "Input should be a valid string"
            ),
            (
                {
                    "access_token": "valid_token",
                    "token_type": 123
                },
                "Input should be a valid string"
            ),
        ]
    )
    def test_invalid(self, invalid_data: dict[str, Any], expected_error: str) -> None:
        """Test TokenResponse validation."""
        with pytest.raises(ValidationError) as exc_info:
            TokenResponse(**invalid_data)
        assert expected_error in str(exc_info.value)

    def test_model_config(self) -> None:
        """Test TokenResponse model configuration."""
        schema = TokenResponse.model_json_schema()
        
        required = schema.get("required", [])
        assert "access_token" in required
        assert "token_type" not in required
        
        properties = schema["properties"]
        assert properties["access_token"]["type"] == "string"
        assert properties["token_type"]["type"] == "string"
        assert properties["token_type"]["default"] == "bearer"
        
        assert "description" in properties["access_token"]
        assert "description" in properties["token_type"]

    def test_json_serialization(self) -> None:
        """Test that token data can be properly serialized to JSON."""
        token = TokenResponse(
            access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            token_type="bearer"
        )
        
        json_str = token.model_dump_json()
        assert isinstance(json_str, str)
        
        data = json.loads(json_str)
        assert data["access_token"] == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        assert data["token_type"] == "bearer"
