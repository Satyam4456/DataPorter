import subprocess
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


def run_subprocess(
    cmd: List[str],
    timeout: Optional[int] = None,
    check: bool = True,
) -> subprocess.CompletedProcess:
    """
    Run subprocess safely.
    
    Args:
        cmd: Command and arguments as list
        timeout: Timeout in seconds
        check: Raise exception if return code != 0
        
    Returns:
        CompletedProcess object
        
    Raises:
        subprocess.CalledProcessError: If check=True and process fails
    """
    try:
        logger.debug(f"Running subprocess: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=check,
        )
        logger.debug(f"Subprocess completed with return code {result.returncode}")
        
        if result.stdout:
            logger.debug(f"Command output:\n{result.stdout}")
        
        return result
    except subprocess.TimeoutExpired as e:
        error_msg = f"Command timed out after {timeout} seconds"
        logger.error(error_msg)
        raise Exception(error_msg) from e
    except subprocess.CalledProcessError as e:
        # Capture BOTH stdout and stderr for detailed error info
        error_details = f"Command failed with exit code {e.returncode}\n"
        if e.stdout:
            error_details += f"\n--- STDOUT ---\n{e.stdout}\n"
        if e.stderr:
            error_details += f"\n--- STDERR ---\n{e.stderr}\n"
        
        logger.error(error_details)
        raise Exception(error_details) from e
    except Exception as e:
        logger.error(f"Subprocess error: {e}")
        raise Exception(f"Subprocess error: {e}") from e