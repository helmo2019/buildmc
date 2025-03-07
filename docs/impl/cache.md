# BuildMC - Implementation Documentation

## Cache Directory

### Introduction

The cache directory is located inside of `buildmc/cache` in the project root. It contains
files and directories for quick access. It may be deleted at any time and will regenrate
itself. While this may sometimes solve issues, it will also result in longer build times.


### Acquiring a cache directory

1. Check if the there is a file `buildmc/cache/<name>`. If there is, delete it.
   - This case should not occur in normal usage. `buildmc/cache/` should only ever
     contain directories. If there is a file, it must have been placed there by the user or
     another application.
2. Make sure the entire directory tree `buildmc/cache/<name>` exists using `os.mkdirs`


### Cleaning a cache directory

(Recursively) remove the directory at `buildmc/cache/<name>`.


### Functions

The following functions inside of `builmc/api/_util.py` facilitate the cache operations
listed above:

- `cache_get(name: str, clean: bool) -> str|None`
  - Returns the **absolute path** of the created cache subdirectory, or `None` if there was an error
  - Calls `cache_clean()` if `clean == True`
- `cache_clean(name: str)`
  - Recursively removes the directory `buildmc/cache/<name>`, if it exists
