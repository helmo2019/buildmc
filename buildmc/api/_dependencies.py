"""Classes for dependency management"""

from abc import ABC, abstractmethod

import _project

class Dependency(ABC):

    @abstractmethod
    def download(self, project: _project.Project) -> str:
        """Download the data pack file tree to a cache location & return the path."""
        pass

    @abstractmethod
    def should_update(self, project: _project.Project) -> bool:
        pass

    @abstractmethod
    def url(self) -> str:
        """Get the URL pointing to the dependency file, if possible"""
        pass
