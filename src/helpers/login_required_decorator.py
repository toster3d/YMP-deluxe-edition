from flask import session
from functools import wraps
from typing import Callable, Any
from flask import Response

def login_required(f: Callable[..., Any]) -> Callable[..., Response]:
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Response:
        if session.get("user_id") is None:
            return Response("Użytkownik musi być zalogowany.", status=401)
        return f(*args, **kwargs)
    return decorated_function
