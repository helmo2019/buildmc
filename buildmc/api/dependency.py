"""Project dependencies"""

import shutil
from abc import ABC, abstractmethod
from hashlib import sha256
from pathlib import Path
from subprocess import run, DEVNULL
from typing import Literal, Optional
from zipfile import ZipFile

from buildmc import _config as cfg
from buildmc.util import cache_clean, cache_get, download, log, log_error, log_warn
from . import _pack_format_check as f, _project as p


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


    @abstractmethod
    def __init__(self, project: p.Project, name: str, version_check: bool, deployment: _DEPLOYMENT):
        """
        :param project: The project
        :param name: Name of the dependency
        :param version_check: Whether a compatibility check should be performed when acquiring
        :param deployment: In which way the dependency should be deployed alongside the project
        """

        self.name: str = name
        self.do_version_check = version_check
        self.location: Optional[Path] = None

        if deployment not in ('bundle', 'ship', 'link', 'none'):
            project.fail()
            log(f"{self.name}: Invalid deployment mode '{deployment}'", log_error)
        else:
            self.deployment = deployment


    @abstractmethod
    def acquire(self, project: p.Project):
        """
        Download the data pack file tree to a cache location & return the path.
        If any errors occur, project.fail() is called and the function returns.
        """
        pass


    def _handle_acquired_files(self, project: p.Project, source: Path, *,
                               remove_source = True, archive_root: Optional[Path] = None) -> Optional[Path]:
        """
        Unpacks the acquired file, if appropriate. Then
        validates and moves them, possibly from a temporary
        location, to the final destination. If any errors
        occur, project.fail() is called and the function returns.

        :param project: The project
        :param source: Path where the files currently are
        :param remove_source: Whether to delete the source files afterward
        """

        # Unpack, if required
        if source.is_file():
            unpack_working_dir = cache_get(Path('unpack'), True)
            archive_root_path: Optional[Path] = (Path(unpack_working_dir, archive_root).resolve()
                                                 if archive_root is not None else None)

            with (ZipFile(source) as archive):
                # Get list of all files in the archive
                archive_files: list[str] = [zip_member.filename for zip_member in archive.infolist()
                                            if not zip_member.is_dir()]
                # Make sure that pack.mcmeta is in the archive
                if f'{str(archive_root) + "/" if archive_root is not None else ""}pack.mcmeta' not in archive_files:
                    log(f"Dependency '{self.name}' is missing pack.mcmeta!", log_error)
                    project.fail()
                    return None
                # Extract files
                for archive_file_name in archive_files:
                    file_destination: Path = (unpack_working_dir / archive_file_name).resolve()

                    if archive_root is not None:
                        if archive_root_path not in file_destination.parents:
                            continue
                        else:
                            file_destination = (unpack_working_dir
                                                / file_destination.relative_to(archive_root_path))

                    if not unpack_working_dir in file_destination.parents:
                        log(f"Skipping file '{archive_file_name}' from dependency '{self.name}'"
                            "as it would be placed outside of the dependency directory", log_warn)
                    else:
                        file_destination.parent.mkdir(parents=True, exist_ok=True)

                        if archive_root is not None:
                            extracted_path = archive.extract(archive_file_name, cache_get(Path('unpack2'),
                                                                                          True))
                            shutil.copy(extracted_path, file_destination)
                        else:
                            archive.extract(archive_file_name, file_destination)

            source = unpack_working_dir

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


    def version_check(self, project: p.Project):
        """
        Make sure this dependency is compatible with
        the project. If it is not or there is an error
        at any point, project.fail() is called.

        :param project: The current project
        """

        if self.location is not None:
            f.pack_format_compatible(f"Compatibility check for dependency '{self.name}' failed: ",
                                     (self.location / 'pack.mcmeta').resolve(), project)


class Local(Dependency):

    def __init__(self,
                 project: p.Project,
                 name: str,
                 version_check: bool,
                 deployment: _DEPLOYMENT,
                 path: Path, *,
                 archive_root: Optional[Path] = None):
        """
        Configure a local file dependency. The path may be a normal
        directory or a ZIP file. If it's a directory, it has to
        contain pack.mcmeta at top-level. The same goes for ZIP
        archives except for the archive_root parameter, which
        allows specifying a directory inside the archive to take
        the files from.

        :param project: The project
        :param name: Name of the dependency
        :param version_check: Whether a compatibility check should be performed when acquiring
        :param deployment: In which way the dependency should be deployed alongside the project
        :param path: Path to the directory or ZIP archive
        :param archive_root: ZIP file only. Path inside the archive to take files from.
        """
        super().__init__(project, name, version_check, deployment)
        self.path = path.resolve()
        self.root = archive_root


    def acquire(self, project: p.Project):
        self.location = self._handle_acquired_files(project, self.path, remove_source=False,
                                                    archive_root=self.root)


