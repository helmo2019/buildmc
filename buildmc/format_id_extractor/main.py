from argparse import Namespace
from concurrent.futures import ProcessPoolExecutor, as_completed
from json import load as json_load, dump as json_write
from math import ceil
from os.path import isfile
from re import fullmatch
from sys import argv

import requests

from . import _config as config
from ._worker import WorkerProcess

# TODO implement new output format, fix crash when CTRL+C is pressed (issue with SHA1 of 1.13-pre8? it never seems to finish.)

def _find_versions():
    """Compiles the version list"""

    # Get the version manifest
    print('Downloading versions manifest...')
    config.version_list = requests.get('https://piston-meta.mojang.com/mc/game/version_manifest_v2.json').json()['versions']
    version_indices: dict[int, str] = {i: config.version_list[i]['id'] for i in range(len(config.version_list))}

    # Find the indices of the first and last version to process
    def find_index(search: str) -> int:
        if fullmatch(r'\d+', search):
            literal_index = int(search)
            if 0 <= literal_index < len(config.version_list):
                return literal_index
            else:
                raise IndexError(f'No version with index {literal_index}')
        else:
            matching_indices = [version_index for version_index in version_indices.keys() if
                                version_indices[version_index] == search]
            if len(matching_indices) > 0:
                return matching_indices[0]
            else:
                raise ValueError(f'No such version: {config.options.from_version}')

    first_version_index, last_version_index = find_index(config.options.from_version), find_index(config.options.to_version)
    print(
        f'Processions versions #{first_version_index} ({version_indices[first_version_index]}) to #{last_version_index} ({version_indices[last_version_index]})')
    version_list = config.version_list[min(first_version_index,last_version_index):max(last_version_index, first_version_index)+1]
    print(f'new list size: {len(version_list)}')


def _setup_workers():
    """Distributes versions across workers and submits them to the process pool"""

    # Number of version to process per thread
    per_thread = int(ceil(len(config.version_list) / config.options.threads))

    # Populate a thread pool executor
    bandwidth_per_thread = config.options.bandwidth // config.options.threads
    config.process_pool = ProcessPoolExecutor(config.options.threads)
    for version_range in range(config.options.threads):
        config.worker_threads.append(config.process_pool.submit(WorkerProcess(
            config.version_list[version_range * per_thread: (version_range + 1) * per_thread],
            bandwidth_per_thread, config.options.retries).start))

def main(args: list[str] | dict | None):
    """Main entry point. """

    # Default to sys.argv. Can't use default
    # parameter syntax because sys.argv is mutable.
    if args is None:
        args = argv[1:]

    # Attempt configuration / initialization
    try:
        if isinstance(args, list):
            # Parse args
            config.parser.parse_args(args=args, namespace=config.options)
        else:
            # Turn dictionary into namespace
            config.options = Namespace(**args)

        print(
            f'Running with parameters: {config.options.threads} threads; {config.options.bandwidth}b bandwidth limit; {config.options.retries}'
            f' max retries; from {config.options.from_version}; to {config.options.to_version}; merge: {config.options.merge}; output: {config.options.output}')

        # Load / create results dictionary
        if config.options.merge:
            if isfile(config.options.output):
                with open(config.options.output, 'r') as output_file:
                    # Load JSON, converting the keys from strings to integers
                    pack_formats = {int(key): value for key, value in json_load(output_file).items()}

                    for processed_versions in pack_formats.values():
                        config.already_processed.extend(processed_versions)
            else:
                config.pack_formats = {}
        else:
            config.pack_formats = {}

        _find_versions()
    except KeyboardInterrupt:
        exit(0)

    # Wait until everything is done
    try:
        # Submit all workers
        _setup_workers()

        # Wait for everything to complete
        for future in as_completed(config.worker_threads):
            future.result()

    except KeyboardInterrupt:
        print('Program stopped by KeyboardInterrupt: Stopping threads and saving results...')

    # Store results
    while True:
        try:
            # Yield and store results
            for future in as_completed(config.worker_threads):
                result = future.result()
                for pack_format in result:
                    # No list mapped yet; We can just use the one from the result
                    if not pack_format in config.pack_formats:
                        config.pack_formats[pack_format] = result[pack_format]
                    # Extend a previously mapped list
                    else:
                        config.pack_formats[pack_format].extend(result[pack_format])

            # Sort results
            sorted_results = {}
            for key in sorted(config.pack_formats):
                sorted_results[key] = config.pack_formats[key]

            # Write results
            with open(config.options.output, 'w') as output_json:
                json_write(sorted_results, output_json, indent=4, ensure_ascii=False) # type: ignore

            break
        except KeyboardInterrupt:
            # KeyboardInterrupt just restarts the collection & storage process >:)
            # (spamming CTRL+C still ends the program eventually as it will at some
            #  point happen while this except block is executing so it won't be caught)
            print('Please wait a moment, the program is just finishing up...')
            pass


if __name__ == '__main__':
    main(None)
