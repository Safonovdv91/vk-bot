import logging
import logging.handlers
import typing

if typing.TYPE_CHECKING:
    from app.web.app import Application


def setup_logging(
    _: "Application",
    sh_logging_level: int = logging.DEBUG,
    fh_logging_level: int = logging.INFO,
) -> None:
    logger = logging.getLogger()
    format_logger = "%(asctime)s - %(name)s:%(lineno)s - %(levelname)s - %(message)s"
    logger.setLevel(10)

    sh = logging.StreamHandler()  # отображение в экран
    sh.setLevel(sh_logging_level)
    sh.setFormatter(logging.Formatter(format_logger))

    err_fh = logging.handlers.RotatingFileHandler(filename="app/logger/err_logfile.log")
    err_fh.setFormatter(logging.Formatter(format_logger))
    err_fh.setLevel(logging.ERROR)

    full_log = logging.handlers.RotatingFileHandler(filename="app/logger/logfile.log")
    full_log.setFormatter(logging.Formatter(format_logger))
    full_log.setLevel(fh_logging_level)

    logger.addHandler(sh)
    logger.addHandler(err_fh)
    logger.addHandler(full_log)

    logger.debug("Logger was initialized")
