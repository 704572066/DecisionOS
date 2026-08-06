from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone

from app.core.config import settings


class DecisionOSFormatter(logging.Formatter):
    """Compact structured logs suitable for Docker stdout collection."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        request_id = getattr(record, "request_id", "-")
        meeting_id = getattr(record, "meeting_id", "-")
        message = record.getMessage().replace("\n", "\\n")
        base = (
            f'timestamp="{timestamp}" '
            f'level="{record.levelname}" '
            f'logger="{record.name}" '
            f'request_id="{request_id}" '
            f'meeting_id="{meeting_id}" '
            f'message="{message}"'
        )
        if record.exc_info:
            exception = self.formatException(record.exc_info).replace("\n", "\\n")
            base += f' exception="{exception}"'
        return base


def configure_logging() -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(DecisionOSFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)

    # Keep access logs useful without duplicating every internal debug message.
    logging.getLogger("uvicorn.access").setLevel(level)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
