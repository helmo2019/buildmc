"""Shared variables"""

from typing import Optional

buildmc_root: Optional[str] = None
script_path: Optional[str] = None
download_bytes_per_second: int = 0
version_meta_index_url: str = ''

def reset():
    global buildmc_root, download_bytes_per_second, version_meta_index_url

    buildmc_root = None
    download_bytes_per_second = 1024 * 1024 * 8 # 8 MiB
    version_meta_index_url = 'https://codeberg.org/helmo2019/buildmc/raw/branch/main/version_meta_data.json'

reset()
