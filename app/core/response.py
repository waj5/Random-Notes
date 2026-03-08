from typing import Any

from fastapi.encoders import jsonable_encoder


def success_response(data: Any = None, message: str = "success", code: int = 0):
    return {
        "code": code,
        "message": message,
        "data": jsonable_encoder(data),
    }