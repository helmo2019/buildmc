"""Project tasks"""

from pathlib import Path
from typing import Callable, Iterable, Union
from zipfile import ZipFile

from buildmc.util import ansi, cache_clean_all, cache_get, log, log_heading, cache_clean
from . import _project as p


def clean(_):
    """Clean all caches"""
    log('Cleaning caches', log_heading)
    cache_clean_all()


def variables(project: p.Project):
    """Print out project variables"""

    project.ensure_completed(project.project)

    if project.has_failed():
        return

    log(f'Project variables:{ansi.reset}' + (''.join(
            [
                (
                        f"\n  {ansi.gray}'{var_name}'{ansi.reset} = " +
                        (', '.join(map(str, project.var_get(var_name)))
                         if isinstance(project.var_get(var_name), list|tuple) else
                         str(project.var_get(var_name)))
                )
                for var_name in project.var_list()
            ]
    )), log_heading)


def files(project: p.Project):
    """Print out files included in project build"""

    project.ensure_completed(project.included_files)

    if project.has_failed():
        return

    log(f'Project files:{ansi.reset}' + (''.join(
            [f"\n  {ansi.gray}'{project_file.source}'{ansi.reset}\n   → "
             f"'{project_file.destination}'"
             f"{f'{ansi.purple} (processed){ansi.reset}' if project_file.process else ''}"
             for project_file in project.iter_pack_files()]
    )), log_heading)


def build(project: p.Project):
    """Assemble ZIP file"""

    project.ensure_completed(project.project)
    project.ensure_completed(project.included_files)
    project.ensure_completed(project.dependencies)

    if project.has_failed():
        return

    if not project.has_failed():
        log(f'Building project {project.var_get("project/name")}', log_heading)

        build_cache = cache_get(Path('build'), True)
        core_pack_build_cache = cache_get(Path('build', 'pack'), False)

        # Copy files
        log('Copying & processing included files')

        for file in project.iter_pack_files():
            file.copy(core_pack_build_cache, project)

        if not project.has_failed():
            # Create ZIP
            log('Assembling ZIP file')

            zip_file_path = build_cache / (f'{project.var_get("project/name")}'
                                           f'-{project.var_get("project/version")}.zip')

            with ZipFile(zip_file_path, 'w') as zip_file:
                for pack_file in project.iter_pack_files():
                    zip_file.write(core_pack_build_cache / pack_file.destination,
                                   arcname=str(pack_file.destination))


def dependencies(project: p.Project):
    """Configure & acquire project dependencies"""

    project.ensure_completed(project.project)
    project.ensure_completed(project.dependencies)
    project.ensure_completed(project.dependency_index.resolve_dependencies)


def post(project: p.Project):
    """Runs after all other tasks"""

    project.dependency_index.save_index()

    cache_clean(Path('download'))
    cache_clean(Path('unpack'))
    cache_clean(Path('unpack2'))


TASKS = Union[clean, variables, files, build, dependencies]
task_map: dict[str, Callable] = {
    'clean': clean,
    'variables': variables,
    'files': files,
    'build': build,
    'dependencies': dependencies
}
