from abc import ABC, abstractmethod
from typing import Any

class Project(ABC):

    def __init__(self):
        from buildmc import api
        self.variables: dict[str, Any] = {}
        self.dependencies: dict[str, api.Dependency] = {}
        self.platforms: dict[str, api.Platform] = {}
        self.documents: dict[str, api.Document] = {}
        self.overlays: dict[str, api.Overlay] = {}


    @abstractmethod
    def project(self):
        """Called when initializing the project"""
        pass

    @abstractmethod
    def release_platforms(self):
        """Called by the "publish" task. Defines platforms to release on"""
        pass

    @abstractmethod
    def included_documents(self):
        """Called by the "build" task. Defines (possibly processed) documents to include in the build."""
        pass

    @abstractmethod
    def pack_overlays(self):
        """Used by "patchtool". Defines the overlays that are available."""
        pass
