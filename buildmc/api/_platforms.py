"""Platforms to publish on"""

from abc import ABC, abstractmethod
from typing import Any

import _project

class Platform(ABC):

    def __init__(self):
        self.variables: dict[str, Any] = {}