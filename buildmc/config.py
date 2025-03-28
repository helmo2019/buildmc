"""Shared variables"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import buildmc
import modrinth


@dataclass
class Options:
    buildmc_root: Optional[Path] = None
    script_directory: Optional[Path] = None
    download_bytes_per_second: int = 0
    version_meta_index_url: str = 'https://codeberg.org/helmo2019/buildmc/raw/branch/main/version_meta_data.json'
    modrinth_options: modrinth.Options = field(default_factory=lambda: modrinth.Options(
            error_log=lambda msg: buildmc.util.log(msg, buildmc.util.log_error),
            user_agent=f'{modrinth.Options().user_agent} codeberg.org/helmo2019/buildmc/1.0',
            instance_caching=True
    ))


global_options: Options = Options()
