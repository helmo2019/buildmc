# BuildMC - Python build tool API for Minecraft Data Packs

## Planned features

- Dependency management
  - Download from modrinth
  - Download from custom location (e.g. GitHub releases)
- Building / packaging the project
  - Pre-processor for markdown documents (e.g. README.md): different links depending on the platform
    - E.g. links to modrinth pages on the README for modrinth, but links to codeberg pages
      on the README for codeberg
    - Also for changelogs
    - Define variables in the platform's build configuration that can then be inserted
      using `%{variable_name}`
  - Publish releases on modrinth and codeberg using the respective APIs
- Patchtool
- API tokens: either passed using `--modrinth-api TOKEN` and `--codeberg-api TOKEN`, or stored
  in the tokens file specified using `--tokens` (default: `buildmc.tokens.toml`)
  - E.g.
    ```
    modrinth-api = 'TOKEN'
    codeberg-api = 'TOKEN'
    ```
  - TODO: Figure out how to securely store tokens / secrets like this on disk or in memory

## The buildmc.build.py file
BuildMC provides a Python API that can be used to configure the tool. The configuration
file / build script is called `buildmc.build.py` and should be placed at the root of the data
pack folder (at the same level as `pack.mcmeta`). It is structured as follows:

```
# Import the API module
from buildmc import api

# The abstract 'Project' class defines a set of static, abstract functions
# that configure a project
class Build(api.Project):

    @staticmethod
    def init():
        api.pack_version("1.0")
        api.mc_version(api.MinecraftVersion("1.21.4"))
        
        api.Dependency.Modrinth(version_id="abcd1234")
        api.Dependency.Modrinth(project_id="1234abcd") # Automatically find a fitting version
        api.Dependency.File(url="https://somewebsite.com/datapack.zip", sha256="your hash here")
        api.Dependency.Git(url="https://github.com/someone/some_repo", root="datapack/", token="token_name")
    
    @staticmethod
    def overlays():
      # The overlays are applied in the order they're configured in here!
      api.Overlay("my_overlay", api.MinecraftVersion("24w23a"), to=api.MinecraftVersion("1.21.3"))
      other_overlay = api.Overlay("other_overlay", api.MinecraftVersion("1.20.3))
      other_overlay.process(api.Document("data/my_namespace/"))  # ??? what was my idea here...
    
    @staticmethod
    def platforms():
      codeberg = api.Platform.Codeberg("codeberg", "https://codeberg.org/username/repo")
      codeberg.include_changelog(api.Document("CHANGELOG.md", api.variables_get(codeberg))
      
      # 'url=...' is also possible, but 'id=' is preferred
      modrinth = api.Platform.Modrinth("modrinth", project_id="1kjsfw82",
        include_readme=api.Document("README.md", api.variables(modrinth)),
        include_changelog=api.Document("CHANGELOG.md", api.variables(modrinth))
      )
    
    @staticmethod
    def docs():
      # Remember to auto-generate the overlays part in your
      # pack.mcmeta using '%{overlays}'
      api.include(api.Document("pack.mcmeta"))
      
      # Use api.Document.Copy("path", origin="root") to copy
      # a file without any processing
      api.include(api.Document.Copy("LICENSE"))
```

## CLI usage
> <tt>buildmc [options...] tasks...</tt>

### Options
- `--root, -r [config file]`: specify the `buildmc.build.py` to use

### Tasks
- `clean`: clear previous output in `buildmc/`
- `docs`: pre-process documents
- `overlay [name...]`: generate the given / all overlay(s)
- `build`: run `docs`; package data pack files
- `publish [platform...]`: publish to all configured platforms or the ones given
- `patchtool ...`: see below
- `variables`: print available variables for substitution in files

### Patchtool - CLI tool for generating pack overlays
Usage: `buildmc patchtool <target overlay> <operation> [files...]`

#### Concept
- Overlays are configured in `buildmc.build.py`. They have the following properties:
  - Target version(s): A version or a range of versions that need the overlay
  - Name: Used in the `patchtool` subcommand. This is also the name of the
    overlay folder in the packaged data pack
- The changes to the individual data pack files are stored as `.patch` files
- For editing, the entire data pack or the given files are copied to a working
  directory and the patch files are applied
  - When exiting editing mode:
    - Update diff files for changed files
      - `inotify` time?
    - Files which do not exist in the base pack are simply copied
- When running the `overlay` task:
  - Patch files: copy over the file from the base pack and patch it
  - Files unique to the overlay: just copy them over

#### Usage
- Target overlay: An overlay configured in `buildmc.build.py`
- Operations:
  - `edit`: Enter editing mode, as described above
  - `restore`: Delete the patch files for the given files
  - `apply`: Exit editing mode, as described above
  - `discard`: If an editing session is open, delete it
