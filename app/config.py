from pydantic_settings import BaseSettings
from typing import List
import logging
import logging.handlers
import sys
from pathlib import Path


class Settings(BaseSettings):
    """Application settings and configuration"""

    # API
    app_name: str = "OCR API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    workers: int = 1

    # Gemini API
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # File Upload
    max_file_size: int = 20 * 1024 * 1024  # 20MB
    allowed_file_types: List[str] = [
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
    ]

    # CORS
    cors_enabled: bool = True
    cors_origins: List[str] = [
        "http://localhost:8000",
        "http://localhost:3000",
        "http://127.0.0.1:54422",
        "http://127.0.0.1:8000",
        "*",
    ]
    cors_credentials: bool = False
    cors_methods: List[str] = ["*"]
    cors_headers: List[str] = ["*"]

    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: str = "ocr_api.log"
    enable_file_logging: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"

    # --- Validation helpers ---

    def validate(self) -> bool:
        """Validate that all required configurations are set"""
        errors = []
        if not self.gemini_api_key:
            errors.append("GEMINI_API_KEY is not set in environment variables")
        if self.max_file_size <= 0:
            errors.append("MAX_FILE_SIZE must be greater than 0")
        if not (1 <= self.port <= 65535):
            errors.append("PORT must be between 1 and 65535")
        if errors:
            for error in errors:
                logger.error(f"Configuration Error: {error}")
            return False
        return True

    def is_file_type_allowed(self, content_type: str) -> bool:
        return content_type in self.allowed_file_types

    @property
    def max_file_size_mb(self) -> float:
        return self.max_file_size / (1024 * 1024)

    def log_summary(self) -> None:
        logger.info("=" * 60)
        logger.info("OCR API Configuration Summary")
        logger.info("=" * 60)
        logger.info(f"App: {self.app_name} v{self.app_version}")
        logger.info(f"Server: {self.host}:{self.port}")
        logger.info(f"Gemini Model: {self.gemini_model}")
        logger.info(f"Max File Size: {self.max_file_size_mb:.0f}MB")
        logger.info(f"Allowed Types: {', '.join(self.allowed_file_types)}")
        logger.info(f"CORS: {'Enabled' if self.cors_enabled else 'Disabled'}")
        logger.info("=" * 60)


settings = Settings()


# --- Logger setup ---

def _setup_logger(name: str) -> logging.Logger:
    _logger = logging.getLogger(name)
    _logger.setLevel(getattr(logging, settings.log_level))
    _logger.handlers.clear()

    formatter = logging.Formatter(settings.log_format)

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(getattr(logging, settings.log_level))
    console.setFormatter(formatter)
    _logger.addHandler(console)

    if settings.enable_file_logging:
        log_path = Path(settings.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            log_path, maxBytes=10 * 1024 * 1024, backupCount=5
        )
        file_handler.setLevel(getattr(logging, settings.log_level))
        file_handler.setFormatter(formatter)
        _logger.addHandler(file_handler)

    return _logger


logger = _setup_logger("ocr_api")
