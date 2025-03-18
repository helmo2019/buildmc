from os import chdir
from os.path import basename
from pathlib import Path
from sys import argv, exit
from typing import Type

from buildmc import _config as cfg, api, util


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
                                                        if task not in api.tasks.task_map]) != 0:
        show_help()

    for command in argv[1:]:
        if project.has_failed():
            break

        if command in api.tasks.task_map:
            api.tasks.task_map[command](project)
        else:
            show_help()

    # Show end result
    if project.has_failed():
        print(f'\n{util.ansi.red}{util.ansi.bold}[✘]{util.ansi.not_bold} Project build failed')
        exit(1)
    else:
        print(f'\n{util.ansi.green}{util.ansi.bold}[✔]{util.ansi.not_bold} Project build successful')
