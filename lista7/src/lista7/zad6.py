import logging
import time
import functools
import inspect
from datetime import datetime
import logging
import time


def log(log_level=logging.INFO):
    def decorator_wrapper(target_object):
        if inspect.isclass(target_object):
            original_init = target_object.__init__
            
            @functools.wraps(original_init)
            def patched_init(self, *args, **kwargs):
                logging.log(log_level, f"instantiated class: {target_object.__name__}")
                original_init(self, *args, **kwargs)
                
            target_object.__init__ = patched_init
            return target_object
            
        else:
            @functools.wraps(target_object)
            def function_wrapper(*args, **kwargs):
                call_timestamp = datetime.now()
                start_time = time.perf_counter()
                
                function_result = target_object(*args, **kwargs)
                
                execution_duration = time.perf_counter() - start_time
                
                logging.log(
                    log_level,
                    f"call time: {call_timestamp} | "
                    f"duration: {execution_duration:.5f}s | "
                    f"function: {target_object.__name__} | "
                    f"args: {args} | "
                    f"kwargs: {kwargs} | "
                    f"return: {function_result}"
                )
                return function_result
            return function_wrapper
            
    return decorator_wrapper


@log(log_level=logging.DEBUG)
def calculate_product(a, b, multiplier=1):
    time.sleep(0.1)
    return (a * b) * multiplier

@log(log_level=logging.INFO)
class UserProfile:
    def __init__(self, username, role="user"):
        self.username = username
        self.role = role


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(levelname)s - %(message)s"
    )
    
    calculate_product(5, 4, multiplier=2)
    calculate_product(10, 10)
    
    UserProfile("admin_john", role="admin")
    UserProfile("guest_anna")