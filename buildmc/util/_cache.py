"""Cache management functionality"""

import shutil
from pathlib import Path
from typing import Optional

from . import _misc as m
from .. import _config as cfg


def cache_clean_all():
    """Clear all cache directories"""

    for cache_sub_dir in (cfg.buildmc_root / 'cache').iterdir():
        cache_clean(cache_sub_dir)


def cache_clean(name: Path) -> bool:
    """
    Clear a cache directory

    :param name: Path which is relative to 'buildmc_root/cache/'
    """

    # The cache *could* be a relative start with '../', but we want to
    # make sure our path stays inside 'buildmc_root/cache/'
    cache_path = m.require_within(cfg.buildmc_root / 'cache' / name, cfg.buildmc_root / 'cache')

    if cache_path is None:
        # Is None if the require_within_project check above failed
        return False
    elif not cache_path.exists():
        # If the path doesn't exist, we don't need to clean anything :)
        return True
    elif cache_path.is_file():
        # Caches should be directories, but we'll ask no questions and clean up anyway
        m.log(f"Cache '{cache_path}' should be a directory, but is a file! Removing...",
                               m.log_warn)
        cache_path.unlink()
        return True
    else:
        # The cache is a directory. This is the intended case.
        try:
            # Recursively delete the cache directory
            shutil.rmtree(cache_path)
            # Re-create the cache as an empty directory
            cache_path.mkdir()

            return True
        except shutil.Error:
            # Catch errors
            m.log(f"Unable to remove: '{cache_path}'", m.log_error)
            return False


def cache_get(name: Path, clean: bool) -> Optional[Path]:
    """
    Make sure that a cache subdirectory exists. Return the absolute path or None, depending on success.

    :param name: Name of directory inside 'buildmc/cache/'
    :param clean: Whether to call cache_clean()
    """

    # The cache *could* be a relative start with '../', but we want to
    # make sure our path stays inside 'buildmc_root/cache/'
    dir_path = m.require_within(cfg.buildmc_root / 'cache' / name, cfg.buildmc_root / 'cache')

    # Clean, if asked
    if clean and not cache_clean(name):
        return None
    # Handle existing non-directory
    elif dir_path.exists():
        if not dir_path.is_dir():
            m.log(f"Attempted to use cache subdirectory '{dir_path}', but it's a file! Removing...",
                                   m.log_error)
            if not cache_clean(name):
                return None

    # mkdirs if needed
    if not dir_path.exists():
        dir_path.mkdir(parents=True, exist_ok=True)

    return dir_path
