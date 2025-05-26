# utils/database.py - Conexión y utilidades de base de datos

import psycopg2
import logging

logger = logging.getLogger(__name__)

def get_db_connection():
    """Obtener conexión a la base de datos"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="caballos_db",
            user="macm1",
            password=""
        )
        return conn
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {e}")
        return None