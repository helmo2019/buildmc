# BuildMC Documentation

The `buildmc.api` module is hereby referred to as `api`.  
This document details the **file structure** of a project,
the **build script** and command-line usage.

---

## Project Structure

The directory in which the build script is located
is called the **project root** or simply **root**.
BuildMC's working directory is named `.buildmc`
and will be created inside the project root if it
does not already exist. Make sure that the `.buildmc`
directory is listed in your `.gitignore`.

Example structure of a project:

```
.
├── .buildmc/
│   └── -- BuildMC files --
├── data/
│   └── -- data pack contents --
├── pack.mcmeta
├── build.py
└── readme.md
```

## CLI Usage

`<build script>.py [task] [task] [task...]`

For example:

`./build.py variables files`

Available tasks are:

- `help`: Print help and exit
- `clean`: Clean all caches
- `variables`: Print project variables
- `files`: Print out files included in the build
- `build`: Build the project

## Build Script

The build script is simply a regular Python 3 script that uses
the BuildMC API. Here is an example build script:

TODO: Update

```python
from buildmc import api, main


class Project(api.Project):

    def project(self):
        self.project_name('Project Name')
        self.project_version('1.0')
        self.pack_type('data')
        self.pack_format('1.21.4')
        self.var_set('custom_variable', 'Hello World!')

        self.add_dependency('modrinth_library', 'bundle', True,
                            api.Dependency.Modrinth(id='abcd1234', id_type='version'))
        self.add_dependency('other_modrinth_lib', 'bundle', True,
                            api.Dependency.Modrinth(id='1234abcd', id_type='project'))
        self.add_dependency('direct_lib', 'bundle', True,
                            api.Dependency.URL(url='https://somewebsite.com/datapack.zip',
                                               sha256='8150e3c1a479de9134baa13cea4ff78856cca5ebeb9bdfa87ecfce2e47ac9b5b'))
        self.dependency('git_lib', 'bundle', True,
                        api.Dependency.Git(url='https://github.com/someone/some_repo.git',
                                           location='datapack/',
                                           checkout='33465980-fa0c-11ef-9e4d-37376f7c2c4b'))


    def included_files(self):
        self.include_files('data/**/*', glob=True)
        self.include_files('../LICENSE', destination='documents')
        self.include_files('readme.md', process=True, destination='documents')


    def release_platforms(self):
        self.add_platform()


    def pack_overlays(self):
        pass


main(Project, __file__)
```

The script consists of two parts:

1. The **project class**: A class extending `buildmc.api.Project`
2. The **call** to `buildmc.main`, passing the **project class**
   and `__file__` as parameters
    - The `__file__` parameter is required so that BuildMC can
      change its working directory to where your script is located

The project class **has to override** the following methods:

### Project meta: `project(self)`

---

Here, the project's basic meta is configured. This includes:

