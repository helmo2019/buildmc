#!/usr/bin/python3
from os import path
from sys import path as module_path

# Add buildmc to module path. For development purposes only,
# will be removed when I set up proper packaging.
module_path.append(path.realpath(f'{path.dirname(__file__)}/../'))

from buildmc import api, main


class Project(api.Project):

    def project(self):
        self.project_name('TestingProject')
        self.project_version('1.0-DEBUG')
        self.pack_type('data')
        self.pack_format('1.21.4')
        self.var_set('custom_variable', 'Hello World!')


    def release_platforms(self):
        pass


    def included_files(self):
        self.include_files('data/**/*')
        self.include_files('readme.md', process=True, do_glob=False)
        self.include_files('../LICENSE', destination="documents")


    def pack_overlays(self):
        pass


main(Project, __file__)
