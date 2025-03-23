"""Version meta querying"""
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

from . import _cache as c, _download as d, _misc as m, log_error
from .. import config as cfg, meta_extractor


@dataclass
class Version:
    pack_type: Literal['data', 'resource']
    version_name: str
    format_number: int


    def __str__(self):
        return f"{self.version_name} ({self.pack_type} pack format {self.format_number})"


def pack_formats_of(version_names: list[str], format_type: str) -> Optional[list[int]]:
    """
    Look up the pack format for a list of versions

    :param version_names: The names of the versions. May be one of the aliases in buildmc.meta_extractor
    :param format_type: 'data' or 'resource'
    :return: The looked up pack format number, or None if the lookup failed
    """

    # Get cache dir
    cache_dir = c.cache_get(Path('meta_extractor'), False)
    version_meta_json = m.require_file(cache_dir / 'version_meta.json', lambda p: p.is_file())
    pack_formats_json = m.require_file(cache_dir / 'pack_formats.json', lambda p: p.is_file())
    real_version_names = list(map(meta_extractor.real_version_name, version_names))

    # Check if the version data sets are in pack_formats.json
    pack_formats_data = m.get_json(pack_formats_json)
    if (
            (pack_formats_data is None)
            or m.any_match(real_version_names, lambda name: name not in pack_formats_data.get('data', { }))
    ):
        # Version name is nowhere inside of pack_formats.json
        # -> Update version metadata index
        if not _update_version_meta_index(version_meta_json, real_version_names):
            return None

        # Version name is now inside of version_meta.json
        # -> Run the Metadata Transformer to update pack_formats.json
        meta_extractor.transformer(
                ['--unwrap', str(version_meta_json), 'version', 'pack_version', str(pack_formats_json)])

    # Extract data from pack_formats.json
    pack_formats_data = m.get_json(pack_formats_json)
    # Check if file exists & is valid JSON
    if pack_formats_data is None:
        # If not, log error and return None
        m.log(f"Unable to query {format_type} pack format for versions '{version_names}'"
              f"from '{pack_formats_json}', l.log_error)")
        return None
    else:
        # Otherwise, extract the data

        # Get the version meta, which is either a single int or a dict {"resource": ..., "data": ...}
        result = []
        for real_name in real_version_names:
            version_meta = pack_formats_data['data'][real_name]
            # Extract correct value
            if isinstance(version_meta, dict):
                result.append(version_meta[format_type])
            else:
                return result.append(version_meta)

        return result


def _update_version_meta_index(file_path: Path, real_version_names: list[str]) -> bool:
    """
    Try to update the cached version_meta.json file

    :param file_path: The absolute path to the version_meta.json file
    :param real_version_names: The real version names that should be in version_meta.json at the end
    :return: Whether the was successful and all version_names may now be looked up in version_meta.json
    """

    json_data = m.get_json(file_path)
    if json_data is None or m.any_match(real_version_names, lambda name: name not in json_data):
        # JSON data is empty / invalid or version name is not inside the file
        # -> Update file
        # Download latest version from Git repo
        with open(file_path, 'wb') as version_meta_file:
            download_success = d.download(version_meta_file,
                                          cfg.global_options.version_meta_index_url,
                                          rate_limit=cfg.global_options.download_bytes_per_second)

        if not (
                download_success
                and (json_data := m.get_json(file_path))
                and m.all_match(real_version_names, lambda name: name in json_data)
        ):
            # Download failed or JSON data invalid or version names still not all in JSON
            # -> Locally update version_meta.json

            # If JSON file is invalid, remove it to allow for merging
            if json_data is None:
                os.remove(file_path)

            # Run the Meta Extractor
            # TODO Make version range selection more flexible
            for real_name in real_version_names:
                meta_extractor.main({
                    "threads": 1,  # We need to download exactly 1 version, so 1 thread.
                    "bandwidth": cfg.global_options.download_bytes_per_second,  # Bandwidth limit
                    "from_version": real_name,  # Specify that we want to download exactly one version
                    "to_version": real_name,  # ↑
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
    elif not m.all_match(real_version_names, lambda name: name in json_data):
        m.log(
                f"Unable to obtain version meta for '{real_version_names}'. Are they spelled correctly? Are they"
                " listed in Mojang's version manifest?", log_error)
        return False
    else:
        # If we've made it here, we can now, *at last*, report that we've updated the version metadata index
        return True
