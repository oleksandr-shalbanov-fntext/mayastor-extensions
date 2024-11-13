import logging
import os

logger = logging.getLogger(__name__)


def get_env(variable: str):
    try:
        value = os.getenv(variable)
        if len(value) == 0:
            raise ValueError("Env {variable} is empty")
        logger.info(f"Found env {variable}={value}")
        return value

    except Exception as e:
        logger.error(f"Failed to get env {variable}: {e}")
        return None
