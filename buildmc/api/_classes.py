"""API classes"""

from abc import ABC, abstractmethod
from typing import Any


class Platform(ABC):

    def __init__(self):
        self.variables: dict[str, Any] = { }


class Overlay(ABC):
    """A managed pack overlay"""


    @abstractmethod
    def __init__(self):
        pass
