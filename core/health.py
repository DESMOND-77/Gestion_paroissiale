import logging

from django.core.cache import cache

logger = logging.getLogger(__name__)


def check_redis_health():
    """
    Check if Redis cache is available.

    Returns:
        bool: True if Redis is operational, False otherwise
    """
    try:
        cache.set("health_check", "ok", 10)
        cache.get("health_check")
        return True
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        return False


def check_database_health():
    """
    Check if database is available.

    Returns:
        bool: True if database is operational, False otherwise
    """
    try:
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return True
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        return False


def get_health_status():
    """
    Get overall health status of the application.

    Returns:
        dict: Health status of Redis and Database
    """
    return {
        "redis": check_redis_health(),
        "database": check_database_health(),
    }