class URL(Dependency):

    def __init__(self,
                 project: p.Project,
                 name: str,
                 version_check: bool,
                 deployment: _DEPLOYMENT,
                 url: str,
                 *,
                 root: Optional[Path] = None,
                 sha256_sum: Optional[str] = None):
        """
        Configure a dependency downloaded from a URL. The URL
        has to point to a ZIP archive which should contain
        pack.mcmeta on the top-level. If it does not, the
        optional root parameter may be used to specify from
        where inside the archive the files should be taken from.

        :param project: The project
        :param name: Name of the dependency
        :param version_check: Whether a compatibility check should be performed when acquiring
        :param deployment: In which way the dependency should be deployed alongside the project
        :param url: Download URL
        :param root: Optional. Path inside the downloaded archive to take files from.
        :param sha256_sum: Optional. SHA256 checksum for download verification.
        """

        super().__init__(project, name, version_check, deployment)
        self.url = url
        self.root = root
        self.sha256_sum = sha256_sum


    def acquire(self, project: p.Project):
        download_location: Path = cache_get(Path('download'), True) / 'download_file.zip'
        with download_location.open('wb') as download_file:
            if not download(download_file, self.url, checksum=self.sha256_sum, checksum_algorithm=sha256):
                log(f"Unable to acquire dependency '{self.name}'", log_error)
                project.fail()
                return
        self.location = self._handle_acquired_files(project, download_location, archive_root=self.root)


class Git(Dependency):

    def __init__(self,
                 project: p.Project,
                 name: str,
                 version_check: bool,
                 deployment: _DEPLOYMENT,
                 url: str,
                 *,
                 location: Optional[str] = None,
                 checkout: Optional[str] = None):
        """
        Configure a dependency downloaded from Git repository.
        The repository should contain pack.mcmeta on the top-level.
        If it does not, the optional location parameter may be used
        to specify from where inside the repository the files should
        be taken from.

        :param project: The project
        :param name: Name of the dependency
        :param version_check: Whether a compatibility check should be performed when acquiring
        :param deployment: In which way the dependency should be deployed alongside the project
        :param url: Download URL
        :param location: Optional. Path inside the downloaded repository to take files from.
        :param checkout: Commit SHA1 to check out
        """

        super().__init__(project, name, version_check, deployment)
        self.url = url
        self.root = location
        self.checkout = checkout


    def acquire(self, project: p.Project):
        download_cache: Path = cache_get(Path('download'), True)
        git_dir_args = ['--git-dir',str(download_cache / '.git'),'--work-tree',str(download_cache)]

        if self.checkout is None:
            # Check out latest commit
            if run([
                # Clone only the latest commit
                # https://stackoverflow.com/questions/1209999/how-to-use-git-to-get-just-the-latest-revision-of-a
                # -project
                'git', 'clone', '--depth', '1', '--recurse-submodules', '--shallow-submodules',
                self.url,
                str(download_cache)
            ], stdout=DEVNULL, stderr=DEVNULL).returncode != 0:
                log(f"Unable to clone Git repository '{self.url}'", log_error)
                project.fail()
                return
        else:
            # Check out specific commit
            # https://stackoverflow.com/questions/31278902/how-to-shallow-clone-a-specific-commit-with-depth-1
            # Method 1, requires uploadpack.allowReachableSHA1InWant=true on client and server
            cache_clean(Path('download'))
            if (run(['git', 'init', str(download_cache)], stderr=DEVNULL, stdout=DEVNULL).returncode != 0
                    or run(['git']+git_dir_args+['remote', 'add', 'origin',
                            self.url], stderr=DEVNULL, stdout=DEVNULL).returncode != 0
                    or run(['git']+git_dir_args+['fetch', '--depth', '1', 'origin',
                            self.checkout], stderr=DEVNULL, stdout=DEVNULL) != 0
                    or run(['git',]+git_dir_args+['checkout', 'FETCH_HEAD'], stderr=DEVNULL, stdout=DEVNULL).returncode != 0
                    or run(['git']+git_dir_args+['submodule', 'update', '--init',
                            '--recursive'], stderr=DEVNULL, stdout=DEVNULL).returncode != 0
            ):
                log(f"Unable to clone commit '{self.checkout}' from '{self.url}' using fetch method! Attempting full "
                    f"clone.", log_warn)

                cache_clean(Path('download'))

                if (run(['git', 'clone', '--depth', '1', '--recurse-submodules', '--shallow-submodules', self.url,
                         str(download_cache)], stderr=DEVNULL, stdout=DEVNULL).returncode != 0
                        or run(['git']+git_dir_args+['checkout', self.checkout], stderr=DEVNULL, stdout=DEVNULL).returncode != 0
                ):
                    log(f"Unable to clone Git repository '{self.url}' and check out commit '{self.checkout}'!",
                        log_error)
                    project.fail()
                    return

        copy_source: Path = download_cache if self.root is None else download_cache / self.root
        if not copy_source.is_dir():
            log(f"No such directory '{self.location}' in Git repository '{self.url}'", log_error)
            project.fail()
            return

        self.location = self._handle_acquired_files(project, copy_source)
