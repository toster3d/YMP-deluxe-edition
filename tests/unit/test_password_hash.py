from werkzeug.security import check_password_hash, generate_password_hash


def test_password_hash() -> None:
    password = "Test123!"
    hashed_password = generate_password_hash(password)
    assert check_password_hash(hashed_password, password) 