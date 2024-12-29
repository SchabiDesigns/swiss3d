import psutil

def print_memory_usage(message):
    process = psutil.Process()
    mem_info = process.memory_info()
    print(f"{message} - Memory usage: {mem_info.rss / 1024 ** 2:.2f} MB")

def memory_usage_decorator(func):
    def wrapper(*args, **kwargs):
        module_name = func.__module__
        print_memory_usage(f"{module_name}:{func.__name__} before")
        result = func(*args, **kwargs)
        print_memory_usage(f"{module_name}:{func.__name__} after")
        return result
    return wrapper