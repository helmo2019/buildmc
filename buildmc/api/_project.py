"""Project and Project Files"""

import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Literal, Optional

from buildmc import config as cfg
from buildmc.util import Version, ansi, log, log_error, log_heading, log_warn, pack_formats_of, all_match
from . import _classes as c, dependency


class Project(ABC):
    """A project managed by BuildMC"""

    __special_vars: dict[str, Callable[['Project'], Any]] = {
        'project/name': lambda p: p.__project_name,
        'project/version': lambda p: p.__project_version,
        'project/pack_format': lambda p: p.__pack_format,
        'project/pack_type': lambda p: p.__pack_type
    }


    def __init__(self):
        # Dependency manager
        self.dependency_index = dependency.DependencyIndex(self, cfg.global_options.buildmc_root / 'dependencies')

        # Project meta
        self.__variables: dict[str, Any] = { }
        self.__project_name: Optional[str] = None
        self.__project_version: Optional[str] = None
        self.__pack_format: Optional[Version] = None
        self.__supported_pack_formats: Optional[tuple[Version, Version]] = None
        self.__pack_type: Optional[Literal['data', 'resource']] = None

        # Files to be included in the pack build. Relative to <root dir>/../
        self.__pack_files: list[ProjectFile] = []
        self.__successful: bool = True

        self.__dependencies: dict[str, 'dependency.Dependency'] = { }
        self.__platforms: dict[str, c.Platform] = { }
        self.__overlays: dict[str, c.Overlay] = { }

        self.__completed: dict[Callable, list[bool | str]] = {
            self.project: [False, 'Configuring project'],
            self.dependencies: [False, 'Configuring dependencies'],
            self.release_platforms: [False, 'Configuring platforms'],
            self.included_files: [False, 'Configuring files'],
            self.pack_overlays: [False, 'Configuring pack overlays'],
            self.dependency_index.resolve_dependencies: [False, 'Resolving dependencies']
        }


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


    def __validate_pack_format(self, pack_format: int) -> bool:
        """
        Verifies that the given pack format is valid and compatible
        with the project's pack type.
        """

        if not isinstance(pack_format, int):
            log(f"Expected type int for to-be-validated pack format, but got '{type(pack_format)}'")
            self.fail()
            return False

        if self.__pack_type == 'data':
            # Validation for data pack
            if pack_format >= 4:
                return True
            else:
                log(f'Minimum pack format for data packs is 4, but {pack_format} was given!', log_error)
                self.fail()
                return False
        else:
            # Validation for resource pack
            if pack_format >= 1:
                return True
            else:
                log(f'Minimum pack format for resource packs is 1, but {pack_format} was given!', log_error)
                self.fail()
                return False


    def pack_format(self, main: str, *, min_inclusive: Optional[str] = None, max_inclusive: Optional[str] = None):
        """
        Set the pack format number for the project. If the given
        pack_format is invalid, the project's pack format is set
        to None. Additionally, *both* min_inclusive and max_inclusive
        may be specified.

        :param main: Either a literal pack format number or a version name
        :param min_inclusive: Optional. Minimum compatible version
        :param max_inclusive: Optional. Maximum compatible version
        """

        if self.__pack_type is None:
            log("Cannot set supported pack format(s) if the pack type hasn't been set yet!", log_error)
            self.fail()
            return

        if isinstance(main, int):
            log(f'Got literal pack format number {main} as pack format. Modrinth dependencies {ansi.bold}will not'
                f" work{ansi.not_bold} if the pack format hasn't been set from a version name!", log_warn)

        if not (bool(min_inclusive) and bool(max_inclusive)) and (bool(min_inclusive) or bool(max_inclusive)):
            log(f'Incorrect usage of pack_format: Either {ansi.bold}both{ansi.not_bold} {ansi.italic}min_inclusive'
                f'{ansi.not_italic} and {ansi.italic}max_inclusive{ansi.not_italic} may be specified, {ansi.bold}or'
                f'{ansi.not_bold} neither.', log_error)
            self.fail()
            return

        if bool(min_inclusive) and bool(max_inclusive):
            resolved = pack_formats_of([main, min_inclusive, max_inclusive], self.__pack_type)

            if len(resolved) == 3 and all_match(resolved, self.__validate_pack_format):
                self.__pack_format = Version(self.__pack_type, main, resolved[0])
                self.__supported_pack_formats = (Version(self.__pack_type, min_inclusive, resolved[1]),
                                                 Version(self.__pack_type, max_inclusive, resolved[2]))
            else:
                self.fail()
        else:
            main_format = pack_formats_of([main], self.__pack_type)
            if len(main_format) == 1 and self.__validate_pack_format(main_format[0]):
                self.__pack_format = Version(self.__pack_type, main, main_format[0])
            else:
                self.fail()


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


    def iter_pack_files(self) -> Iterable['ProjectFile']:
        """
        Get an iterator of all pack files. The returned iterable
        contains tuples with two element each: The first element
        is the absolute source file path, and the second element
        is the destination file path, which is relative to the
        build cache directory 'buildmc_root/cache/build/pack'.

        :return: The iterator
        """

        return iter(self.__pack_files)


    def iter_dependencies(self) -> Iterable['dependency.Dependency']:
        """
        Get an iterator over all project dependencies.

        :return: An iterator of buildmc.api.dependency.Dependency objects
        """

        return iter(self.__dependencies.values())


    def include_files(self, pattern: str, *, process: bool = False, destination: Optional[str | Path] = None,
                      glob: bool = False):
        """
        Include files in the file list of the core pack. If

        :param pattern: A file path / pattern
        :param process: Whether variable substitution should be performed for the file
        :param destination: Where to place the files inside the output
        :param glob: Whether to enable UNIX style globbing (e.g. './**/*.txt')
        """

        included = list(cfg.global_options.script_directory.rglob(pattern)) if glob else [Path(pattern)]

        if len(included) == 0:
            log(f"No file matched the pattern '{pattern}'", log_error)
            self.fail()
            return

        for file in [file.resolve() for file in included]:
            # Make sure the file exists
            if not file.exists():
                log(f"File not found: '{file}'", log_error)
                self.fail()
                return

            # Only include files, not directories;
            # And do not include files from buildmc_root
            if not file.is_file() or (cfg.global_options.buildmc_root in file.parents):
                continue

            # Set destination correctly
            if destination is None:
                if cfg.global_options.script_directory in file.parents:
                    # File is inside the script's directory
                    destination_path = file.relative_to(cfg.global_options.script_directory)
                else:
                    # File is outside the script's directory
                    log(f"Including file which is outside of the project root: '{file.resolve()}'", log_warn)
                    destination_path = Path(file.name)
            else:
                # Print error if outside root
                if cfg.global_options.script_directory not in file.parents:
                    log(f"Including file which is outside of the project root: '{file.resolve()}'", log_warn)

                # Manually set destination
                destination_path = Path(destination) / file.name

            project_file = ProjectFile(file, destination_path, process)

            # If the file is already included, remove it first
            if project_file in self.__pack_files:
                self.__pack_files.remove(project_file)

            self.__pack_files.append(project_file)


    def exclude_files(self, pattern: str, *, by_destination: bool = False):
        """
        Exclude files from the file list of the core pack

        :param pattern: A file path. Supports UNIX style globbing (e.g. './**/*.txt')
        :param by_destination: Whether to remove pack file entries whose destination paths matches the pattern
        """

        excluded = [(file if by_destination else file.resolve()) for file in
                    cfg.global_options.script_directory.rglob(pattern)]
        self.__pack_files = [entry for entry in self.__pack_files if
                             ((by_destination and entry.destination not in excluded)
                              or (not by_destination and entry.source not in excluded))]


    def fail(self):
        """Mark this project's build as failed"""

        self.__successful = False


    def has_failed(self) -> bool:
        """
        Check whether this project's build is successful so far

        :return: Whether the build is successful so far
        """

        return not self.__successful


    def ensure_completed(self, function: Callable):
        """Ensure that a project function has been executed"""

        if self.has_failed():
            return

        if not function in self.__completed:
            log(f"Unknown state '{str(function)}'", log_error)
        else:
            state_data = self.__completed[function]
            if not state_data[0]:
                log(state_data[1], log_heading)
                function()
                state_data[0] = True


    def add_dependency(self, dep: 'dependency.Dependency'):
        """
        Add and configure a project dependency

        :param dep: The dependency itself
        """

        self.__dependencies[dep.name] = dep


    @abstractmethod
    def project(self):
        """Called when initializing the project"""
        pass


    @abstractmethod
    def dependencies(self):
        """Configures and acquires project dependencies"""
        pass


    @abstractmethod
    def release_platforms(self):
        """Called by the "publish" task. Defines platforms to release on"""
        pass


    @abstractmethod
    def included_files(self):
        """Called by the "build" task. Defines (possibly processed) documents to include in the build."""
        pass


    @abstractmethod
    def pack_overlays(self):
        """Used by "patchtool". Defines the overlays that are available."""
        pass


