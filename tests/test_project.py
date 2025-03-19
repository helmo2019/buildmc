import shutil
from os import path
from pathlib import Path
from unittest import TestCase

from buildmc import config as cfg, api, util


class TestProject(api.Project):

    def project(self):
        self.project_version('1.0-DEBUG')
        self.pack_type('data')
        self.pack_format('1.21.4')


    def dependencies(self):
        pass


    def release_platforms(self):
        pass


    def included_files(self):
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
        cfg.buildmc_root = Path("./buildmc_debug").resolve()
        cfg.script_directory = Path(__file__).parent.resolve()


class ProjectConfigTests(ProjectTests):

    def test__1_project_init(self):
        project = ProjectConfigTests.project

        project.project()
        project.var_set('my_variable', 123)
        project.var_set('project/version', 'Using var(), this string should never be visible')
        project.var_set(123, 'This value should not get set!')
        self.assertIsNone(project.var_get(123))


    def test__2_project_special_variables(self):
        project = ProjectConfigTests.project
        project_version = project.var_get("project/version")
        project_pack_format = project.var_get("project/pack_format")
        project_pack_type = project.var_get("project/pack_type")
        my_variable = project.var_get('my_variable')

        self.assertEqual(project_version, '1.0-DEBUG', 'Project version')
        self.assertEqual(project_pack_format, 61, 'Pack format of 1.21.4')
        self.assertEqual(project_pack_type, 'data', 'Pack type')
        self.assertEqual(my_variable, 123, 'Custom variable')

        util.log(f'Project version: {project_version}')
        util.log(f'Project pack format: {project_pack_format}')
        util.log(f'Project pack_type: {project_pack_type}')
        util.log(f"Custom variable 'my_variable': {my_variable}")


class DependencyIdentityTests(ProjectTests):

    def test__local(self):
        example_datapack = ('/home/moritz/.local/share/PrismLauncher/instances/main/.minecraft/'
                                        'saves/Datapacks & Creative/datapacks/chickens_lay_anything')

        dep = api.dependency.Local(DependencyIdentityTests.project, 'file_dependency', False, 'none',
                                   Path(example_datapack))
        dep_identity = dep.identity()

        identity_1 = {
            'type': 'local',
            'path_absolute': '/some/nonexistent/path',
            'path_relative': '../../../',
            'file_type': 'directory'
        }

        identity_2 = {
            'type': 'local',
            'path_absolute': '/some/nonexistent/path',
            'path_relative': dep_identity['path_relative'],
            'file_type': 'directory'
        }

        self.assertFalse(dep.matches_identity(identity_1))
        self.assertTrue(dep.matches_identity(identity_2))
