from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List
import os
from datetime import datetime
from app.utils.logging import logger

router = APIRouter(prefix="/logs", tags=["logs"])


class FrontendLogEntry(BaseModel):
    logs: List[str]
    timestamp: str
    userAgent: str
    url: str


@router.post(
    "/frontend",
    status_code=status.HTTP_200_OK,
    summary="Ingest frontend log batch",
    description=(
        "Accepts a batch of console/log lines from the browser along with **`userAgent`** and **`url`**. "
        "Appends to `logs/maison_frontend_log` on the server and mirrors a summary to the backend logger. "
        "Use for debugging production/staging without exposing secrets in the client bundle."
    ),
    response_description="Success message with count of lines written.",
)
async def receive_frontend_logs(log_entry: FrontendLogEntry):
    """
    Receive frontend logs and save them to maison_frontend_log file
    """
    try:
        # Ensure logs directory exists
        logs_dir = "logs"
        os.makedirs(logs_dir, exist_ok=True)

        # Path to frontend log file
        frontend_log_path = os.path.join(logs_dir, "maison_frontend_log")

        # Format the log entry
        timestamp = datetime.now().isoformat()
        header = f"\n{'='*80}\n"
        header += f"Frontend Log Entry - {timestamp}\n"
        header += f"User Agent: {log_entry.userAgent}\n"
        header += f"URL: {log_entry.url}\n"
        header += f"{'='*80}\n"

        # Write to frontend log file
        with open(frontend_log_path, "a", encoding="utf-8") as f:
            f.write(header)
            for log in log_entry.logs:
                f.write(log + "\n")
            f.write("\n")

        # Also log to backend logger for monitoring
        logger.info(f"Received {len(log_entry.logs)} frontend logs from {log_entry.url}")

        return {"status": "success", "message": f"Saved {len(log_entry.logs)} logs"}

    except Exception as e:
        logger.error(f"Failed to save frontend logs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save frontend logs")
