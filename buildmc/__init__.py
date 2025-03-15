from os import chdir
from os.path import basename
from pathlib import Path
from sys import argv, exit
from typing import Type
from zipfile import ZipFile

from buildmc import _config as cfg, ansi, api, util


_valid_tasks = ('help', 'clean', 'variables', 'files', 'build')
_configure_project_message = 'Configuring project'
_configure_files_message = 'Configuring files'


def main(project_class: Type[api.Project], build_script_file_name: str):
    """
    Start BuildMC for a project

    :param project_class: A class extending buildmc.api.Project
    :param build_script_file_name: File path of the build script, obtained with __file__
    """

    # Set root directory
    cfg.reset()

    cfg.script_directory = Path(build_script_file_name).parent
    cfg.buildmc_root = cfg.script_directory / '.buildmc'
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


    def ensure_state(name: str, function, message):
        if not project_state[name]:
            util.log(message, util.log_heading)
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
        if project.has_failed():
            break

        match command:
            case 'clean':
                # Clean all caches
                util.log('Cleaning caches', util.log_heading)
                util.cache_clean_all()
            case 'variables':
                # Print project variables

                ensure_state('project_configured', project.project, _configure_project_message)

                util.log(f'Project variables:{ansi.reset}' + (''.join(
                        [f"\n  {ansi.gray}'{var_name}'{ansi.reset} = {repr(project.var_get(var_name))}"
                         for var_name in project.var_list()]
                )), util.log_heading)
            case 'files':
                # Print included files

                ensure_state('files_configured', project.included_files, _configure_files_message)

                util.log(f'Project files:{ansi.reset}' + (''.join(
                        [f"\n  {ansi.gray}'{project_file.source}'{ansi.reset}\n   → "
                         f"'{project_file.destination}'"
                         f"{f'{ansi.purple} (processed){ansi.reset}' if project_file.process else ''}"
                         for project_file in project.pack_files()]
                )), util.log_heading)
            case 'build':
                # Assemble the included files into a ZIP

                # Configure included files
                ensure_state('project_configured', project.project, _configure_project_message)
                ensure_state('files_configured', project.included_files, _configure_files_message)

                if not project.has_failed():
                    util.log(f'Building project {project.var_get("project/name")}', util.log_heading)

                    build_cache = util.cache_get(Path('build'), True)
                    core_pack_build_cache = util.cache_get(Path('build', 'pack'), False)

                    # Copy files
                    util.log('Copying & processing included files')

                    for file in project.pack_files():
                        file.copy(core_pack_build_cache, project)

                    if not project.has_failed():
                        # Create ZIP
                        util.log('Assembling ZIP file')

                        zip_file_path = build_cache / (f'{project.var_get("project/name")}'
                                                       f'-{project.var_get("project/version")}.zip')

                        with ZipFile(zip_file_path, 'w') as zip_file:
                            for pack_file in project.pack_files():
                                zip_file.write(core_pack_build_cache / pack_file.destination,
                                               arcname=str(pack_file.destination))
            case _:
                show_help()

    # Show end result
    if project.has_failed():
        print(f'\n{ansi.red}{ansi.bold}[✘]{ansi.not_bold} Project build failed')
        exit(1)
    else:
        print(f'\n{ansi.green}{ansi.bold}[✔]{ansi.not_bold} Project build successful')
