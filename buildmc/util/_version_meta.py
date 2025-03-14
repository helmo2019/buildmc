"""Version meta querying"""

import os
from pathlib import Path

from . import _cache as c, _misc as m, log_error
from .. import _config as cfg, meta_extractor
from ..util import download


def pack_format_of(version_name: str, format_type: str) -> int | None:
    """
    Look up the pack format for a version

    :param version_name: The name of the version. May be one of the aliases in buildmc.meta_extractor
    :param format_type: 'data' or 'resource'
    :return: The looked up pack format number, or None if the lookup failed
    """

    # Get cache dir
    cache_dir = c.cache_get(Path('meta_extractor'), False)
    version_meta_json = m.require_file(cache_dir / 'version_meta.json', lambda p: p.is_file())
    pack_formats_json = m.require_file(cache_dir / 'pack_formats.json', lambda p: p.is_file())
    real_version_name = meta_extractor.real_version_name(version_name)

    # Check if the version data is in pack_formats.json
    pack_formats_data = m.get_json(pack_formats_json)
    if ((pack_formats_data is None)
            or real_version_name not in pack_formats_data.get('data', { })):
        # Version name is nowhere inside of pack_formats.json
        # -> Update version metadata index
        if not _update_version_meta_index(version_meta_json, version_name):
            return None

        # Version name is now inside of version_meta.json
        # -> Run the Metadata Transformer to update pack_formats.json
        meta_extractor.transformer(['--unwrap', str(version_meta_json), 'version', 'pack_version', str(pack_formats_json)])

    # Extract data from pack_formats.json
    pack_formats_data = m.get_json(pack_formats_json)
    # Check if file exists & is valid JSON
    if pack_formats_data is None:
        # If not, log error and return None
        m.log(f"Unable to query {format_type} pack format for version '{version_name}'"
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


def _update_version_meta_index(file_path: Path, version_name: str) -> bool:
    """
    Try to update the cached version_meta.json file

    :param file_path: The absolute path to the version_meta.json file
    :param version_name: The version name that should be in version_meta.json at the end
    :return: Whether the was successful and version_name may now be looked up in version_meta.json
    """

    json_data = m.get_json(file_path)
    if json_data is None or version_name not in json_data:
        # JSON data is empty / invalid or version name is not inside the file
        # -> Update file
        # Download latest version from Git repo
        with open(file_path, 'wb') as version_meta_file:
            download_success = download(version_meta_file,
                              cfg.version_meta_index_url,
                              rate_limit=cfg.download_bytes_per_second)

        if not (download_success and ((json_data := m.get_json(file_path)) and (version_name in json_data))):
            # Download failed or JSON data invalid or version name still not in JSON
            # -> Locally update version_meta.json

            # If JSON file is invalid, remove it to allow for merging
            if json_data is None:
                os.remove(file_path)

            # Run the Meta Extractor
            real_version_name = meta_extractor.real_version_name(version_name)
            meta_extractor.main({
                "threads": 1,  # We need to download exactly 1 version, so 1 thread.
                "bandwidth": cfg.download_bytes_per_second,  # Bandwidth limit
                "from_version": real_version_name,  # Specify that we want to download exactly one version
                "to_version": real_version_name,  # ↑
                "merge": True,  # Merge with existing JSON
                "output": file_path  # Output file path
            })

    # At this point, we *hopefully* have a usable version_meta.json in our cache directory
    # First, let's check if the JSON is valid
    json_data = m.get_json(file_path)
    if json_data is None:
        m.log('Unable to obtain usable version meta data index', m.log_error)
        return False
    # Now, let's see if the version is (finally) inside the index
    elif version_name not in json_data:
        m.log(
                f"Unable to obtain version meta for '{version_name}'. Is it spelled correctly? Is it listed in "
                f"Mojang's version manifest?", log_error)
        return False
    else:
        # If we've made it here, we can now, *at last*, report that we've updated the version metadata index
        return True
