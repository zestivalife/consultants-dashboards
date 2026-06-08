from typing import Any
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
import structlog

_ctx = structlog.contextvars


def _get_request_id() -> str | None:
    ctx = _ctx.get_contextvars()
    return ctx.get("request_id")


def success_response(
    data: Any = None,
    message: str = "OK",
    status_code: int = 200,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": jsonable_encoder(data),
            "error": None,
            "request_id": _get_request_id(),
        },
    )


def error_response(
    message: str = "An error occurred",
    status_code: int = 500,
    errors: Any = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": message,
            "data": None,
            "error": errors or message,
            "request_id": _get_request_id(),
        },
    )
