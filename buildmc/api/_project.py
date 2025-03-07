from abc import ABC, abstractmethod
from typing import Any

from . import  _dependencies, _platforms, _documents, _overlay

class Project(ABC):

    def __init__(self):
        self.variables: dict[str, Any] = {}
        self.dependencies: dict[str, _dependencies.Dependency] = {}
        self.platforms: dict[str, _platforms.Platform] = {}
        self.documents: dict[str, _documents.Document] = {}
        self.overlays: dict[str, _overlay.Overlay] = {}


    @abstractmethod
    def project(self):
        """Called when initializing the project"""
        pass

    @abstractmethod
    def release_platforms(self):
        """Called by the publish task. Defines platforms to release on"""
        pass

    @abstractmethod
    def included_documents(self):
        """Called by the build task. Defines (possibly processed) documents to include in the build."""
        pass

    @abstractmethod
    def pack_overlays(self):
        """Used by patchtool. Defines the overlays that are available."""
        pass
