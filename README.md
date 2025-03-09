# BuildMC - Python Build API for Minecraft Data and Resource Packs

## 🚧 Under Construction 🚧

This project is still mostly in **planning stage**. Even the name is
not final, right now it sounds generic and also far too similar to
[MC-Build](https://mcbuild.dev/). But for a rough idea of my vision for
the tool, see the [example build script](testing_env/project.py)
and the [result of a recent brainstorming session](docs/concept.py).

The project's progress is documented on the [roadmap](docs/roadmap.md).

The results of my very first brainstorming session are [here](docs/overview.md).

## Version Meta Index

Ever since snapshot **18w47b**, the `client.jar` (and `server.jar`) of
each Minecraft version has included a `version.json` which contains
information such as the data and resource pack format number and world
format.

I've written a [tool](buildmc/meta_extractor) I call the **Meta Extractor**
which extracts the  contents of `version.json` from all the `client.jar`
files which contain it and compiles the results in a 
[single file](version_meta_data.json).

Additionally, I've written [another script](buildmc/meta_extractor/transform.py)
which can transform the output of the Meta Extractor. For example, it can
generate a JSON file in which you can directly look up the [data and/or resource
pack format number for any version](pack_versions.json), e.g.:

```
{
    "data": {
        "1.14": 4,
        ...
        "1.21.4": {
            "resource": 46,
            "data": 61
        },
        ...
    }
}
```

And all of that just so I can do `pack_format('1.21.4')` instead of `pack_format(61)`
in my build script! You could say I procrastinated. But maybe, someone will find this
data useful, I don't know...
