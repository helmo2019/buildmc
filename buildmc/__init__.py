from os import path, chdir, makedirs
from shutil import copyfile
from sys import argv
from typing import Type
from zipfile import ZipFile

from buildmc import api, util, _config as cfg

def main(project_class: Type[api.Project]):
    """
    Start BuildMC for a project

    :param project_class: A class extending buildmc.api.Project
    """

    # Set root directory
    cfg.reset()
    script_dir = path.dirname(path.realpath(argv[0]))
    chdir(script_dir)
    cfg.buildmc_root = f'{script_dir}/buildmc_root'

    # Configure project
    project = project_class()
    project.project()

    # Execute commands
    for command in argv[1:]:
        match command:
            case 'clean':
                util.cache_clean_all()
            case 'variables':
                util.log('Project variables:'+(''.join(
                        [f"\n  \033[38;2;140;140;140m'{var_name}'\033[0m: {repr(project.var_get(var_name))}"
                         for var_name in project.var_list()]
                )))
            case 'build':
                util.log(f'Building project {project.var_get("project/name")} ...')

                # Configure included files
                project.included_files()

                build_cache = util.cache_get('build', True)
                core_pack_build_cache = util.cache_get('build/pack', False)

                # Copy files
                for file in project.pack_files():
                    # Get paths
                    directory_tree = f'{core_pack_build_cache}/{path.dirname(file)}'
                    destination = f'{directory_tree}/{path.basename(file)}'

                    # Create directories & copy file
                    makedirs(directory_tree, exist_ok=True)
                    copyfile(path.realpath(file), destination, follow_symlinks=True)

                # Create ZIP
                zip_file_path = (f'{build_cache}/{project.var_get("project/name")}'
                                 f'-{project.var_get("project/version")}.zip')

                with ZipFile(zip_file_path, 'w') as zip_file:
                    for pack_file in project.pack_files():
                        zip_file.write(f'{core_pack_build_cache}/{pack_file}', arcname=pack_file)
