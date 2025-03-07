# BuildMC - Roadmap
## Core Features
1. Setting project metadata
    - Integration with the meta extractor
    - Cache file system
2. Building the pack
   - **Document processing system**
3. Dependency management
   - Integration with [weld](https://docs.smithed.dev/weld/) for building
     packs with all dependencies included
   - Support downloading from **modrinth**, **Git repositories**,
     or raw **URLs to ZIP files**
   - Option for whether the dependency should be bundled or not
4. Publishing of builds
   - Modrinth
   - Codeberg Releases (or any other Forgejo instance)
   - Maybe other Git hosting services that have a *Releases* feature (GitHub, GitLab)
   - Allow inclusion of a README / other files

## Extra Features
5. *(Not sure)* Patch tool
   - Utility for (hopefully) easier handling of
     pack overlays
   - Definitions of overlays in the build script
     - Set target pack formats & name
   - Auto-generation of the `overlays` section in pack.mcmeta
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
6. Daemon process
   - Start CLI with `daemon` action
   - Communicate via a `buildmc.sock` UNIX socket file
     - Simply pass lines with CLI options to be executed
   - Better performance, hopefully
