"""Generates a text file containing all version names in order of release"""

import requests

from sys import exit, stderr
from pathlib import Path
from typing import Any, Callable


VERSION_MANIFEST_URL = 'https://piston-meta.mojang.com/mc/game/version_manifest_v2.json'

def main(output: Path, *,
         error_callback: Callable[[], Any] = lambda: exit(1),
         error_log: Callable[[str], Any] = lambda msg: print(msg, file=stderr)):

    # Attempt to request the version manifest
    version_manifest_request: requests.Response = requests.get(VERSION_MANIFEST_URL)
    if version_manifest_request.status_code != 200:
        error_log(f"Got status code {version_manifest_request.status_code} while requesting '{VERSION_MANIFEST_URL}'")
        error_callback()
        return

    # Extract data from JSON
    with output.open('w') as file:
        for ver in [ver['id'] for ver in version_manifest_request.json()['versions']]:
            file.write(f'{ver}\n')


if __name__ == '__main__':
    from sys import argv


    if len(argv) != 2:
        print('Usage: version_list [output file path]', file=stderr)
        exit(1)
    else:
        main(Path(argv[1]))
