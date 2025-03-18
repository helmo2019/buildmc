# BuildMC - Implementation Documentation

## Dependency Index

### Terminology

- **Configured dependency**: A dependency as configured in the build script
  using `api.Project.add_dependency`
- **Index entry**: An object from the `dependencies` array in `index.json`
- **Dependency identity**, **Identity**: Data from an Index entry's `identity` field
- **Index file**, **Index**: `.buildmc/dependencies/index.json`

### Introduction

In order to properly handle dependency version changes and
already acquired dependencies, an **Index file** is maintained.
It stores information about all acquired dependencies and is
used to determine when to (re)acquire dependencies and
when to treat existing files as valid.

It may also be able to identify an already acquired
dependency in case that the dependency's name in
the build script differs from the directory name.

### JSON Structure

```json5
{
    "dependencies": [
        // A single dependency object
        {
            "name": "name of dependency in the build script",
            "identity": {
                "type": "local | url | git (| modrinth ...)",
                // Other fields here are type dependent. See below for more.
            },
            "uuid": "contents of 'dependency_dir/.buildmc_dependency_uuid'"
        }
    ]
}
```

### Dependency Identity

The `identity` stores the parameters the dependencies
was configured with. It is used to find the matching
index entry for a configured dependency.

#### Identity of `api.dependency.Local`

```json
{
    "type": "local",
    "path_absolute": "/absolute/file_path",
    "path_relative": "../../relative/path",
    "file_type": "directory | archive",
    "archive_root": "archive/root" // Optional
}
```

#### Identity of `api.dependency.URL`

```json
{
    "type": "url",
    "url": "https://example.com/file.zip",
    "root": "archive/root", // Optional
    "sha256": "checksum" // Optional
}
```

#### Identity of `api.dependency.Git`

```json
{
    "type": "git",
    "url": "https://github.com/someone/repo.git",
    "root": "datapacks/base", // Optional
    "checkout": "commit sha1" // Optional
}
```

### UUID

BuildMC creates a `.buildmc_dependency_uuid` file at the
root of the acquired files of each dependency. This text
file contains a UUID that is regenerated each time the
index saved.

1. Before dependencies are acquired, BuildMC attempts
   to find the correct previously acquired files
   for each configured dependency. First, it looks
   for an entry with a matching `name` in the index.
   If one is found, the `identity` data is also checked.
   If it matches, the files are now considered to belong
   to the respective configured dependency.
2. In case there are configured dependencies and previously
   acquired files left over, BuildMC will try to find the
   correct files for each dependency using the `identity`
   data. If a **single** valid index entry is found, its
   `name` field as well as the directory name for the
   dependency files is changed to match the name configured
   in the build script.

### Process

This section describes the inner workings of the `dependencies` task.

#### 1. Validating the Index

---

After this first step, there will be as many directories in `.buildmc/dependencies`
as there are index entries, and each index entry will be unambiguously mapped
to a directory.

1. Using the contents of the UUID files, a dictionary is created that
   maps each available UUID to a file in the `.buildmc/dependencies`
2. The correct directory for each index entry is determined using the
   UUID-to-directory dictionary. If a directory's name does not match
   the `name` value in the index, it is renamed.
3. Leftover index entries and directories are deleted

<br>

#### 2. Finding the correct Index entry for each configured dependency

---

After this step, each configured dependency will be unambiguously
mapped to an index entry, and therefore, to a directory.

1. Map by finding the index entry with the matching name and
   then additionally validating by also checking the `identity`.
   Only if both `name` and `identity` match, the index entry
   and the configured dependency will be mapped.
2.
    1. If there are **leftover index entries**: The index entries and the
       respective files are deleted
    2. If there are **leftover configured dependencies**: The dependencies
       are acquired and added to the index
    3. If there are **both** leftover index entries and leftover configured
       dependencies:
        1. Try to map them using the `identity`. If a match is found, the
           index entry's `name` field is corrected and the respective
           directory is renamed.
        2. Any index entries that are still left will be deleted along
           with their respective files
        3. Any configured dependencies that are still left will be
           (re)acquired