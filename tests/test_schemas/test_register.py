import json
from typing import Any

import pytest
from pydantic import ValidationError

from src.resources.pydantic_schemas import RegisterSchema


class TestRegisterSchema:
    def test_valid(self) -> None:
        """Test valid RegisterSchema creation."""
        register = RegisterSchema(
            email="test@example.com",
            username="testuser",
            password="Test123!#",
            confirmation="Test123!#"
        )
        
        assert register.email == "test@example.com"
        assert register.username == "testuser"
        assert register.password == "Test123!#"
        assert register.confirmation == "Test123!#"

    @pytest.mark.parametrize(
        "invalid_data,expected_error",
        [
            (
                {
                    "username": "testuser",
                    "password": "Test123!#",
                    "confirmation": "Test123!#"
                },
                "Field required"
            ),
            (
                {
                    "email": "test@example.com",
                    "password": "Test123!#",
                    "confirmation": "Test123!#"
                },
                "Field required"
            ),
            (
                {
                    "email": "test@example.com",
                    "username": "testuser",
                    "confirmation": "Test123!#"
                },
                "Field required"
            ),
            (
                {
                    "email": "test@example.com",
                    "username": "testuser",
                    "password": "Test123!#"
                },
                "Field required"
            ),
            (
                {
                    "email": "invalid_email",
                    "username": "testuser",
                    "password": "Test123!#",
                    "confirmation": "Test123!#"
                },
                "value is not a valid email address"
            ),
            (
                {
                    "email": "test@example.com",
                    "username": "te",
                    "password": "Test123!#",
                    "confirmation": "Test123!#"
                },
                "String should have at least 3 characters"
            ),
            (
                {
                    "email": "test@example.com",
                    "username": "t" * 31,
                    "password": "Test123!#",
                    "confirmation": "Test123!#"
                },
                "String should have at most 30 characters"
            ),
            (
                {
                    "email": "test@example.com",
                    "username": "testuser",
                    "password": "short",
                    "confirmation": "short"
                },
                "String should have at least 8 characters"
            ),
            (
                {
                    "email": "test@example.com",
                    "username": "testuser",
                    "password": "Test123!#",
                    "confirmation": "DifferentPass!#"
                },
                "Passwords do not match. Please ensure both passwords are identical."
            ),
            (
                {
                    "email": "test@example.com",
                    "username": "testuser",
                    "password": "weakpassword",
                    "confirmation": "weakpassword"
                },
                "Password does not meet complexity requirements."
            ),
        ]
    )
    def test_invalid(self, invalid_data: dict[str, Any], expected_error: str) -> None:
        """Test RegisterSchema validation."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterSchema(**invalid_data)
        assert expected_error in str(exc_info.value)

    @pytest.mark.parametrize(
        "password",
        [
            "Test123!#",
            "Complex!Pass123",
            "Ab1!defghijklmnop",
            "Test!#123",
        ]
    )
    def test_valid_passwords(self, password: str) -> None:
        """Test RegisterSchema with various valid passwords."""
        register = RegisterSchema(
            email="test@example.com",
            username="testuser",
            password=password,
            confirmation=password
        )
        
        assert register.password == password
        assert register.confirmation == password

    def test_model_config(self) -> None:
        """Test RegisterSchema model configuration."""
        schema = RegisterSchema.model_json_schema()
        
        required = schema.get("required", [])
        assert "email" in required
        assert "username" in required
        assert "password" in required
        assert "confirmation" in required
        
        properties = schema["properties"]
        assert properties["email"]["type"] == "string"
        assert properties["email"]["format"] == "email"
        assert properties["username"]["type"] == "string"
        assert properties["username"]["minLength"] == 3
        assert properties["username"]["maxLength"] == 30
        assert properties["password"]["type"] == "string"
        assert properties["password"]["minLength"] == 8
        assert properties["password"]["maxLength"] == 50
        
        assert "description" in properties["email"]
        assert "description" in properties["username"]
        assert "description" in properties["password"]
        assert "description" in properties["confirmation"]

    def test_json_serialization(self) -> None:
        """Test that registration data can be properly serialized to JSON."""
        register = RegisterSchema(
            email="test@example.com",
            username="testuser",
            password="Test123!#",
            confirmation="Test123!#"
        )
        
        json_str = register.model_dump_json()
        assert isinstance(json_str, str)
        
        data = json.loads(json_str)
        assert data["email"] == "test@example.com"
        assert data["username"] == "testuser"
        assert data["password"] == "Test123!#"
        assert data["confirmation"] == "Test123!#"