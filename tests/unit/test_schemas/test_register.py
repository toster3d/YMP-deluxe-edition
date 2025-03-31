"""Unit tests for RegisterSchema and PasswordValidator."""

import json

import pytest
from pydantic import ValidationError

from src.resources.pydantic_schemas import RegisterSchema
from src.services.password_validator import PasswordValidator


@pytest.fixture
def valid_register_data() -> dict[str, str]:
    """Fixture providing valid registration data."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "Test123!#",
        "confirmation": "Test123!#"
    }


@pytest.mark.schema
class TestRegisterSchema:
    """Test suite for RegisterSchema validation and functionality."""
    
    class TestEmailValidation:
        """Tests for email validation."""

        @pytest.mark.parametrize(
            "email",
            [
                "test.email@example.com",
                "test+label@example.com",
                "test.email+label@example.com",
                "test@subdomain.example.com",
                "test@example.co.uk",
                "very.common@example.com",
                "disposable.style.email.with+symbol@example.com",
                "other.email-with-hyphen@example.com",
                "fully-qualified-domain@example.com",
                "user.name+tag+sorting@example.com",
                "x@example.com",
                "example-indeed@strange-example.com",
                "example@s.example",
            ]
        )
        def test_valid_email_formats(self, email: str, valid_register_data: dict[str, str]) -> None:
            """Test various valid email formats."""
            valid_register_data["email"] = email
            register = RegisterSchema(**valid_register_data)
            assert register.email == email

        @pytest.mark.parametrize(
            "invalid_email,expected_error",
            [
                ("plainaddress", "value is not a valid email address"),
                ("@missinglocal.com", "value is not a valid email address"),
                ("email@", "value is not a valid email address"),
                ("email@.com", "value is not a valid email address"),
                ("email@domain", "value is not a valid email address"),
                ("email@111.222.333.44444", "value is not a valid email address"),
                ("email@[123.123.123.123]", "value is not a valid email address"),
                ("", "value is not a valid email address"),
                (" ", "value is not a valid email address"),
            ]
        )
        def test_invalid_email_formats(
            self, invalid_email: str, expected_error: str, valid_register_data: dict[str, str]
        ) -> None:
            """Test various invalid email formats."""
            valid_register_data["email"] = invalid_email
            with pytest.raises(ValidationError) as exc_info:
                RegisterSchema(**valid_register_data)
            assert expected_error in str(exc_info.value)

        def test_email_case_sensitivity(self, valid_register_data: dict[str, str]) -> None:
            """Test email case sensitivity handling."""
            test_cases = [
                ("TEST.USER@EXAMPLE.COM", "TEST.USER@example.com"),
                ("Test.User@Example.COM", "Test.User@example.com"),
                ("test.user@EXAMPLE.COM", "test.user@example.com"),
            ]
            
            for input_email, expected_email in test_cases:
                valid_register_data["email"] = input_email
                register = RegisterSchema(**valid_register_data)
                assert register.email == expected_email, f"Failed for email: {input_email}"

    class TestPasswordValidation:
        """Tests for password validation."""

        @pytest.mark.parametrize(
            "password,expected_validation",
            [
                ("short", False),
                ("nodigits!", False),
                ("no-upper-1!", False),
                ("NO-LOWER-1!", False),
                ("NoSpecial1", False),
                ("Valid1!Pass", True),
                ("Test123!#", True),
                ("A" * 65 + "1!", False),
                ("Ab1!" * 16, True),
                ("Ab1!aaaa", False),
                ("Test1!a b", False),
                ("Test1!a\t", False),
                ("Test1!a\n", False),
            ]
        )
        def test_password_validator(self, password: str, expected_validation: bool) -> None:
            """Test PasswordValidator with various password combinations."""
            validator = PasswordValidator()
            assert validator.validate(password) == expected_validation, \
                f"Password validation failed for: {password}"

        @pytest.mark.parametrize(
            "special_char",
            ["!", "#", "?", "%", "$", "&"]
        )
        def test_allowed_special_characters(
            self, special_char: str, valid_register_data: dict[str, str]
        ) -> None:
            """Test that all allowed special characters are accepted in passwords."""
            test_password = f"Test123{special_char}"
            valid_register_data["password"] = test_password
            valid_register_data["confirmation"] = test_password
            register = RegisterSchema(**valid_register_data)
            assert register.password == test_password, \
                f"Failed for special character: {special_char}"

        @pytest.mark.parametrize(
            "special_char",
            ["@", "*", "(", ")", "+", "=", "|", "{", "}", "[", "]", "~", "`", ",", ";", ":", "'", '"', "\\", "/"]
        )
        def test_disallowed_special_characters(
            self, special_char: str, valid_register_data: dict[str, str]
        ) -> None:
            """Test that disallowed special characters are rejected in passwords."""
            test_password = f"Test123{special_char}"
            valid_register_data["password"] = test_password
            valid_register_data["confirmation"] = test_password
            with pytest.raises(ValidationError) as exc_info:
                RegisterSchema(**valid_register_data)
            assert "Password does not meet complexity requirements" in str(exc_info.value), \
                f"Failed for special character: {special_char}"

        def test_password_whitespace_handling(self, valid_register_data: dict[str, str]) -> None:
            """Test handling of whitespace in passwords."""
            whitespace_cases = [
                " Test123!#",
                "Test123!# ",
                "Test 123!#",
                "\tTest123!#",
                "Test123!#\n",
                "Test123!#\r",
            ]
            
            for test_password in whitespace_cases:
                valid_register_data["password"] = test_password
                valid_register_data["confirmation"] = test_password
                with pytest.raises(ValidationError) as exc_info:
                    RegisterSchema(**valid_register_data)
                assert "Password does not meet complexity requirements" in str(exc_info.value), \
                    f"Failed for password with whitespace: {test_password!r}"

        @pytest.mark.parametrize(
            "password,confirmation",
            [
                ("Test123!#", "Test123!#"),
                ("Test123!#Ab", "Test123!#Ab"),
                ("Test123!#Abcd", "Test123!#Abcd"),
                ("Test123!#" + "Aa1!" * 10, "Test123!#" + "Aa1!" * 10),
                ("Test123!#" + "Aa1!" * 13 + "xyz", "Test123!#" + "Aa1!" * 13 + "xyz"),
            ]
        )
        def test_password_length_boundaries(self, password: str, confirmation: str) -> None:
            """Test boundary values for password length."""
            register = RegisterSchema(
                email="test@example.com",
                username="testuser",
                password=password,
                confirmation=confirmation
            )
            assert register.password == password, f"Failed for password length: {len(password)}"

        @pytest.mark.parametrize(
            "invalid_password",
            [
                "Test123!#" + "A" * 56,
                "Test123!#" + "A" * 100,
                "A" * 1000 + "Test123!#",
            ]
        )
        def test_password_too_long(self, invalid_password: str, valid_register_data: dict[str, str]) -> None:
            """Test that passwords longer than 64 characters are rejected."""
            valid_register_data["password"] = invalid_password
            valid_register_data["confirmation"] = invalid_password
            with pytest.raises(ValidationError) as exc_info:
                RegisterSchema(**valid_register_data)
            assert "String should have at most 64 characters" in str(exc_info.value), \
                f"Failed for password length: {len(invalid_password)}"

    class TestUsernameValidation:
        """Tests for username validation."""

        @pytest.mark.parametrize(
            "username",
            [
                "user_name",
                "user-name",
                "user123",
                "123user",
                "a" * 30,
                "min",
                "user_123",
                "123_user",
                "user-123",
            ]
        )
        def test_valid_username_formats(self, username: str, valid_register_data: dict[str, str]) -> None:
            """Test various valid username formats."""
            valid_register_data["username"] = username
            register = RegisterSchema(**valid_register_data)
            assert register.username == username, f"Failed for username: {username}"

        @pytest.mark.parametrize(
            "invalid_username,expected_error",
            [
                ("ab", "String should have at least 3 characters"),
                ("a" * 31, "String should have at most 30 characters"),
                ("user@name", "String should match pattern"),
                ("user name", "String should match pattern"),
                ("user.name", "String should match pattern"),
                ("", "String should have at least 3 characters"),
                (" " * 3, "String should match pattern"),
            ]
        )
        def test_invalid_username_formats(
            self, invalid_username: str, expected_error: str, valid_register_data: dict[str, str]
        ) -> None:
            """Test various invalid username formats."""
            valid_register_data["username"] = invalid_username
            with pytest.raises(ValidationError) as exc_info:
                RegisterSchema(**valid_register_data)
            assert expected_error in str(exc_info.value), \
                f"Failed for invalid username: {invalid_username}"

    class TestSchemaConfiguration:
        """Tests for schema configuration and serialization."""

        def test_model_config(self) -> None:
            """Test RegisterSchema model configuration."""
            schema = RegisterSchema.model_json_schema()
            
            required = schema.get("required", [])
            for field in ["email", "username", "password", "confirmation"]:
                assert field in required, f"Field {field} should be required"
            
            properties = schema["properties"]
            
            assert properties["email"]["type"] == "string"
            assert properties["email"]["format"] == "email"
            
            assert properties["username"]["type"] == "string"
            assert properties["username"]["minLength"] == 3
            assert properties["username"]["maxLength"] == 30
            assert "pattern" in properties["username"]
            
            assert properties["password"]["type"] == "string"
            assert properties["password"]["minLength"] == 8
            assert properties["password"]["maxLength"] == 64
            
            for field in ["email", "username", "password", "confirmation"]:
                assert "description" in properties[field], \
                    f"Field {field} should have a description"

        def test_json_serialization(self, valid_register_data: dict[str, str]) -> None:
            """Test JSON serialization and deserialization."""
            register = RegisterSchema(**valid_register_data)
            json_str = register.model_dump_json()
            assert isinstance(json_str, str)
            
            data = json.loads(json_str)
            for field, value in valid_register_data.items():
                assert data[field] == value, f"Field {field} was not correctly serialized"
            
            register_2 = RegisterSchema(**data)
            assert register_2.model_dump() == valid_register_data

        def test_model_validation_error_messages(self, valid_register_data: dict[str, str]) -> None:
            """Test that validation error messages are clear and helpful."""
            data = valid_register_data.copy()
            del data["email"]
            with pytest.raises(ValidationError) as exc_info:
                RegisterSchema(**data)
            assert "Field required" in str(exc_info.value)
            
            data = valid_register_data.copy()
            data["email"] = "invalid"
            with pytest.raises(ValidationError) as exc_info:
                RegisterSchema(**data)
            assert "value is not a valid email address" in str(exc_info.value)