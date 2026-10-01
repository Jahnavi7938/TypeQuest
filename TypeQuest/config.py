
import os
from pathlib import Path
from dotenv import load_dotenv

# Get the project directory
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env
load_dotenv(BASE_DIR / ".env")


class Config:
    # Flask configuration
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "typequest-development-secret-key-change-this"
    )

    DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"

    # SQLite database configuration
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{(BASE_DIR / 'typequest.db').as_posix()}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Security settings
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Password and login settings
    REMEMBER_COOKIE_HTTPONLY = True

    # Application settings
    APP_NAME = "TypeQuest"
    APP_VERSION = "1.0.0"

    # Typing test default settings
    DEFAULT_TEST_DURATION = 60
    DEFAULT_WORD_COUNT = 25

    # Maximum request size (16 MB)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024