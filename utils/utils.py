import os
import logging

from pid import PidFile

logger = logging.getLogger(__name__)

def check_running(function_name):
    if not os.path.exists('/tmp'):
        os.mkdir('/tmp')
    file_lock = PidFile(str(function_name), piddir='/tmp')
    file_lock.create()
    return file_lock


def stop_duplicate_task(func):
    def inner_function():
        try:
            file_lock = check_running(func.__name__)
        except:
            logger.error(f"[Another {func.__name__} is already running]")
            return

        func()

        if file_lock:
            file_lock.close()

    return inner_function
