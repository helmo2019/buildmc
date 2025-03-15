"""API classes"""

from abc import ABC, abstractmethod
from typing import Any

from . import _project as p


class Dependency(ABC):
    """A project dependency"""


    @abstractmethod
    def __init__(self):
        pass


    @abstractmethod
    def download(self, project: p.Project) -> str:
        """Download the data pack file tree to a cache location & return the path."""
        pass


    @abstractmethod
    def should_update(self, project: p.Project) -> bool:
        pass


    @abstractmethod
    def url(self) -> str:
        """Get the URL pointing to the dependency file, if possible"""
        pass


class Platform(ABC):

    def __init__(self):
        self.variables: dict[str, Any] = { }


class Overlay(ABC):
    """A managed pack overlay"""


    @abstractmethod
    def __init__(self):
        pass
