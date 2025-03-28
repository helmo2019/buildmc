"""Project dependencies"""

from os.path import relpath
from zipfile import ZipFile

import json
import shutil
from abc import ABC, abstractmethod
from hashlib import sha256
from pathlib import Path
from subprocess import DEVNULL, run
from typing import Literal, Optional, TYPE_CHECKING
from uuid import uuid4 as new_uuid

import modrinth
from buildmc import config as cfg
from buildmc.util import ansi, cache_clean, cache_get, download, get_json, log, log_error, log_sub_heading, log_warn
from . import _pack_format_check as f, _project as p


_DEPLOYMENT = Literal['bundle', 'ship', 'link', 'none']


class DependencyIndex:
    """Manager class for .builmc/dependencies and index.json"""

    __index_file_name = 'index.json'
    __uuid_file_name = '.buildmc_dependency_uuid'


    def __init__(self, project: p.Project, managed_path: Path):
        """
        :param project: The project
        :param managed_path: The path to the dependencies directory
        """

        self.project = project
        self.managed_path = managed_path
        self.managed_path.mkdir(parents=True, exist_ok=True)

        # Read index data
        index_data: dict = get_json(managed_path / DependencyIndex.__index_file_name)
        if index_data is None:
            self.index: list[dict] = []
        else:
            self.index: list[dict] = index_data.get('dependencies', [])


    def __resolve_index(self):
        """
        Step one. Ensures that there are as many index entries
        as there are directories in .buildmc/dependencies, and
        that each index can be unambiguously mapped to a directory.
        """

        # Map UUID -> dir
        uuid_to_dir: dict[str, Path] = { }
        for dependency in self.managed_path.iterdir():
            if TYPE_CHECKING: dependency: Path = dependency

            if not dependency.is_dir():
                continue

            try:
                with (dependency / DependencyIndex.__uuid_file_name).open('r') as uuid_file:
                    uuid = uuid_file.read()
                    if uuid in uuid_to_dir:
                        log(f"Duplicate UUIDs for '{dependency.name}' and '{uuid_to_dir[uuid].name}. Deleting "
                            f"both.'", log_warn)
                        shutil.rmtree(dependency)
                        shutil.rmtree(uuid_to_dir[uuid])
                    else:
                        uuid_to_dir[uuid] = dependency

            except OSError:
                log(f"Unable to read UUID file in dependency files of '{dependency.name}'"
                    '. Deleting.', log_warn)
                shutil.rmtree(dependency)

        # Resolve
        for i in range(len(self.index)):
            # noinspection PyTypeChecker
            if (entry_uuid := self.index[i].get('uuid', None)) in uuid_to_dir:
                if TYPE_CHECKING:
                    entry_uuid: str = entry_uuid
                del uuid_to_dir[entry_uuid]
            else:
                log('Removing orphaned index entry '
                    + self.index[i].get('name', f'{ansi.italic}No Name{ansi.not_italic}')
                    + f' ({entry_uuid})',
                    log_warn)
                del self.index[i]
                i -= 1

        # There are now only the directories in the dict
        # that have no associated index entry. We can
        # remove them.
        for to_be_deleted in uuid_to_dir.values():
            log(f"Removing orphaned dependency files '{to_be_deleted.name}'", log_warn)
            shutil.rmtree(to_be_deleted)


    def resolve_dependencies(self):
        """
        Second step. Finds the corresponding index entry
        for each configured dependency, then acquires all
        dependencies.
        """

        self.__resolve_index()

        to_be_resolved: list[Dependency] = list(self.project.iter_dependencies())
        to_be_mapped: list[dict] = self.index.copy()
        config_to_entry: dict[Dependency, dict] = { }

        for i in range(len(to_be_resolved)):
            if i >= len(to_be_resolved):
                break
            # Try to find a fitting index entry for each configured dependency
            # 1. By name
            for j in range(len(to_be_mapped)):
                index_entry = to_be_mapped[j]
                if index_entry['name'] == to_be_resolved[i].name:
                    # Compare identity
                    if to_be_resolved[i].matches_identity(index_entry['identity']):
                        # Found a match!
                        config_to_entry[to_be_resolved[i]] = index_entry
                        del to_be_mapped[j]
                        del to_be_resolved[i]
                        i -= 1
                        break

        # There are both leftover index entries and leftover configured dependencies
        if len(to_be_resolved) > 0 and len(to_be_mapped) > 0:
            # Attempt to match them by identity
            for i in range(len(to_be_resolved)):
                if i >= len(to_be_resolved):
                    break

                dependency: Dependency = to_be_resolved[i]
                for j in range(len(to_be_resolved)):
                    index_entry: dict = to_be_mapped[j]
                    if dependency.matches_identity(index_entry['identity']):
                        # Index entry's identity matches Dependency's identity
                        # 1. Correct index & directory name
                        shutil.move(self.managed_path / index_entry['name'], self.managed_path / dependency.name)
                        index_entry['name'] = dependency.name

                        # 2. Remove from the lists and map
                        del to_be_resolved[i]
                        del to_be_mapped[j]
                        i -= 1
                        config_to_entry[dependency] = index_entry
                        break

        # There are still leftover index entries
        if len(to_be_resolved) == 0 and len(to_be_mapped) > 0:
            # Remove them along with their directories
            for leftover_entry in to_be_mapped:
                log(f"Removing unused dependency '{leftover_entry['name']}'", log_warn)
                shutil.rmtree(self.managed_path / leftover_entry['name'])

        # There are still leftover configured dependencies
        if len(to_be_resolved) > 0:
            # Acquire them
            for dep in to_be_resolved:
                log(f"Acquiring '{dep.name}'", log_sub_heading)
                dep.acquire(self.project)

                if self.project.has_failed():
                    if (dep_files := (self.managed_path / dep.name)).exists():
                        shutil.rmtree(dep_files)
                    return

                if dep.do_version_check:
                    dep.version_check(self.project)

                if self.project.has_failed():
                    return


    def save_index(self):
        """Regenerate index and UUID files"""

        dependency_list: list[dict] = []

        for dependency in self.project.iter_dependencies():
            # Regenerate UUID
            dependency_uuid = str(new_uuid())

            # Write to file
            with (self.managed_path / dependency.name / DependencyIndex.__uuid_file_name).open('w') as uuid_file:
                uuid_file.write(dependency_uuid)

            # Generate JSON
            dependency_list.append({
                'name': dependency.name,
                'identity': dependency.identity(),
                'uuid': dependency_uuid
            })

        with (self.managed_path / DependencyIndex.__index_file_name).open('w') as index_file:
            # For some reason, PyCharm says the type of index_files is
            # not correct for json.dump, but it works just fine...
            # noinspection PyTypeChecker
            json.dump({
                'dependencies': dependency_list
            }, index_file, indent=4, ensure_ascii=False)


