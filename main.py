import logging
import os

from aiohttp.web import run_app

from app.web.app import setup_app

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    if os.getenv("PORT"):
        logger.warning("Running on port %s", os.getenv("PORT"))
        port = int(os.getenv("PORT"))
    else:
        logger.warning("Running on port 8080")
        port = 8080

    run_app(
        setup_app(
            config_path=os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "etc/config.yaml"
            )
        ),
        port=port,
    )