@dataclass
class ProjectFile:
    source: Path
    destination: Path
    process: bool = False


    def __process_and_copy(self, build_directory: Path, project: Optional[Project]):
        """
        Process the file: Substitute any '%{variable_name}'
        with the value of 'variable_name'. Expects the destination
        directory to exist.

        :param project: The project to take variable values from
        """

        with self.source.open('r') as source_file, (build_directory / self.destination).open('w') as destination_file:
            # Define operations
            buffer = ""


            def peek(characters: int = 1) -> str:
                """Read the next character(s) without advancing the file pointer"""

                current_position = source_file.tell()
                next_char = source_file.read(characters)
                source_file.seek(current_position)
                return next_char


            def consume(characters: int = 1):
                """Discard the next character"""

                source_file.read(characters)


            def pop():
                """Read the next character into the buffer"""

                nonlocal buffer
                buffer += source_file.read(1)


            def push():
                """Write the buffer into the destination file and empty it"""

                nonlocal buffer
                destination_file.write(buffer)
                buffer = ""


            while True:  # The loop is broken at appropriate points when end-of-file is reached
                # While there is no begin of a variable substitution, simply read into the buffer
                while peek(2) != '%{' and peek():
                    pop()

                # Push the buffer when we reach an opening '%{' / end-of-file
                push()

                # Break if we've reached end-of-file
                if not peek():
                    break

                # Discard the '%{'
                consume(2)

                # Read the variable name into the buffer until we hit a '}' or end-of-file
                while peek() != '}' and peek():
                    pop()

                # Reached end-of-file while looking for closing '}'
                if not peek():
                    log(f"While processing '{self.source}': Reached end-of-file while looking for closing '}}' for"
                        f" '{ansi.gray}%{{{buffer[:10]}{ansi.reset} ...'", log_error)
                    project.fail()
                    break

                # Look up variable value
                if buffer not in project.var_list():
                    log(f"While processing '{self.destination}': Unresolved variable reference '{buffer}'", log_warn)

                buffer = str(project.var_get(buffer))
                push()

                # Discard the closing '}'
                consume()


    def copy(self, build_directory: Path, project: Optional['Project'] = None):
        """
        Process the file, if required, and copy it to the destination.

        :param build_directory: The pack build directory
        :param project: The project to take variables from when processing
        """

        if project.has_failed():
            return

        # Get paths
        directory_tree = build_directory / self.destination.parent
        destination = directory_tree / self.destination.name

        # Create directories & copy file
        directory_tree.mkdir(parents=True, exist_ok=True)

        if self.process:
            self.__process_and_copy(build_directory, project)
        else:
            try:
                shutil.copyfile(self.source, destination)
            except shutil.Error:
                project.fail()


    def __eq__(self, __value):
        if isinstance(__value, ProjectFile):
            return (self.source.resolve() == __value.source.resolve()
                    and self.destination.resolve() == __value.destination.resolve())
        else:
            return False
