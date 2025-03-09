"""Cache management functionality"""

import os
import shutil
from os import makedirs, path
from typing import Optional

from . import _logging as l
from .. import _config as cfg


def cache_clean_all():
    """Clear all cache directories"""

    for cache_sub_dir in os.listdir(f"{cfg.buildmc_root}/cache/"):
        cache_clean(cache_sub_dir)


def cache_clean(name: str) -> bool:
    """
    Clear a cache directory

    :param name: Name of directory inside 'buildmc/cache/'
    """

    cache_path = f"{cfg.buildmc_root}/cache/{name}"

    try:
        shutil.rmtree(cache_path)
        return True
    except shutil.Error:
        l.log(f"Unable to remove: '{cache_path}'", l.log_error)
        return False


def cache_get(name: str, clean: bool) -> Optional[str]:
    """
    Make sure that a cache subdirectory exists. Return the absolute path or None, depending on success.

    :param name: Name of directory inside 'buildmc/cache/'
    :param clean: Whether to call cache_clean()
    """

    dir_path = path.realpath(f"{cfg.buildmc_root}/cache/{name}")

    # Clean, if asked
    if clean and not cache_clean(name):
        return None
    # Handle existing non-directory
    elif path.exists(dir_path):
        if not path.isdir(dir_path):
            l.log(f"Attempted to use cache subdirectory '{dir_path}', but is a file! Removing...", l.log_error)
            if not cache_clean(name):
                return None

    # mkdirs if needed
    if not path.exists(dir_path):
        makedirs(dir_path, exist_ok=True)

    return dir_path
