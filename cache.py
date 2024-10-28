import os.path

cache_dir = os.path.join(os.path.dirname(__file__), 'cache')

def open_cache(file: str, mode: str):
    return open(get_file(file), mode=mode)


def exists(file: str):
    return os.path.exists(get_file(file))


def get_file(file: str):
    if not os.path.exists(cache_dir):
        os.mkdir(cache_dir)

    return os.path.join(cache_dir, file)

def remove(file: str):
    os.remove(get_file(file))