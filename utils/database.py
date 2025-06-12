"""Database connection utilities."""
import os
import logging
import psycopg2

logger = logging.getLogger(__name__)


def get_db_connection():
    """Get a PostgreSQL database connection using environment variables."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            database=os.getenv("DB_NAME", "caballos_db"),
            user=os.getenv("DB_USER", "macm1"),
            password=os.getenv("DB_PASSWORD", ""),
        )
        return conn
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {e}")
        return None
