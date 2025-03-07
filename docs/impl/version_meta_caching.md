# BuildMC - Implementation Documentation

## Version Meta Data Caching

### Introduction

BuildMC includes the *Version Meta Extractor* tool. While it may be used as a standalone CLI
utility, it is also integrated into BuildMC to allow for convenient conversion from version
names to pack formats. For example, in your `def project(self):` you could write:

```
    self.type("data")
    self.mc_version("1.21.4")
```

BuildMC will automatically look up the data pack format for version 1.21.4.


### Cache Directory

The cache directory, hereafter referred to as `<cache>`, is `buildmc/cache/meta_extractor`.


### Querying

#### Parameters:
 - `<version>`: Version name to query pack format of
 - `<type>`: Either `"data"` or `"resource"`; The type of pack format to look up

#### Implemented in:
 - Module: `buildmc.api._util`
 - `version_meta_get(version_name: str, type: str) -> int|None`

#### Process:

1. Perform a Data Update
   - Try out the following methods, in this order:
     1. Downloading the latest complete `version_meta.json` **from this repository**
     2. Running the Meta Extractor to get the meta for the requested `<version>`
   - For each run:
     1. Run the `buildmc.meta_extractor.transform` module to get the `pack_formats.json`, a JSON
        file for looking up resource and data pack format numbers by version name
     2. If the requested `<version` is not inside of `pack_formats.json`, try the next method
     3. If all methods were tried, log an error message and return `None`
2. Query the data set from `<cache>/pack_formats.json`
   1. If the version name is not a key in the JSON's `data` object, try looking it up in
      the `aliases` object
   2. If it is not in the `aliases`, perform a Data Update
   3. If it is still not in the `data` object nor in the `aliases` object, log an error message and return `None`
   4. Otherwise, return the looked-up pack format number
