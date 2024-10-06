from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request  # type: ignore
from typing import Callable, Any


def login_required(f: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorate routes to require login.
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        try:
            verify_jwt_in_request()
        except Exception:
            return jsonify({"msg": "User must be logged in."}), 401
        return f(*args, **kwargs)
    return decorated_function
