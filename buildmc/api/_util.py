"""Utility functions"""
import os
import shutil

from json import load as json_load
from os import path, makedirs
from sys import stdout, stderr

from . import _config as cfg

__min_pack_format = 4

_log_info = 0
_log_warn = 1
_log_error = 2

def _ansi(seq: str) -> str:
    return f"\033[{seq}m"

_f = {
    "r": _ansi("0"),    # Reset
    "b": _ansi("1"),    # Bold
    "n": _ansi("22"),   # Normal intensity
    "yellow": _ansi("38;2;219;185;42"), # Custom yellow
    "red": _ansi("38;2;221;42;84")      # Custom red
}

def _log(msg: str, level: int = 0):
    """Print styled log message to appropriate output stream"""
    print(
        (f"{_f["b"]}ℹ{_f["n"]}" if level == _log_info else
        f"⚠{_f["yellow"]}" if level == _log_warn else
        f"{_f["red"]}{_f["b"]}⮾{_f["n"]}")
        +f" {msg}{_f["r"]}"
    , file=stderr if level > _log_info else stdout)

def _cache_clean_all():
    for cache_sub_dir in os.listdir(f"{cfg.buildmc_root}/cache/"):
        _cache_clean(cache_sub_dir)

def _cache_clean(name: str) -> bool:
    cache_path = f"{cfg.buildmc_root}/cache/{name}"

    try:
        shutil.rmtree(cache_path)
        return True
    except shutil.Error:
        _log(f"Unable to remove: '{cache_path}'", _log_error)
        return False

def _cache_get(name: str, clean: bool) -> str | None:
    """Make sure that a cache sub-directory exists. Return the absolute path or None, depending on success."""

    dir_path = f"{cfg.buildmc_root}/cache/{name}"

    # Clean, if asked
    if clean and not _cache_clean(name):
        return None
    # Handle existing non-directory
    elif path.exists(dir_path):
        if not path.isdir(dir_path):
            _log(f"Attempted to use cache subdirectory '{dir_path}', but is a file! Removing...", _log_error)
            if not _cache_clean(name):
                return None

    # mkdirs if needed
    if not path.exists(dir_path):
        makedirs(dir_path, exist_ok=True)

    return dir_path

def _version_meta_of(version_name: str) -> dict|None:
    if (data_file := _cache_version_meta()) is None:
        return None

    # File exists
    if path.isfile(data_file):
        with open(data_file) as file:
            json_data = json_load(file)



def _cache_version_meta() -> str|None:
    # Make sure the cache directory exists
    if (cache_dir := _cache_get("meta_extrator")) is None:
        return None

    data_file = f"{cache_dir}/version_meta.json"

    # File already exists
    if path.isfile()

def pack_version_of(version: str|int) -> int|None:
    if isinstance(version, int)
