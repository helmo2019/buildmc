## Project build file
from buildmc import api

class Project(api.Project):

    # Put any variables here...
    readme = api.Document.Processed("doc/README.md")
    changelog = api.Document.Processed("doc/CHANGELOG.md")

    def project(self):
        """Set project meta & dependencies here. Invoked at the start of any task."""

        self.project_version = "1.0"
        self.pack_type("data")
        self.pack_format("1.21.4")

        self.variables["some_var"] = "This can be inserted with %{some_var}!"

        self.dependencies["modrinth_library"] = api.Dependency.Modrinth(self, version_id="abcd1234")

        self.dependencies["other_modrinth_lib"] = api.Dependency.Modrinth(self, project_id="1234abcd") # Automatically finds a fitting version
        self.dependencies["direct_lib"] = api.Dependency.URL(self, url="https://somewebsite.com/datapack.zip",
                                                             sha256="your hash here")
        self.dependencies["git_lib"] = api.Dependency.Git(self, url="https://github.com/someone/some_repo",
                                                          root="datapack/", token="token_name",
                                                          checkout="33465980-fa0c-11ef-9e4d-37376f7c2c4b")

    def release_platforms(self):
        """Define platforms to release on. Invoked by the publish task."""

        # Codeberg releases page
        self.platforms["codeberg"] = api.Platform.CodebergReleases(url="https://codeberg.org/username/repo")
        self.platforms["codeberg"].changelog = Project.readme
        self.platforms["codeberg"].variables["download_url"] = f"{self.platforms["codeberg"].project_url()}/releases"

        # Modrinth
        # 'url=...' is also possible, but 'id=' is preferred
        self.platforms["modrinth"] = api.Platform.Modrinth(project_id="1kjsfw82",
                                                           readme=Project.readme,changelog=Project.changelog)
        # Variables can be inserted in processed documents
        self.platforms["modrinth"].variables["download_url"] = f"{self.platforms["modrinth"].project_url()}/versions"

    def included_documents(self):
        """Define documents to include in the build. Invoked by the build task."""

        self.documents["pack.mcmeta"] = api.Document.Processed("pack.mcmeta")
        self.documents["license"] = api.Document.Copy("doc/License.txt")
        self.documents["credits"] = api.Document.Copy("doc/Credits.txt")

    def pack_overlays(self):
        """Define pack overlays for use with the patchtool. Invoked by patchtool."""

        # As opposed to documents and platforms, this uses a helper method
        # to add an overlay as the overlay name is needed in both the api.Overlay
        # object and as the key in the self.overlays dictionary.
        self.overlay_add(api.Overlay("my_overlay", "24w23a", "1.21.3"))

        # Pack formats can be specified directly as integers or as
        # version names. The appropriate number for version names
        # will be looked up using the bundled buildmc.meta_extractor
        # module. In both cases, the (resulting) number will be validated,
        # and an error will be raised if it is unsupported by BuildMC.
        self.overlay_add(api.Overlay("other_overlay", 50, "1.21.4"))

# Call this at the end to actually start the build!
api.main(Project)
