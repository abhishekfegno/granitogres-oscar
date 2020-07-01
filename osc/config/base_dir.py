import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _is_env_set_as(_key, _default):
    return str(os.environ.get(_key, ...)).upper() == str(_default).upper()
