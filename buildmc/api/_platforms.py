"""Platforms to publish on"""

from abc import ABC, abstractmethod
from typing import Any

class Platform(ABC):

    def __init__(self):
        self.variables: dict[str, Any] = {}