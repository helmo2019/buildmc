"""API classes"""

from abc import ABC, abstractmethod
from glob import glob
from os import path
from typing import Any, Callable, Iterable, Literal, Optional

from buildmc import _config as cfg
from buildmc.util import log, log_error, pack_format_of


class Project(ABC):
    """A project managed by BuildMC"""

    __special_vars: dict[str, Callable[['Project'], Any]] = {
        'project/name': lambda p: p.__project_name,
        'project/version': lambda p: p.__project_version,
        'project/pack_format': lambda p: p.__pack_format,
        'project/pack_type': lambda p: p.__pack_type
    }


    def __init__(self):
        self.dependencies: dict[str, Dependency] = { }
        self.platforms: dict[str, Platform] = { }
        self.documents: dict[str, Document] = { }
        self.overlays: dict[str, Overlay] = { }

        self.__variables: dict[str, Any] = { }
        self.__project_name: Optional[str] = None
        self.__project_version: Optional[str] = None
        self.__pack_format: Optional[int] = None
        self.__pack_type: Optional[Literal['data', 'resource']] = None
        # Files to be included in the pack build. Relative to <root dir>/../
        self.__pack_files: list[str] = []


    def project_version(self, project_version: str):
        """
        Set the project version

        :param project_version: Any string
        """

        self.__project_version = project_version


    def project_name(self, project_version: str):
        """
        Set the project name

        :param project_version: Any string
        """

        self.__project_name = project_version


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
                    log(f'Looking up {self.__pack_type} pack format number for {pack_format} ...')
                    if looked_up := pack_format_of(pack_format, self.__pack_type):
                        # pack_format_of should take care of all error logging
                        self.pack_format(looked_up)

        else:
            log(f'pack_format should be int or str, but is {type(pack_format)}', log_error)


    def var_set(self, name: str, value: Any):
        """
        Safely set a variable

        :param name: The variable name. Must be a string!
        :param value: Variable value
        """

        if isinstance(name, str):
            self.__variables[name] = value
        else:
            log(f"Variable names can only be strings, but '{repr(name)}' is {type(name)}", log_error)


    def var_get(self, name: str) -> Any:
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
            return self.__variables.get(name, None)


    def var_list(self) -> Iterable[str]:
        """
        Get a set of all variable names of the project
        :return: A list containing all special variable names, followed by all custom variable names
        """

        return (list(Project.__special_vars.keys()) +
                [varname for varname in self.__variables.keys() if varname not in Project.__special_vars])


    def pack_files(self) -> Iterable[str]:
        """
        Get an iterator of all pack files. The file paths
        are relative to the directory that the build script
        is in.

        :return: The iterator
        """
        return iter(self.__pack_files)


    def include_files(self, pattern: str):
        """
        Include files in the file list of the core pack

        :param pattern: A file path. Supports UNIX style globbing (e.g. './**/*.txt')
        """

        root_dir = path.realpath(f'{cfg.buildmc_root}/../')
        self.__pack_files.extend([file for file
                                  in glob(pattern, root_dir=root_dir, recursive=True,
                                          include_hidden=True)
                                  if path.realpath(file).startswith(root_dir)
                                  and path.isfile(file) and file not in self.__pack_files
                                  ])


    def exclude_files(self, pattern: str):
        """
        Exclude files from the file list of the core pack

        :param pattern: A file path. Supports UNIX style globbing (e.g. './**/*.txt')
        """

        excluded = glob(pattern, root_dir=f'{cfg.buildmc_root}/../',
                        recursive=True, include_hidden=True)
        self.__pack_files = [entry for entry in self.__pack_files if entry not in excluded]


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
