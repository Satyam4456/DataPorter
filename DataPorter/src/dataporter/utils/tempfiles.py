import tempfile
import os
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


@contextmanager
def safe_temp_file(suffix='', prefix='tmp', mode='w', delete=False, dir=None):
    """
    Context manager for safe temp file creation and cleanup.
    
    Args:
        suffix: File suffix
        prefix: File prefix
        mode: File open mode
        delete: Delete on exit
        dir: Temp directory
        
    Yields:
        File object
    """
    tmp = tempfile.NamedTemporaryFile(
        mode=mode,
        suffix=suffix,
        prefix=prefix,
        delete=delete,
        dir=dir,
    )
    
    try:
        logger.debug(f"Created temp file: {tmp.name}")
        yield tmp
    finally:
        tmp.close()
        if os.path.exists(tmp.name) and delete:
            try:
                os.unlink(tmp.name)
                logger.debug(f"Cleaned up temp file: {tmp.name}")
            except Exception as e:
                logger.warning(f"Failed to clean temp file {tmp.name}: {e}")


def create_temp_file(suffix='', prefix='tmp', dir=None) -> str:
    """
    Create a temporary file path.
    
    Args:
        suffix: File suffix
        prefix: File prefix
        dir: Temp directory
        
    Returns:
        Path to temp file
    """
    tmp = tempfile.NamedTemporaryFile(
        suffix=suffix,
        prefix=prefix,
        dir=dir,
        delete=False,
    )
    tmp.close()
    logger.debug(f"Created temp file: {tmp.name}")
    return tmp.name