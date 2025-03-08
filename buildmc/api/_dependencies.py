"""Classes for dependency management"""

from abc import ABC, abstractmethod

from buildmc import api

# TODO stop coding Java but it's python. There can be *multiple classes per file*.

class Dependency(ABC):

    @abstractmethod
    def download(self, project: api.Project) -> str:
        """Download the data pack file tree to a cache location & return the path."""
        pass

    @abstractmethod
    def should_update(self, project: api.Project) -> bool:
        pass

    @abstractmethod
    def url(self) -> str:
        """Get the URL pointing to the dependency file, if possible"""
        pass
