import shutil
from os import path
from unittest import TestCase

from buildmc import _config as cfg, api
from buildmc.util import log


class TestProject(api.Project):

    def project(self):
        self.project_version = '1.0-DEBUG'
        self.pack_type('data')
        self.pack_format('1.21.4')


    def release_platforms(self):
        pass


    def included_documents(self):
        pass


    def pack_overlays(self):
        pass


class ProjectTests(TestCase):
    clean_up_before = True
    clean_up_after = False


    @classmethod
    def setUpClass(cls):
        # Call setUp so that cfg.buildmc_root gets set
        cls.setUp()

        if ProjectTests.clean_up_before and path.isdir(cfg.buildmc_root):
            shutil.rmtree(cfg.buildmc_root)

        cls.project: api.Project = TestProject()


    @classmethod
    def tearDownClass(cls):
        if ProjectTests.clean_up_after:
            shutil.rmtree(cfg.buildmc_root)


    @classmethod
    def setUp(cls):
        # Reset config & set root path before each test
        cfg.reset()
        cfg.buildmc_root = path.realpath("./buildmc_debug")


class ProjectConfigTests(ProjectTests):

    @classmethod
    def test__1_project_init(cls):
        cls.project.project()
        cls.project.variables['my_variable'] = 123
        cls.project.variables['project/version'] = 'Using var(), this string should never be visible'


    def test__2_project_special_variables(self):
        project = ProjectConfigTests.project
        project_version = project.var("project/version")
        project_pack_format = project.var("project/pack_format")
        project_pack_type = project.var("project/pack_type")
        my_variable = project.var('my_variable')

        self.assertEqual(project_version, '1.0-DEBUG', 'Project version')
        self.assertEqual(project_pack_format, 61, 'Pack format of 1.21.4')
        self.assertEqual(project_pack_type, 'data', 'Pack type')
        self.assertEqual(my_variable, 123, 'Custom variable')

        log(f'Project version: {project_version}')
        log(f'Project pack format: {project_pack_format}')
        log(f'Project pack_type: {project_pack_type}')
        log(f"Custom variable 'my_variable': {my_variable}")
