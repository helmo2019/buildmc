"""API classes"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Literal, Optional

from buildmc.util import log, log_error, pack_format_of


class Project(ABC):
    """A project managed by BuildMC"""

    __special_vars: dict[str, Callable[['Project'], Any]] = {
        'project/version': lambda p: p.project_version,
        'project/pack_format': lambda p: p.__pack_format,
        'project/pack_type': lambda p: p.__pack_type
    }


    def __init__(self):
        self.variables: dict[str, Any] = { }
        self.dependencies: dict[str, Dependency] = { }
        self.platforms: dict[str, Platform] = { }
        self.documents: dict[str, Document] = { }
        self.overlays: dict[str, Overlay] = { }

        self.project_version: Optional[str] = None

        self.__pack_format: Optional[int] = None
        self.__pack_type: Optional[Literal['data', 'resource']] = None


    def pack_type(self, pack_type: str):
        """
        Set the project's pack type

        :param pack_type: Either 'data' or 'resource'
        :raise ValueError: If the given pack_type is invalid
        """

        if pack_type in ('data', 'resource'):
            self.__pack_type = pack_type
        else:
            log(f"Invalid pack type '{pack_type}', expected 'data' or 'resource'", log_error)


    def pack_format(self, pack_format: int | str):
        """
        Set the pack format number for the project. If the given
        pack_format is invalid, the project's pack format is set
        to None.

        :param pack_format: Either a literal pack format number or a version name
        """

        if isinstance(pack_format, int) or isinstance(pack_format, str):
            if self.__pack_type is None:
                log("Cannot set the project's pack format if the project's pack type is not yet defined!", log_error)
            else:
                if isinstance(pack_format, int):
                    # Literal pack format
                    if self.__pack_type == 'data':
                        # Validation for data pack
                        if pack_format >= 4:
                            self.__pack_format = pack_format
                        else:
                            log(f'Minimum pack format for data packs is 4, but {pack_format} was given. Value remains '
                                f'at '
                                f'{self.__pack_format}',
                                log_error)
                    else:
                        # Validation for resource pack
                        if pack_format >= 1:
                            self.__pack_format = pack_format
                        else:
                            log(f'Minimum pack format for resource packs is 0, but {pack_format} was given. Value '
                                f'remains at '
                                f'{self.__pack_format}', log_error)
                elif isinstance(pack_format, str):
                    # Version name
                    if looked_up := pack_format_of(pack_format, self.__pack_type):
                        # pack_format_of should take care of all error logging
                        self.pack_format(looked_up)

        else:
            log(f'pack_format should be int or str, but is {type(pack_format)}', log_error)


    def var(self, name: str) -> Any:
        """
        Read a project variable. The given name is first looked up in the list
        of special variables ('project/version', 'project/pack_format',
        'project/pack_type'), then in the Project object's variables attribute.

        :param name: The name of the variable to look up
        :return: The value of the variable, or None if it's not found
        """

        if name in Project.__special_vars:
            return Project.__special_vars[name](self)
        else:
            return self.variables.get(name, None)


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


class Dependency(ABC):
    """A project dependency"""


    @abstractmethod
    def __init__(self):
        pass


    @abstractmethod
    def download(self, project: Project) -> str:
        """Download the data pack file tree to a cache location & return the path."""
        pass


    @abstractmethod
    def should_update(self, project: Project) -> bool:
        pass


    @abstractmethod
    def url(self) -> str:
        """Get the URL pointing to the dependency file, if possible"""
        pass


class Platform(ABC):

    def __init__(self):
        self.variables: dict[str, Any] = { }


class Document(ABC):
    """A possible processed document"""


    @abstractmethod
    def __init__(self):
        pass


class Overlay(ABC):
    """A managed pack overlay"""


    @abstractmethod
    def __init__(self):
        pass
