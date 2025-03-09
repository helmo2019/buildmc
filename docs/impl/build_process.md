# BuildMC - Implementation Documentation

## Build Process

### File Structure

In the directory that the build script is in, there are:

- The `assets` / `data` directory of the Data / Resource Pack
    - <u>Idea</u>: Have **both** the resource- and the data pack in the
      same directory
    - Add a `Local` platform that copies the packaged pack(s) into
      a local directory
    - This way, you could develop both your data- and resource packs
      in your development directory and deploy into your `datapacks` and
      `resourcepacks` directories
    - Maybe have two `buildmc.api.Project`s in your build script?
- Any other files
- The cache: `buildmc_root/cache`, hereafter referred to as `<cache>`

### File Selection

- `buildmc.api.Project.include_files(path: str)`
    - Includes a file tree in the file list of the core pack
- `buildmc.api.Project.exclude_files(path: str)`
    - Inverse of `include_files`
    - May be useful if you have included a large file tree with `include_files`
      but need to add some small exceptions
- `buildmc.api.Project.include_document(document: buildmc.api.Document)`
    - Includes a document in the file list of the core pack
    - For example, you could process `pack.mcmeta` this way, or insert
      your project version in a function that displays a welcome message
      to the player
- `buildmc.api.Project.bundle_dependency(dependency: buildmc.api.Dependency)`
    - Uses the [weld](https://docs.smithed.dev/weld/) tool to merge the
      dependencies with the main project
    - **Please ensure that the licence of your dependency permits this!**
- `buildmc.api.Project.ship_dependency(dependency: buildmc.api.Dependency)`
    - Deploys (copies) the dependency as an additional file on the publishing platform
    - The file itself will be directly linked on the release platform
- `buildmc.api.Project.link_dependency(dependency: buildmc.api.Dependency)`
    - Links a dependency as an additional file (e.g. as an *External Asset* on codeberg)
    - For example, on modrinth, the dependency will be linked by using the project's/version's slug

### Process

1. **Core pack**
    - Copy all files that were added using `include_files` to `<cache>/build/pack`
    - Also process any documents that were added using `include_document`
2. **Bundled Dependencies**
    - Use *weld* to merge all dependencies that were marked as *bundled* with
      `bundle_dependency` into the core pack at `<cache>/build/pack`
3. **Packing**
    - Pack the contents of `<cache>/build/pack` into a ZIP file
    - The ZIP file will be placed at `<cache>/build`
    - It is named `<project_name>-<project_version>-merged.zip`
4. **Shipped dependencies**
    - Compress all dependencies that were marked as *shipped* with
      `ship_dependency` to ZIP files
    - They're placed at `<cache>/build` and are (in most cases) named
      `<cache>/<dependency-name>-<dependency-version>-shipping.zip`
        - Depending on the dependency type, the file name may be different

Linked dependencies and the created ZIP files are handled when
publishing to platforms.
