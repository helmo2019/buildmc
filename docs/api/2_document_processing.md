# BuildMC Python API Documentation - API functions documentation
The module `buildmc.api` is hereby referred to as `api`.  
This document details the functions and classes available
for processing text files.

## Document Processing
The API offers two ways of processing and including documents
in the data pack build:

### Substitution Variables and Variable Holders
The syntax for a substitution is `%{variable name}`. Variables are
stored in *Variable Holders*, which can be a number of different
classes:
- `api.Platform` and sub-classes
- `api.Dependency` and sub-classes

The available variables are detailed in the respective
sections about `api.Platform` and `api.Dependency`.

### Getting and setting variables
`api.var` and `api.projectvar` can be used to get values from
Variable Holders or set project variables respectively.

---

Usage: <tt>api.var(*name*, *\*holders*)</tt>

Search for the variable with the given *name*, first
in all the given *holders*, then in the project
variables.

- **name**: The name of the variable
- **holders**: Additional variable holders (see above) to search

---

Usage: <tt>api.project_var(*name*, *value*)</tt>

Set a **project** variable.

- **name**: The name of the variable
- **value**: The value of the variable

### Document objects
Use `api.Document` and `api.Document.Copy` to include text files
at various points, possibly processing them by inserting variables.
Note that the objects themselves do nothing, they still need to be
passed to other functions or as parameters to be used.

---

Usage: <tt>api.Document(*path*, *\*variables*, *origin="input"*, *target="output"*)</tt>

Copies a file from *origin* into *target* and substitutes any variable
placeholders inside of it using the given *VariableHolder*s.

**\*variables**: Zero or more *Variable Holders*
**path**: The path of the file, relative to *origin*.
**origin** and **target**: The origin and destination of the file. Allowed
values are:
- `"input"`: The input directory. Context dependent.
- `"output"`: The output directory. Context dependent.
- `"root"`: The project root.

---

Usage: <tt>api.Document.Copy(*path*, *origin="input"*, *target="output"*)</tt>

Copies a file from *origin* into *target*.

**path**: The path of the file, relative to *origin*.
**origin** and **target**: The origin and destination of the file. Allowed
values are:
- `"input"`: The input directory. Context dependent.
- `"output"`: The output directory. Context dependent.
- `"root"`: The project root.


## Example Use Cases
These functions may be used to:
- Automatically generate different parts of `pack.mcmeta`. For example:
  - A `description` containing the project version
  - The correct pack format for the project's Minecraft version
  - An automatically generated `overlays` section
- Generate different READMEs for different platforms:
  - For example, you may want links to other projects to remain
    on site, such that on modrinth, they link to other modrinth pages,
    and on your Git hosting service, they link to other Git repositories
    on that site