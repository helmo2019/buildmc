# BuildMC - Roadmap

## Permanent

- [ ] Comprehensive API & implementation documentation
- [ ] Ensure stability
  - [ ] Do not allow local dependencies to source from `.buildmc`
  - [ ] 

## Core Features

1. Setting project metadata
    - [x] Integration with the meta extractor
    - [x] Cache file system
2. Building the pack
    - [x] Including files & assembling ZIP file
    - [x] **Document processing system**
3. Dependency management
    - [ ] Integration with [weld](https://docs.smithed.dev/weld/) for building
      packs with all dependencies included
    - [ ] Support acquiring the files from a variety of sources:
      - [ ] Modrinth
      - [x] Git repositories
      - [x] URLs to ZIP files
      - [x] Local files
    - [ ] Options for dependency bundling (`bundle`, `ship`, `link`, `none`)
4. Publishing of builds
    - [ ] Local
    - [ ] Modrinth
    - [ ] Codeberg Releases (or any other Forgejo instance)
    - [ ] Maybe other Git hosting services that have a *Releases* feature (GitHub, GitLab)
    - [ ] Allow inclusion of a README / other files
5. Smart auto-updating
    - Currently, a dependency is only (re)downloaded if it
      can't be matched to an index entry, meaning if either
      it's parameters are changed or the files are deleted
      by an external application / the user. But what if...
      - The local files are changed (`api.dependency.Local`)?
      - The file pointed to by a URL is changed (`api.dependency.URL`)?
      - There is a new version uploaded to modrinth that would
        be compatible with the project (`api.depndency.Modrinth`)?
      - There were new commits to a Git repository (`api.dependency.Git`)?
    - [ ] Local files: Look for changed files and copy them
    - [ ] URL: Compare size or checksum?
    - [ ] Modrinth: (If no specific version is specified) Store currently
      downloaded file name / ID and query API to see if a newer file
      matching the given criteria was published
    - [ ] Git: (If not specific commit is specified) Keep the Git repo
      in a cache, then fetch & pull

## Side Quests

1. Modrinth API bindings for downloading

   - [ ] Get project info
   - [ ] Search for file to download using
     only the project's Minecraft version
     & pack type

2. Modrinth API bindings for uploading

   - [ ] Push version to project
       - [ ] Generate title & version number(s) from project meta
       - [ ] Attach README / description

## Extra Features

1. *(Not sure)* Patch tool
    - Utility for (hopefully) easier handling of
      pack overlays
    - [ ] Definitions of overlays in the build script
        - [ ] Set target pack formats & name
    - [ ] Auto-generation of the `overlays` section in pack.mcmeta
    - Workflow for creating:
        1. Open an editing copy of any data pack file
           (including files from **bundled** dependencies!)
            - For language servers (SpyglassMC) it may be
              better to just copy the entire data pack
            - If a patch exist already, apply it for editing
            - Add option to open unpatched file for editing
            - **Handle patch errors appropriately**
        2. Compute the `diff`s of the original files and
           the editing copies
        3. Store the diffs in the `buildmc_overlays` directory
    - Workflow for building:
        1. Copy the file trees with the to-be-patched files
        2. Apply the patches
        3. Copy the patched file trees to the appropriately named
           overlay directories in the build directory
2. Daemon process
    - [ ] Start CLI with `daemon` action
    - [ ] Communicate via a `buildmc.sock` UNIX socket file
        - Simply pass lines with CLI options to be executed
    - Better performance, hopefully