class Dependency(ABC):
    """A project dependency"""


    @staticmethod
    def get_destination_directory() -> Path:
        """
        Get the path to place downloaded dependencies into

        :return: The path
        """

        destination: Path = cfg.global_options.buildmc_root / 'dependencies'
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


    @abstractmethod
    def identity(self) -> dict:
        """Generate the identity JSON data for this dependency"""
        pass


    @abstractmethod
    def matches_identity(self, identity: dict) -> bool:
        """
        Check whether this dependency matches the
        supplied identity from the dependency index
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
        self.path = path.expanduser().resolve()
        self.root = archive_root


    def acquire(self, project: p.Project):
        self.location = self._handle_acquired_files(project, self.path, remove_source=False,
                                                    archive_root=self.root)


    def identity(self) -> dict:
        result = {
            'type': 'local',
            'path_absolute': str(self.path.resolve()),
            'path_relative': relpath(str(self.path.resolve()), str(cfg.global_options.script_directory.resolve())),
            'file_type': 'directory' if self.path.is_dir() else 'file'
        }

        if self.root is not None and result['file_type'] == 'file':
            result['archive_root'] = str(self.root)

        return result


    def matches_identity(self, identity: dict) -> bool:
        if identity.get('type') != 'local':
            return False

        self_identity = self.identity()
        return (
            # EITHER relative or absolute path should match
                (identity.get('path_absolute') == self_identity.get('path_absolute')
                 or identity.get('path_relative') == self_identity.get('path_relative'))
                # BOTH file type and archive root need to match
                and identity.get('file_type') == self_identity.get('file_type')
                and identity.get('archive_root') == self_identity.get('archive_root')
        )


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


    def identity(self) -> dict:
        result = {
            'type': 'url',
            'url': self.url
        }

        if self.root is not None:
            result['root'] = str(self.root)

        if self.sha256_sum is not None:
            result['sha256'] = self.sha256_sum

        return result


    # TODO fix
    def matches_identity(self, identity: dict) -> bool:
        if identity.get('type') != 'url':
            return False

        if identity.get('url') == self.url:
            self_identity = self.identity()
            if (self_identity.get('root') == identity.get('root')
                    and self_identity.get('sha256') == identity.get('sha256')):
                return True

        return False


class Git(Dependency):

    def __init__(self,
                 project: p.Project,
                 name: str,
                 version_check: bool,
                 deployment: _DEPLOYMENT,
                 url: str,
                 *,
                 root: Optional[str] = None,
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
        :param root: Optional. Path inside the downloaded repository to take files from.
        :param checkout: Commit SHA1 to check out
        """

        super().__init__(project, name, version_check, deployment)
        self.url = url
        self.root = root
        self.checkout = checkout


    def acquire(self, project: p.Project):
        try:
            run(['git'], stdout=DEVNULL, stderr=DEVNULL)
        except FileNotFoundError:
            log('Git is not installed!', log_error)
            project.fail()
            return

        download_cache: Path = cache_get(Path('download'), True)
        git_dir_args = ['--git-dir', str(download_cache / '.git'), '--work-tree', str(download_cache)]

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
                    or run(['git'] + git_dir_args + ['remote', 'add', 'origin',
                                                     self.url], stderr=DEVNULL, stdout=DEVNULL).returncode != 0
                    or run(['git'] + git_dir_args + ['fetch', '--depth', '1', 'origin',
                                                     self.checkout], stderr=DEVNULL, stdout=DEVNULL) != 0
                    or run(['git', ] + git_dir_args + ['checkout', 'FETCH_HEAD'], stderr=DEVNULL,
                           stdout=DEVNULL).returncode != 0
                    or run(['git'] + git_dir_args + ['submodule', 'update', '--init',
                                                     '--recursive'], stderr=DEVNULL, stdout=DEVNULL).returncode != 0
            ):
                log(f"Unable to clone commit '{self.checkout}' from '{self.url}' using fetch method! Attempting full "
                    f"clone.", log_warn)

                cache_clean(Path('download'))

                if (run(['git', 'clone', '--depth', '1', '--recurse-submodules', '--shallow-submodules', self.url,
                         str(download_cache)], stderr=DEVNULL, stdout=DEVNULL).returncode != 0
                        or run(['git'] + git_dir_args + ['checkout', self.checkout], stderr=DEVNULL,
                               stdout=DEVNULL).returncode != 0
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


    def identity(self) -> dict:
        result = {
            'type': 'git',
            'url': self.url
        }

        if self.root is not None:
            result['root'] = str(self.root)

        if self.checkout is not None:
            result['checkout'] = self.checkout

        return result


    def matches_identity(self, identity: dict) -> bool:
        if identity.get('type') != 'git':
            return False

        self_identity = self.identity()
        return (
                self_identity.get('root') == identity.get('root')
                and self_identity.get('checkout') == identity.get('checkout')
        )


class ModrinthProject(Dependency):

    def __init__(self,
                 project: p.Project,
                 name: str,
                 version_check: bool,
                 deployment: _DEPLOYMENT,
                 id_or_slug: str,
                 *,
                 featured: Optional[bool] = True):

        super().__init__(project, name, version_check, deployment)
        raise AssertionError('Modrinth dependencies not implemented yet :)')


        # self.id_or_slug: str = id_or_slug
        # self.featured: Optional[bool] = featured
        #
        # # Get project info. Will call project.fail() if anything goes wrong
        # self.modrinth_project: modrinth.Project = modrinth.Project.from_slug(id_or_slug,
        #                                                                      options=cfg.global_options.modrinth_options)
        # if project.has_failed():
        #     return
        #
        # # Get version info. Will call project.fail() if anything goes wrong
        # matching_versions: list[modrinth.Version] = self.modrinth_project.list_versions(
        #         mc_versions=project.var_get('project/supported_versions'))
        # if project.has_failed() or len(matching_versions) == 0:
        #     # Called by list_versions if anything goes wrong (via error_callback
        #     # in config.global_options.modrinth_options)
        #     return
        # # Use last-published version
        # # TODO transitive dependencies, download optional/required resource
        # # TODO packs etc
        # TODO modrinth package manager ...
        # self.modrinth_version: modrinth.Version = max(matching_versions)
        # self.url_dependency: URL = URL(project, f'modrinth_version_{self.modrinth_version.id}',
        #                                version_check, deployment, self.modrinth_version.primary_file)




    def acquire(self, project: p.Project):
        pass


    def identity(self) -> dict:
        pass


    def matches_identity(self, identity: dict) -> bool:
        pass
