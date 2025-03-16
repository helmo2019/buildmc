"""Project dependencies"""

import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Literal, Optional

from buildmc import _config as cfg
from buildmc.util import log, log_error, log_warn
from . import _project as p
from . import _pack_format_check as f


_DEPLOYMENT = Literal['bundle', 'ship', 'link', 'none']


class Dependency(ABC):
    """A project dependency"""


    @staticmethod
    def get_destination_directory() -> Path:
        """
        Get the path to place downloaded dependencies into

        :return: The path
        """

        destination: Path = cfg.buildmc_root / 'dependencies'
        if destination.exists():
            if not destination.is_dir():
                log(f"Dependency destination '{destination}' exists,"
                    f"but is not a directory! Removing...", log_warn)
                destination.unlink()
                destination.mkdir(parents=True, exist_ok=True)
        else:
            destination.mkdir()

        return destination


    def __init__(self, project: p.Project, name: str, deployment: _DEPLOYMENT):
        """
        Create a new dependency

        :param project: The project
        :param name: The dependency's name
        :param deployment: In which way the dependency should be deployed alongside the project
        """

        self.name: str = name
        self._location: Optional[Path] = None

        if deployment not in ('bundle', 'ship', 'link', 'none'):
            project.fail()
            log(f"{self.name}: Invalid deployment mode '{deployment}'", log_error)
        else:
            self.deployment = deployment


    def _handle_downloaded_files(self, project: p.Project, source: Path, *, remove_source: True) \
            -> Optional[Path]:
        """
        Validate the acquired and unpacked files and move
        them from a temporary location to the final destination.
        If any error occurs, project.fail() is called and
        the function returns.

        :param project: The project
        :param source: Path where the files currently are
        :param remove_source: Whether to delete the source files afterward
        """

        # Validate source
        if not (source / 'pack.mcmeta').is_file():
            log(f"Dependency '{self.name}' is missing pack.mcmeta!", log_error)
            project.fail()
            return None

        # Return (for now) if the destination already exists
        destination: Path = Dependency.get_destination_directory() / self.name
        if destination.exists():
            # TODO: Implement dependency index which keeps
            # TODO:  track of which dependencies have been
            # TODO:  downloaded and where. Add a '.buildmc_dep'
            # TODO:  file inside the downloaded dependency
            # TODO:  which contains a UUID. If destination.is_dir(),
            # TODO:  the correct UUID is looked up in the index.
            # TODO:  If the UUID is different or absent from
            # TODO:  the index, the dependency is re-acquired.
            log(f"Dependency '{self.name}' already acquired")
            return destination

        # Move / copy files
        try:
            if remove_source:
                shutil.move(source, destination)
            else:
                shutil.copytree(source, destination)
            return destination
        except shutil.Error as err:
            log(f"Failed to place files for dependency '{self.name}' into '{destination}': {err}",
                log_error)
            project.fail()
            return None


    @abstractmethod
    def acquire(self, project: p.Project):
        """Download the data pack file tree to a cache location & return the path."""
        pass


    def get_location(self) -> Optional[Path]:
        """
        Get the location of the downloaded and unpacked dependency,
        which is the directory containing pack.mcmeta.

        :return: The final location of the acquired files
        """
        return self._location


    def version_check(self, project: p.Project):
        """
        Make sure this dependency is compatible with
        the project. If it is not or there is an error
        at any point, project.fail() is called.

        :param project: The current project
        """

        f.pack_format_compatible(f"Compatibility check for dependency '{self.name}' failed: ",
                               (self.get_location() / 'pack.mcmeta').resolve(), project)


class _Local(Dependency):

    def __init__(self,
                 project: p.Project,
                 name: str,
                 deployment: _DEPLOYMENT,
                 path: Path
                 ):
        super().__init__(project, name, deployment)
        self.path = path.resolve()


    def acquire(self, project: p.Project):
        self._location = self._handle_downloaded_files(project, self.path, remove_source=False)

Dependency.Local = _Local
