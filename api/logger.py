import logging
import os
import sys
import time
from logging.handlers import RotatingFileHandler

from fastapi import Request

LOG_PATH = "api/Logs/"
LOG_NAME = "api.log"

MAX_BACKUPS = 5
MAX_LOG_SIZE_MB = 50

# sqlalchemy logger
db_logger = logging.getLogger("sqlalchemy.engine")
db_logger.setLevel(logging.INFO)

# uvicorn logger
uvicorn_logger = logging.getLogger("uvicorn.error")
uvicorn_logger.setLevel(logging.INFO)

# custom logger
api_logger = logging.getLogger(__name__)
api_logger.setLevel(logging.INFO)

formater = logging.Formatter(fmt="%(asctime)s-%(name)s-%(levelname)s-%(message)s")

# file handler
# creates log path, checks if it already exists
os.makedirs(LOG_PATH, exist_ok=True)

file_handler = RotatingFileHandler(
    os.path.join(LOG_PATH, LOG_NAME),
    maxBytes=MAX_LOG_SIZE_MB * 1000 * 1000,
    backupCount=MAX_BACKUPS,
)
file_handler.setFormatter(formater)

# console output handler
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formater)


loggers = [db_logger, uvicorn_logger, api_logger]

for logger in loggers:
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)


async def request_logging_middleware(request: Request, call_next):
    """Loggs incoming request data"""
    start_time = time.time()
    response = await call_next(request)
    response_time = time.time() - start_time

    log_dict = {
        "path": request.url.path,
        "method": request.method,
        "client_ip": request.client.host,
        "response_code": response.status_code,
        "response_time": response_time,
    }
    api_logger.info(log_dict)
    return response
