import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration shared by all environments."""

    # --- Database -----------------------------------------------------
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "smart_waste_db")

    # Falls back to SQLite so the project can be run instantly without
    # setting up MySQL first. Point DATABASE_URL at MySQL for production,
    # e.g. mysql+pymysql://user:pass@localhost:3306/smart_waste_db
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'smart_waste.db')}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Auth -----------------------------------------------------------
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-secret-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=12)
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-flask-secret")

    # --- Bin thresholds (%) ---------------------------------------------
    BIN_WARNING_THRESHOLD = 70
    BIN_FULL_THRESHOLD = 90

    # --- Uploads ----------------------------------------------------------
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB
