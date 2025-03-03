from resources.pydantic_schemas import TokenResponse


def test_token_response_schema() -> None:
    token_data: dict[str, str] = {
        "access_token": "test_token",
        "token_type": "bearer"
    }
    
    token_response: TokenResponse = TokenResponse(**token_data)
    
    assert token_response.access_token == "test_token"
    assert token_response.token_type == "bearer" 