"""Application configuration module."""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
DEV_SECRET_KEY = "dev-secret-key-change-in-production"


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self) -> None:
        """Initialize settings from environment variables."""
        self.base_dir: Path = BASE_DIR
        self.app_env: str = os.getenv("APP_ENV", "development")

        secret = os.getenv("SECRET_KEY")
        if self.app_env == "development":
            self.secret_key: str = secret if secret else DEV_SECRET_KEY
        else:
            if not secret or secret == DEV_SECRET_KEY:
                raise RuntimeError(
                    "SECRET_KEY must be set and cannot use the development default "
                    "when APP_ENV is not 'development'"
                )
            self.secret_key = secret

        db_path_env = os.getenv("DATABASE_PATH", "data/expense_tracker.db")
        db_path = Path(db_path_env)
        if not db_path.is_absolute():
            db_path = self.base_dir / db_path
        self.database_path: Path = db_path

        self.access_token_expire_minutes: int = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
        )
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()


settings = Settings()
