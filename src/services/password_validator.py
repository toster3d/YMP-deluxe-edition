class PasswordValidator:
    """Service for validating password strength."""

    def validate(self, password: str) -> bool:
        """
        Validate password strength.

        Requirements:
        - Length between 8 and 64 characters
        - At least one digit
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one special character (!#?%$&)
        - No whitespace characters
        - No more than 3 consecutive identical characters

        Args:
            password: Password to validate

        Returns:
            bool: True if password meets all requirements
        """
        symbols = {"!", "#", "?", "%", "$", "&"}
        if not (8 <= len(password) <= 64):
            return False

        if any(char.isspace() for char in password):
            return False

        for i in range(len(password) - 3):
            if password[i] == password[i + 1] == password[i + 2] == password[i + 3]:
                return False

        has_digit = False
        has_upper = False
        has_lower = False
        has_symbol = False

        for char in password:
            if char.isdigit():
                has_digit = True
            elif char.isupper():
                has_upper = True
            elif char.islower():
                has_lower = True
            elif char in symbols:
                has_symbol = True

        return has_digit and has_upper and has_lower and has_symbol
