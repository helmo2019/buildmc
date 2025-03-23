# BuildMC - Implementation Documentation

## Modrinth API Wrapper

> Fine I'll do it myself

The `buildmc.modrinth` module provides an object-oriented API
for interaction with the Modrinth API.

**Note:** I am planning to introduce dedicated data classes in the future
that will replace the `dict` values in some classes.

---

### `buildmc.modrinth.Project` class

Represents a project on modrinth.

Constructor:

```python
Project(
        name: str
)
```

`name` is either the project's **id** (e.g. *AANobbMI*) or its
**slug** (e.g. *sodium*).

Attributes:
- `slug: str`: E.g. *sodium*
- `id: str`
- `title: str`
- `project_type: LiteralString['mod','modpack','resourcepack','shader']`
- `versions: list[str]`: List of project version IDs
- `game_versions: list[str]`: List of compatible Minecraft versions
- `loaders: list[str]`
- `downloads: int`
- `followers: int`
- `license: dict[str,str]`
  - `id: str`: SPDX license ID
  - `name: str`: Long license name
  - `url: str`: URL to the license
- `color: int`: RGB color of the project, automatically generated from the project icon
- `description: str`: Short description
- `body: str`: Long form description in Markdown format
- `categories: list[str]`: Primary categories
- `additional_categories: list[str]`: Secondary/additional categories
- `client_side: LiteralString['required','optional','unsupported','unknown']`
- `server_side: LiteralString['required','optional','unsupported','unknown']`
- `status: LiteralString['approved','archived','rejected','draft','unlisted','processing','withheld','scheduled','private','unknown']` 
- `issues_url: Optional[str]`: Issue tracker URL
- `source_url: Optional[str]`: Source code URL
- `wiki_url: Optional[str]`: Wiki URL
- `discord_url: Optional[str]`: Discord invite URL
- `updated: str`: ISO-8601 formatted date of the project's last update
- `donation_urls: list[dict]`
  - `id: str`: Platform ID
  - `platform: str`: Platform name
  - `url: str`
- `requested_status: Optional[LiteralString['approved','archived','unlisted','private','draft']]`: The requested status
  when submitting for review or scheduling the project for release
- `icon_url: str`
- `thread_id: str`: ID of the moderation thread associated with this project
- `monetization_status: LiteralString['monetized','demonitized','force-demonitized']`
- `team: str`: ID of the team / user owning this project
- `moderator_message: dict`
  - `message: str`
  - `body: Optional[str]`: Long form message
- `published: str`: ISO-8601 formatted date of the project's release
- `approved: Optional[str]`: ISO-8601 formatted date of the project's last update
- `queued: Optional[str]`: ISO-8601 formatted date of when the project's status was submitted to moderators for review
- `gallery: list[dict]`
  - `url: str`: Image URL
  - `featured: bool`
  - `title: str`
  - `description: str`
  - `created: str`: ISO-8601 formatted creation date of the gallery image
  - `ordering: int`

Methods:
- `.find_version(mc_version: str) -> Optional[Version]`: Find the latest version compatible with
  the given Minecraft version
- `.iter_versions() -> Iterator[Version]`: Iterate over the project's versions. The created Version
  objects are cached.

---

### `buildmc.modrinth.Version` class

Represents a version of a project.

Constructor:

```python
Version(
        id: str
)
```

Attributes:
- `id: str`
- `project_id: str`
- `author_id: str`
- `date_published: str`: ISO-8601 formatted date of the version's publication
- `downloads: int`
- `name: str`
- `version_number: str`
- `changelog: Optional[str]`: Markdown formatted version changelog
- `files: list[dict]`:
  - `hashes: dict`:
    - `sha512: str`
    - `sha1: str`
  - `url: str`
  - `filename: str`
  - `primary: bool`: **Note:** modrinth allows there to be no file with this set to `True` in the file list.
    In this case, `buildmc.modrinth` sets the `primary` attribute of the first entry in this Versions' file
    list to `True`.
  - `size: int`: File size in bytes
  - `file_type: Optional[LiteralString['required-resource-pack','optional-resource-pack]]`
- `dependencies: list[dict]`:
  - `version_id: Optional[str]`
  - `project_id: Optional[str]`
  - `file_name: Optional[str]`
  - `dependency_type: str`
- `game_versions: list[str]`
- `version_type: LiteralString['release','beta','alpha']`
- `loaders: list[str]`
- `status: list[]`
- `featured: bool`
- `status: LiteralString['listed','archived','draft','unlisted','scheduled','unknown']`
- `requested_status: LiteralString['listed','archived','draft','unlisted']`

Methods:

- `.is_compatible(format: str|int) -> bool`: Checks whether this Version is compatible with
  the given Minecraft version or pack format number
  - If `format` is an `int`, the appropriate Minecraft version name is looked up
    using the `buildmc.meta_extractor` module first
- `.download() -> Optional[pathlib.Path]`: Download the file into a BuildMC cache and return
  the file path, or `None` if there was an error
