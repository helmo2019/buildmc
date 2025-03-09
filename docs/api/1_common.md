# BuildMC Python API Documentation - Common functions documentation
The `buildmc.api` module is hereby referred to as `api`.  
This document details commonly used functions and classes.

---

Usage: `pack_format(name) -> int`

Get the pack format of a version by name.

**name**: The name of the Minecraft version, e.g. `1.21.4` or `24w13a`

The pack format will
be looked up using the output of the `buildmc.meta_extractor.main`
module.