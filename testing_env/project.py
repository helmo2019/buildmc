#!/usr/bin/python3
from sys import path


path.append('../buildmc')

from buildmc import api, main


class Project(api.Project):

    def project(self):
        self.project_name('TestingProject')
        self.project_version('1.0-DEBUG')
        self.pack_type('data')
        self.pack_format('1.21.4')
        self.var_set('custom_variable', 'Hello World!')

        self.include_files('data/**')


    def release_platforms(self):
        pass


    def included_documents(self):
        pass


    def pack_overlays(self):
        pass


main(Project)
