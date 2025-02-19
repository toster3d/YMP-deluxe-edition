from settings import get_test_settings


def test_settings_load() -> None:
    """Test if test settings load correctly."""
    settings = get_test_settings()
    assert settings.ASYNC_DATABASE_URI.startswith("sqlite") 
    