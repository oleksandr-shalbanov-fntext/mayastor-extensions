import logging
import os
import subprocess
from shutil import which

from common.environment import get_env

logger = logging.getLogger(__name__)


def get_bin_path():
    bins = get_env("TEST_DIR")
    if bins:
        return os.path.join(bins, "kubectl-plugin/bin/kubectl-mayastor")
    logging.warning(f"Environmental variable 'BIN' is not set")
    return which("kubectl-mayastor")


def kubectl_mayastor(args: list[str]):
    command = [get_bin_path()]
    command.extend(args)
    logger.info(f"Running kubectl-mayastor command: {command}")

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            check=True,
            text=True,
        )
        logger.info(f"kubectl-mayastor command succeeded")
        return result.stdout.strip()

    except subprocess.CalledProcessError as e:
        logger.error(f"Error: command '{command}' failed with exit code {e.returncode}")
        logger.error(f"Error Output: {e.stderr}")
        return None

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return None
