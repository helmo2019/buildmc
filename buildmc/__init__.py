from os import chdir
from os.path import basename
from pathlib import Path
from shutil import copyfile
from sys import argv, exit
from typing import Type
from zipfile import ZipFile

from buildmc import _config as cfg, api, util


_faint = '\033[2m'
_gray = '\033[38;2;150;150;150m'
_reset = '\033[0m'

_valid_tasks = ('help', 'clean', 'variables', 'files', 'build')


def main(project_class: Type[api.Project], build_script_file_name: str):
    """
    Start BuildMC for a project

    :param project_class: A class extending buildmc.api.Project
    :param build_script_file_name: File path of the build script, obtained with __file__
    """

    # Set root directory
    cfg.reset()

    cfg.script_directory = Path(build_script_file_name).parent
    cfg.buildmc_root = cfg.script_directory / 'buildmc_root'
    chdir(str(cfg.script_directory.resolve()))

    # Configure project
    project = project_class()

    # Store project state to prevent some
    # project functions being called twice
    # when they're needed in multiple
    # tasks that are called consecutively
    project_state: dict[str, bool] = {
        'project_configured': False,
        'files_configured': False
    }


    def ensure_state(name: str, function):
        if not project_state[name]:
            function()
            project_state[name] = True


    def show_help():
        """Print help and exit"""

        util.log(
                f"Usage: {basename(build_script_file_name)} task...\n"
                "  Available tasks are:\n"
                "   help        Show this help and exit\n"
                "   clean       Clean all caches\n"
                "   variables   Print out project variables\n"
                "   files       Print out files included in the build\n"
                "   build       Build the project"
        )
        exit()


    # Execute commands

    # Show help, if appropriate
    if len(argv[1:]) == 0 or 'help' in argv[1:] or len([task for task in argv[1:]
                                                        if task not in _valid_tasks]) != 0:
        show_help()

    for command in argv[1:]:
        match command:
            case 'clean':
                # Clean all caches
                util.cache_clean_all()
            case 'variables':
                # Print project variables

                ensure_state('project_configured', project.project)

                util.log('Project variables:' + (''.join(
                        [f"\n  {_gray}'{var_name}'{_reset} = {repr(project.var_get(var_name))}"
                         for var_name in project.var_list()]
                )))
            case 'files':
                # Print included files

                ensure_state('project_configured', project.project)
                ensure_state('files_configured', project.included_files)

                util.log('Project files: ' + (''.join(
                        [f"\n  {_gray}'{project_file[0]}'{_reset}\n   → '{project_file[1]}'"
                         for project_file in project.pack_files()]
                )))
            case 'build':
                # Assemble the included files into a ZIP

                ensure_state('project_configured', project.project)
                ensure_state('files_configured', project.included_files)

                util.log(f'Building project {project.var_get("project/name")} ...')

                # Configure included files
                ensure_state('project_configured', project.project)
                ensure_state('files_configured', project.included_files)

                build_cache = util.cache_get(Path('build'), True)
                core_pack_build_cache = util.cache_get(Path('build', 'pack'), False)

                # Copy files
                for file in project.pack_files():
                    # Get paths
                    directory_tree = core_pack_build_cache / file[1].parent
                    destination = directory_tree / file[1].name

                    # Create directories & copy file
                    directory_tree.mkdir(parents=True, exist_ok=True)
                    copyfile(file[0], destination, follow_symlinks=True)

                # Create ZIP
                zip_file_path = (f'{build_cache}/{project.var_get("project/name")}'
                                 f'-{project.var_get("project/version")}.zip')

                with ZipFile(zip_file_path, 'w') as zip_file:
                    for pack_file in project.pack_files():
                        zip_file.write(core_pack_build_cache / pack_file[1], arcname=str(pack_file[1]))
            case _:
                show_help()
