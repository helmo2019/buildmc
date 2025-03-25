"""Miscellaneous functions"""

from sys import stderr, stdout

import json
import shutil
from json.decoder import JSONDecodeError
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

from buildmc import config as cfg
from buildmc.util import ansi


def require_file(file_path: Path, type_checker: Callable[[Path], bool], *, generator: Callable[[Path], None] = None) \
        -> Path:
    """
    If the type_checker returns False for the file_path,
    remove the file and call the generator, if applicable

    :param file_path: The file path to check
    :param type_checker: A boolean function that takes the file path as input
    :param generator: An optional function that takes the file path as input and creates the file
    """

    if file_path.exists():
        # Remove and regenerate if file exists and is of the wrong type
        if not type_checker(file_path):
            shutil.rmtree(file_path)
            if generator is not None:
                generator(file_path)
    else:
        # Generate if file does not exist
        if generator is not None:
            generator(file_path)

    return file_path


def require_within(file: Path, containing: Path) -> Optional[Path]:
    """
    Ensure a file is at or below the given containing path.

    :param file: The file path to check
    :param containing: The directory the file should be contained in at some level
    :return: The given file path, if it's inside the project root directory, None otherwise.
    """

    if containing in file.parents:
        return file
    else:
        log(f"File '{file}' ('{file.resolve()}') is outside '{cfg.global_options.script_directory}'",
            log_error)
        return None


def require_within_project(file: Path) -> Optional[Path]:
    """
    Ensure a file is within the project root directory
    (the directory that the build script is in).

    :param file: The file path to check
    :return: The given file path, if it's inside the project root directory, None otherwise.
    """

    return require_within(file, cfg.global_options.script_directory)


def get_json(file_path: Path) -> Optional[dict]:
    """
    Safely read & parse a JSON file

    :param file_path: The JSON file's path
    :return: The parsed JSON in a dict or None if loading the file failed
    """

    if not file_path.is_file():
        return None

    with file_path.open() as file:
        try:
            return json.load(file)
        except JSONDecodeError:
            return None


def get_json_string(json_data: str) -> Optional[dict]:
    """
    Safely read & parse a JSON string

    :param json_data: The JSON data in string form
    :return: The parsed JSON in a dict or None if loading the file failed
    """

    try:
        return json.loads(json_data)
    except json.JSONDecodeError:
        return None


def any_match(items: Iterable[Any], condition: Callable[[Any], bool]) -> bool:
    for item in items:
        if condition(item):
            return True
    return False


def all_match(items: Iterable[Any], condition: Callable[[Any], bool]) -> bool:
    for item in items:
        if not condition(item):
            return False
    return True


def count_matching(items: Iterable[Any], condition: Callable[[Any], bool]) -> int:
    n = 0
    for item in items:
        if condition(item):
            n += 1
    return n


# Logging

log_info = 0
log_heading = 1
log_sub_heading = 2
log_warn = 10
log_error = 11


def log(msg: str, level: int = log_info, flush: bool = False):
    """Print styled log message to appropriate output stream"""

    print(
            (f" {ansi.bold}{ansi.green}ℹ{ansi.reset}" if level == log_info else
             f"{ansi.bold}{ansi.blue}==⇒{ansi.reset}{ansi.bold}" if level == log_heading else
             f"{ansi.light_blue}--->{ansi.reset}{ansi.bold}" if level == log_sub_heading else
             f" {ansi.yellow}⚠" if level == log_warn else
             f" {ansi.red}{ansi.bold}⮾{ansi.not_bold}")
            + f" {msg}{ansi.reset}"
            , file=stderr if level >= log_warn else stdout, flush=(flush or level >= log_warn))
