import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Any

logger = logging.getLogger(__name__)

class BackgroundWorker:
    """
    Lite-weight background worker using Python threading.
    Singleton pattern to share the executor across the app.
    """
    _instance = None
    _executor = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BackgroundWorker, cls).__new__(cls)
            # Initialize with a reasonable number of threads (e.g., 4 or based on CPU)
            cls._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="BackgroundWorker")
        return cls._instance

    def submit(self, fn: Callable, *args, **kwargs):
        """
        Submit a task to the background worker.
        Returns a Future object.
        """
        if self._executor is None:
            raise RuntimeError("BackgroundWorker not initialized")
        
        logger.info(f"Submitting background task: {fn.__name__}")
        return self._executor.submit(fn, *args, **kwargs)

    def shutdown(self, wait=True):
        """Shutdown the executor."""
        if self._executor:
            self._executor.shutdown(wait=wait)

# Global instance
worker = BackgroundWorker()
