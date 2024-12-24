import json
import typing

from aiohttp import web
from aiohttp.web_exceptions import HTTPException, HTTPUnprocessableEntity
from aiohttp.web_middlewares import middleware
from aiohttp_apispec import validation_middleware
from aiohttp_session import get_session

from app.admin.models import AdminModel
from app.web.utils import error_json_response

if typing.TYPE_CHECKING:
    from app.web.app import Application, Request


HTTP_ERROR_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "not_implemented",
    409: "conflict",
    500: "internal_server_error",
    503: "service unavailable",
}


@middleware
async def error_handling_middleware(request: "Request", handler):
    try:
        response = await handler(request)
    except HTTPUnprocessableEntity as e:
        return error_json_response(
            http_status=400,
            status=HTTP_ERROR_CODES[400],
            message=e.reason,
            data=json.loads(e.text),
        )
    except HTTPException as e:
        return error_json_response(
            http_status=e.status,
            status=HTTP_ERROR_CODES[e.status],
            message=str(e),
        )
    except Exception as e:
        request.app.logger.error("Exception", exc_info=e)
        return error_json_response(
            http_status=500, status="internal server error", message=str(e)
        )

    return response


@middleware
async def auth_middleware(request: "Request", handler):
    session = await get_session(request)
    if session:
        admin = AdminModel.from_session(session)
        request.admin = admin
    else:
        request.admin = None
    return await handler(request)


async def cors_middleware(app, handler):
    async def middleware_handler(request):
        origin = request.headers.get("Origin")
        if origin and origin in app.config.allowed_origins:
            if request.method == "OPTIONS":
                return web.Response(
                    status=200,
                    headers={
                        "Access-Control-Allow-Origin": origin,
                        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                        "Access-Control-Allow-Headers": "Origin, Content-Type, "
                        "Accept, Authorization",
                        "Access-Control-Allow-Credentials": "true",
                    },
                )

            response = await handler(request)
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, PUT, DELETE, OPTIONS"
            )
            response.headers["Access-Control-Allow-Headers"] = (
                "Origin, Content-Type, Accept, Authorization"
            )
            response.headers["Access-Control-Allow-Credentials"] = "true"
            return response
        return await handler(request)

    return middleware_handler


def setup_middlewares(app: "Application"):
    app.middlewares.append(error_handling_middleware)
    app.middlewares.append(auth_middleware)
    app.middlewares.append(validation_middleware)
    # app.middlewares.append(cors_middleware)
