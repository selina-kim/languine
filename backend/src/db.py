"""Database connection utility for PostgreSQL."""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager


def get_db_connection():
    """
    Create and return a database connection.
    
    Returns:
        psycopg2.connection: Database connection object
    """
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    
    return psycopg2.connect(database_url)


@contextmanager
def get_db_cursor(commit=False):
    """
    Context manager for database operations.
    
    Args:
        commit: Whether to commit the transaction (default: False)
    
    Yields:
        psycopg2.cursor: Database cursor with RealDictCursor for dict-like results
    
    Example:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("INSERT INTO users ...")
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        yield cursor
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
