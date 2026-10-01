import os
import re
from datetime import datetime
from typing import Annotated, List

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field, StringConstraints

from app.api.core.rate_limit import limiter
from app.utils.logging import logger

router = APIRouter(prefix="/logs", tags=["logs"])

MAX_BODY_BYTES = 256 * 1024          # per request
MAX_LOG_FILE_BYTES = 10 * 1024 * 1024  # rotate to .1 beyond this, so the file can never fill the disk
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")


def _one_line(value: str) -> str:
    """Escape control characters (newlines, ANSI escapes) so a client cannot forge log entries."""
    return _CONTROL.sub(lambda m: f"\\x{ord(m.group()):02x}", value)


class FrontendLogEntry(BaseModel):
    logs: List[Annotated[str, StringConstraints(max_length=2000)]] = Field(max_length=200)
    timestamp: Annotated[str, StringConstraints(max_length=100)]
    userAgent: Annotated[str, StringConstraints(max_length=300)]
    url: Annotated[str, StringConstraints(max_length=500)]


@router.post(
    "/frontend",
    status_code=status.HTTP_200_OK,
    summary="Ingest frontend log batch",
    description=(
        "Accepts a batch (max 200 lines of 2000 chars, 256 KB) of console/log lines from the browser along with "
        "**`userAgent`** and **`url`**. Control characters are escaped, then the batch is appended to "
        "`logs/maison_frontend_log` on the server and a summary mirrored to the backend logger. "
        "Public (the app logs before sign-in) and therefore rate limited."
    ),
    response_description="Success message with count of lines written.",
)
@limiter.limit("20/minute")
async def receive_frontend_logs(request: Request, log_entry: FrontendLogEntry):
    """
    Receive frontend logs and save them to maison_frontend_log file
    """
    declared = request.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > MAX_BODY_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Log batch too large")
    try:
        # Ensure logs directory exists
        logs_dir = "logs"
        os.makedirs(logs_dir, exist_ok=True)

        # Path to frontend log file
        frontend_log_path = os.path.join(logs_dir, "maison_frontend_log")
        if os.path.exists(frontend_log_path) and os.path.getsize(frontend_log_path) > MAX_LOG_FILE_BYTES:
            os.replace(frontend_log_path, frontend_log_path + ".1")

        # Format the log entry
        timestamp = datetime.now().isoformat()
        header = f"\n{'='*80}\n"
        header += f"Frontend Log Entry - {timestamp}\n"
        header += f"User Agent: {_one_line(log_entry.userAgent)}\n"
        header += f"URL: {_one_line(log_entry.url)}\n"
        header += f"{'='*80}\n"

        # Write to frontend log file
        with open(frontend_log_path, "a", encoding="utf-8") as f:
            f.write(header)
            for log in log_entry.logs:
                f.write(_one_line(log) + "\n")
            f.write("\n")

        # Also log to backend logger for monitoring
        logger.info(f"Received {len(log_entry.logs)} frontend logs from {_one_line(log_entry.url)}")

        return {"status": "success", "message": f"Saved {len(log_entry.logs)} logs"}

    except Exception as e:
        logger.error(f"Failed to save frontend logs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save frontend logs")
