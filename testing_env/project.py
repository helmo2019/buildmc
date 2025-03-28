#!/usr/bin/python3
from os import path
from sys import path as module_path

from pathlib import Path


# Add buildmc to module path. For development purposes only,
# will be removed when I set up proper packaging.
module_path.append(path.realpath(f'{path.dirname(__file__)}/../'))

from buildmc import api, main


class Project(api.Project):

    def project(self):
        self.project_name('TestingProject')
        self.project_version('1.0-DEBUG')
        self.pack_type('data')
        self.pack_format('1.21.2', min_inclusive='1.21', max_inclusive='1.21.5')
        self.var_set('custom_variable', 'Hello World!')


    def release_platforms(self):
        pass


    def dependencies(self):
        self.add_dependency(api.dependency.Local(self, 'chickens_lay_anything', False,
                                                 'none',
                                                 Path('/home/moritz/.local/share/PrismLauncher/instances/'
                                                      'main/.minecraft/saves/Datapacks & Creative/datapacks/'
                                                      'chickens_lay_anything')))
        self.add_dependency(api.dependency.URL(self, 'wasd_detection', False, 'none',
                                               'https://github.com/CloudWolfYT/'
                                               'WASD-Detection/archive/refs/heads/main.zip',
                                               root=Path('WASD-Detection-main')))
        self.add_dependency(api.dependency.Git(self, 'villager_stats_item', False, 'none',
                                               'https://codeberg.org/helmo2019/minecraft-villager-stats-item.git'))
        self.add_dependency(api.dependency.Git(self, 'veinminer_datapack', False, 'none',
                                               'https://github.com/MiraculixxT/Veinminer.git',
                                               root='datapacks/base'))
        pass


    def included_files(self):
        self.include_files('data/**/*', glob=True)
        self.include_files('readme.md', process=True, destination='documents')
        self.include_files('../LICENSE', destination='documents')
        self.include_files('pack.mcmeta', process=True)


    def pack_overlays(self):
        pass


main(Project, __file__)
