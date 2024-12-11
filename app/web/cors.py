import typing

import aiohttp_cors

if typing.TYPE_CHECKING:
    from app.web.app import Application


def setup_cors(app: "Application"):
    cors = aiohttp_cors.setup(
        app,
        defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True, expose_headers="*", allow_headers="*"
            )
        },
    )

    for route in list(app.router.routes()):
        cors.add(route)
