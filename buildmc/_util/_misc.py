"""Miscellaneous functions"""

from json.decoder import JSONDecodeError
from os import path
from typing import Callable

import json
import shutil


def require_file(file_path: str, type_checker: Callable[[str], bool], generator: Callable[[str], None] = None) -> str:
    """If the type_checker returns False for the file_path,
    remove the file and call the generator, if applicable"""

    if path.exists(file_path):
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


def get_json(file_path: str) -> dict | None:
    """Safely read & parse a JSON file"""

    if not path.isfile(file_path):
        return None

    with open(file_path) as file:
        try:
            return json.load(file)
        except JSONDecodeError:
            return None
