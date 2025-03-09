"""Miscellaneous functions"""

import json
import shutil
from json.decoder import JSONDecodeError
from os import path
from typing import Callable, Optional


def require_file(file_path: str, type_checker: Callable[[str], bool], generator: Callable[[str], None] = None) -> str:
    """
    If the type_checker returns False for the file_path,
    remove the file and call the generator, if applicable

    :param file_path: The file path to check
    :param type_checker: A boolean function that takes the file path as input
    :param generator: An optional function that takes the file path as input and creates the file
    """

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


def get_json(file_path: str) -> Optional[dict]:
    """
    Safely read & parse a JSON file

    :param file_path: The JSON file's path
    :return: The parsed JSON in a dict or None if loading the file failed
    """

    if not path.isfile(file_path):
        return None

    with open(file_path) as file:
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