- The project name, set using `self.project_name(name: str)`
- The project version, set using `self.project_version(name: str)`
- The pack type, set using `self.pack_type('data')` or `self.pack_type('resource')`
- The pack format, set using either `self.pack_format(format: int | str)`
    - If you pass a **version name string**, the appropriate pack format number will be
      looked up using the [Version Meta Extractor](https://codeberg.org/helmo2019/buildmc#version-meta-index)
    - In this case, `self.pack_type(str)` needs to be called first, so the Version Meta Extractor
      can properly find out the format number

<br>

### Dependencies: `dependencies(self)`

---

Dependencies for the project may be defined here using `self.add_dependency()`:

```python
self.add_dependency(
        dependency: api.Dependency
)
```

The `api.Dependency` class is **abstract** and cannot be
instantiated directly. Instead, there are several subclasses
of `api.Dependency`. The available built-in platforms are listed below.
All dependency classes have a set of common constructor
parameters:

- `project: api.Project`: The project itself. Use `self` in your build script
- `name: str`: The dependency's name. This is also the name of the
  directory containing the dependency's files in `.buildmc/dependencies`,
  and the `name` field of the dependency's index entry.
- `version_check: bool`: Whether to perform a version check. If the dependency
  is found to be incompatible with the project, the build fails.
- `deployment: 'bundle' | 'ship' | 'link' | 'none'`: Defines whether the dependency will
  be **merged into** the project at build time (`bundle`),
  **uploaded / copied as an additional file** (`ship`) or
  linked (e.g. by URL) (`link`), or not deployed at all (`none`)

Only the constructor parameters that are not listed above will
be listed in each Dependency subclass's respective section.


<br>

---

#### Local files or ZIP: `api.Dependency.Local`

---

Copies the dependency from another location on the
local machine. The dependency can be either a ZIP
file or a normal directory.

**Parameters:**

- `path: pathlib.Path`: The file path
- `archive_root: Optional[Path]`: Optional. For ZIP files only. Path inside the archive to take files from.

**Examples:**

Copy normal files:

```python
self.add_dependency(api.dependency.Local(
        self, 'other_pack', True, 'bundle',
        Path('~/.minecraft/saves/Other World/datapacks/my_library')))
```

Copy a folder inside a ZIP archive:

```python
self.add_dependency(api.dependency.Local(
        self, 'zip_file', True, 'link',
        Path('~/Documents/minecraft_libraries.zip'),
        archive_root=Path('datapacks/small_library')
))
```

<br>

---

#### File URL: `api.Dependency.URL`

---

Downloads the dependency in the format of a ZIP
file from a URL.

**Parameters:**

- `url: str`: The URL to download from
- `root: Optional[Path]`: Optional. Path inside the downloaded archive to take files from
- `sha256: Optional[str]`: Optional. SHA256 file hash for verification.

**Examples:**

```python
self.add_dependency('my_file', 'bundle', True,
                    api.Platform.URL(url='https://example.com/datapack.zip',
                                     sha256='8150e3c1a479de9134baa13cea4ff78856cca5ebeb9bdfa87ecfce2e47ac9b5b'))
```

<br>

---

#### Modrinth project: `api.Dependency.Modrinth`

---

Downloads the dependency from Modrinth.

**Parameters**:

- `id: str`: Either a **project ID** or a **version ID**
    - If only a project ID is given, BuildMC will look
      for the last project version that is available for
      the project's version
- `type: str`: Either `project` or `version`, referring to the `id` field
- `version_check: bool`: Whether to verify that the dependency is compatible
  with the project

**Examples:**

```python
self.add_dependency('modrinth_library', 'bundle', True,
                    api.Dependency.Modrinth(id='abcd1234', id_type='version'))
```

```python
self.add_dependency('other_modrinth_lib', 'bundle', True,
                    api.Dependency.Modrinth(id='1234abcd', id_type='project'))
```

<br>


---

#### Git repository: `api.Dependency.Git`

---

Downloads the dependency from a Git repository.

**Parameters**:

- `url: str`: URL to the Git repository
- `root: Optional[str]`: Optional. Directory in the Git repository which contains `pack.mcmeta`.
- `checkout: Optional[str]`: Optional. SHA1 of the commit to check out.

**Examples:**



```python
self.add_dependency('git_lib', 'bundle', True,
                    api.Dependency.Git(url='https://github.com/someone/datapack.git'))
```

```python
self.add_dependency('unmaintained_but_works', 'bundle', False,
                    api.Dependency.Git(url='https://github.com/person/datapack.git'))
```

```python
self.add_dependency('functions', 'link', True,
                    api.Dependency.Git(url='https://github.com/group/big_mc_project.git',
                                       location='datapack',
                                       checkout='33465980-fa0c-11ef-9e4d-37376f7c2c4b'))
```

<br>

### Files included in the build: `included_files(self)`

---

In this function, the files included in the project build are defined.

To include a file, use the `self.include_files()` method:

```python
self.include_files(
        pattern: str,
process = False,
destination: Optional[str | Path] = None,
glob = False
)
```

Parameters:

- `pattern`: A file path, relative to the **root directory**
- `process`: Optional. Whether **document processing** should be performed
  on the file
- `destination`: Optional. A **directory** path relative to the built pack's root. If this is given,
  the file(s) is/are placed there.
- `glob`: Whether the `pattern` should be
  [interpreted as a Glob pattern](https://en.wikipedia.org/wiki/Glob_(programming))

<br>

---

#### File Destination

---

If no `destination` is set:

- If the file is inside the **root directory**: The destination is the file path,
  relative to the **root directory**
- Else:
    - A warning is printed to the console
    - The destination is simply the **file name**, so it's placed at top-level in the output
      Else:
- If the file is outside the **root directory**: A warning is printed to the console
- (Regardless of whether the file is outside the **root directory**) A directory with
  the given name (`directory`) will be created at top-level in the output, and the file
  will be copied there

<br>

---

#### Document Processing

---

Files that are included with `process=True` may include **variable insertions** in the following format:

> %{variable name}

In this example, the value of the variable `"variable name"` will be inserted. As described above,
project variables can be set using `self.var_set(variable_name: str, variable_value: Any)`. Variable
names can **only be strings**, while variable values can be **any type**. Values are **converted to string**
when they're inserted into files.

<br>

### Release platforms `release_platforms(self)`

---

Here, you can define the platforms you want your project to
be automatically uploaded to through the `publish:` task.
When `publish:` is called, the project is built first with
the `build` task and the resulting ZIP file is uploaded to
the given platforms.

Adding a platform is done using `self.add_platform()`:

```python
self.add_platform(
        name: str,
platform: api.Platform
)
```

The `name` parameter is used for logging messages.

The `api.Platform` class is **abstract** and cannot be
instantiated directly. Instead, there are several subclasses
of `api.Platform`. The available built-in platforms are listed below.

<br>

---

#### Local deployment: `api.Platform.Local`

---

Copies the ZIP file to a location on the local file machine.
If a file from a previous build exists at the destination,
it is removed.

**Parameters:**

- `path: pathlib.Path`: The directory to copy the ZIP file to

**Examples:**

```python
self.add_platform(api.Platform.Local(Path('~/.minecraft/saves/Development/datapacks')))
```

```python
self.add_platform(api.Platform.Local(Path('~/.minecraft/resourcepacks')))
```

**(Future plans: Modrinth, Codeberg/Forgejo releases, GitHub releases)**
