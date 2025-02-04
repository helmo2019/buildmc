# BuildMC Python API Documentation - Introduction
The `buildmc.api` module is hereby referred to as `api`.  
This document details the **file structure** of a project as
well as the different **tasks** that are available.

---

The entry point is the `Build` class in the `buildmc.build.py`.
It needs to extend the abstract `api.Project` class. The following
**static** functions need to be implemented:
- `init()`
  - Should call `api.pack_version` and `api.mc_version`
  - Recommended place for setting variables
  - Called when the application starts
- `overlays()`: Section for `api.Overlay` calls
- `platforms()`: Section for `api.Platform` calls
- `docs()`: Section for `api.include` calls

## File structure
```
󰉋 buildmc/
    󰉋 build/
        󰉋 docs/
          -- Processed documents from docs() go here
        󰉋 platform/
            󰉋 <platform name>/
              -- Processed document files for this platform
        󰉋 package/
          -- The final top-level data pack files in a ZIP file
        󰉋 overlays/
          󰉋 <overlay name>/
            -- The final overlay files
    󰉋 overlays/
      󰉋 <overlay name>/
        󰉋 files/
          -- The .patch / additional files
        󰉋 editing/
          -- When editing with 'patchtool edit', the working copy will appear here.
             Otherwise, this directory will not be present.
    󰉋 temp/
      -- Temporary files go here
󰉋 data/
  -- Data pack contents
󰈔 (arbitrary files)
 buildmc.build.py
 buildmc.tokens.toml
```

## Tasks
This section documents the different tasks with
their dependencies (in order). A task always runs all of its
dependencies before running itself.

### build
**This is the default task if none was specified.**  
**Dependencies:** `docs`, `overlay`
Copies the contents `󰉋 buildmc/build/docs/` and `󰉋 buildmc/build/overlays/`
as well as `󰉋 data/` into a temporary directory, compresses them and places
the resulting ZIP file into `󰉋 buildmc/build/package/`.

### clean
**Dependencies:** *none*
Clears previous output inside of `󰉋 buildmc/build/` as well as temporary
files inside of `󰉋 buildmc/temp/`.

### docs
**Dependencies:** *none*
Processes documents from `docs()` and `platforms()` and places them
inside of `󰉋 buildmc/docs/` and `󰉋 buildmc/platform/<platform name>`
respectively.

### overlay [name...]
**Dependencies:** *none*
Assemble the given overlays (default: all) and place the output
into `󰉋 buildmc/overlays/`.

### publish [platform...]
**Dependencies:**: `build`
Uploads the packaged data pack from `󰉋 buildmc/build/package/`
to the given platform(s) (default: all), along with the
respective documents.