"""Version meta querying"""

from os import path

import os


from .. import meta_extractor
from .._util import download
from .. import _config as cfg
from . import _cache as c
from . import _logging as l
from . import _misc as m

__min_pack_format = 4

def pack_format_of(version_name: str, format_type: str) -> int | None:
    # Get cache dir
    cache_dir = c.cache_get('meta_extractor', False)
    version_meta_json = m.require_file(f'{cache_dir}/version_meta.json', path.isfile)
    pack_formats_json = m.require_file(f'{cache_dir}/pack_formats.json', path.isfile)
    real_version_name = meta_extractor.real_version_name(version_name)

    # Check if the version data is in pack_formats.json
    pack_formats_data = m.get_json(pack_formats_json)
    if ((pack_formats_data is None)
            or real_version_name not in pack_formats_data.get('data', {})):
        # Version name is nowhere inside of pack_formats.json
        # -> Update version metadata index
        if not _update_version_meta_index(version_meta_json, version_name):
            return None

        # Version name is now inside of version_meta.json
        # -> Run the Metadata Transformer to update pack_formats.json
        meta_extractor.transformer(['--unwrap', version_meta_json, 'version', 'pack_format', pack_formats_json])

    # Extract data from pack_formats.json
    pack_formats_data = m.get_json(pack_formats_json)
    # Check if file exists & is valid JSON
    if pack_formats_data is None:
        # If not, log error and return None
        l.log(f"Unable to query {format_type} pack format for version '{version_name}'"
              f"from '{pack_formats_json}', l.log_error)")
        return None
    else:
        # Otherwise, extract the data

        # Get the version meta, which is either a single int or a dict {"resource": ..., "data": ...}
        version_meta = pack_formats_data['data'][real_version_name]

        # Extract correct value
        if isinstance(version_meta, dict):
            return version_meta[format_type]
        else:
            return version_meta


def _update_version_meta_index(file_path: str, version_name: str) -> bool:
    json_data = m.get_json(file_path)
    if json_data is None or version_name not in json_data:
        # JSON data is empty / invalid or version name is not inside the file
        # -> Update file
        # Download latest version from Git repo
        with open(file_path, 'w') as version_meta_file:
            if not ((download(version_meta_file, 'https://codeberg.org/helmo2019/buildmc/raw/branch/main/version_meta_data.json',
                     rate_limit=cfg.download_bytes_per_second)) and (json_data := m.get_json(file_path) and (version_name in json_data))):
                # Download failed or JSON data invalid or version name still not in JSON
                # -> Locally update version_meta.json

                # If JSON file is invalid, remove it to allow for merging
                if json_data is None:
                    os.remove(file_path)

                # Run the Meta Extractor
                real_version_name = meta_extractor.real_version_name(version_name)
                meta_extractor.main([
                    '-T','1',   # Threads. We need to download exactly 1 version, so 1 thread.
                    '-b',str(cfg.download_bytes_per_second),    # Bandwidth limit
                    '-f',real_version_name, # Specify that we want to download exactly one version
                    '-t',real_version_name, # -''-
                    '-m',   # Merge with existing JSON
                    '-o',file_path  # Output file path
                ]) # TODO make sure that meta_extractor.main does not call exit() at any point!!

    # At this point, we *hopefully* have a usable version_meta.json in our cache directory
    # First, let's check if the JSON is valid
    json_data = m.get_json(file_path)
    if json_data is None:
        l.log('Unable to obtain usable version meta data index', l.log_error)
        return False
    # Now, let's see if the version is (finally) inside the index
    elif version_name not in json_data:
        l.log(f"Unable to obtain version meta for '{version_name}'. Is it spelled correctly? Is it listed in Mojang's version manifest?")
        return False
    else:
        # If we've made it here, we can now, *at last*, report that we've updated the version metadata index
        return True
