import logging
import time
from uuid import uuid4

from fastapi import Request

logger = logging.getLogger("ai_workbench")


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return True


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s request_id=%(request_id)s %(message)s")
for handler in logging.getLogger().handlers:
    handler.addFilter(RequestIdFilter())


async def request_logging_middleware(request: Request, call_next):
    request_id = str(uuid4())
    started = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    logger.info("%s %s status=%s duration_ms=%s", request.method, request.url.path, response.status_code, duration_ms, extra={"request_id": request_id})
    return response
