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
the BuildMC API. Generally, it should contain at least this code:

```python
from buildmc import api, main


class Project(api.Project):

    def project(self):
        self.project_name('Project Name')
        self.project_version('1.0')
        self.pack_type('data')
        self.pack_format('1.21.4')
        self.var_set('custom_variable', 'Hello World!')


    def included_files(self):
        self.include_files('data/**/*', glob=True)
        self.include_files('../LICENSE', destination='documents')
        self.include_files('readme.md', process=True, destination='documents')


    def release_platforms(self):
        pass


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

Here, the project's basic meta is configured. This should - at least - include:

- The project name, set using `self.project_name(str)`
- The project version, set using `self.project_version(str)`
- The pack type, set using `self.pack_type('data')` or `self.pack_type('resource')`
- The pack format, set using either `self.pack_format(int)` or `self.pack_format(str)`
    - If you pass a **version name string**, the appropriate pack format number will be
      looked up using the [Version Meta Extractor](https://codeberg.org/helmo2019/buildmc#version-meta-index)
    - In this case, `self.pack_type(str)` needs to be called first, so the Version Meta Extractor
      can properly find out the format number

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

#### Document Processing

---

Files that are included with `process=True` may include **variable insertions** in the following format:

> %{variable name}

In this example, the value of the variable `"variable name"` will be inserted. As described above,
project variables can be set using `self.var_set(variable_name: str, variable_value: Any)`. Variable
names can **only be strings**, while variable values can be **any type**. Values are **converted to string**
when they're inserted into files.

<br>

### Defining platforms to release on with `release_platforms(self)`

---

