"""Environment based configuration."""

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    api_id: int
    api_hash: str
    iway_chat: str
    session_path: Path
    dry_run: bool


def load_settings() -> Settings:
    load_dotenv()
    required = ("TELEGRAM_API_ID", "TELEGRAM_API_HASH", "IWAY_CHAT")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise ValueError(f"Missing environment variables: {', '.join(missing)}")
    try:
        api_id = int(os.environ["TELEGRAM_API_ID"])
    except ValueError as exc:
        raise ValueError("TELEGRAM_API_ID must be an integer") from exc
    dry_run_value = os.getenv("DRY_RUN", "true").strip().lower()
    if dry_run_value not in {"true", "false"}:
        raise ValueError("DRY_RUN must be true or false")
    session_path = Path(os.getenv("TELEGRAM_SESSION", "data/iway"))
    session_path.parent.mkdir(parents=True, exist_ok=True)
    return Settings(api_id, os.environ["TELEGRAM_API_HASH"], os.environ["IWAY_CHAT"], session_path, dry_run_value == "true")
