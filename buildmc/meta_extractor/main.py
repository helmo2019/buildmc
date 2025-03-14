from argparse import Namespace
from concurrent.futures import ProcessPoolExecutor, as_completed
from json import dump as json_write
from pathlib import Path
from re import fullmatch
from sys import argv

import requests
from math import ceil

from buildmc.util import get_json, log, log_error, log_warn
from . import _config as config
from ._worker import WorkerProcess


def _find_versions():
    """
    Compiles the version list

    :raise IndexError: If the from_version and/or to_version options specify an invalid index in the version list
    :raise ValueError: If the from_version and/or to_version options specify an invalid version name
    """

    # Get the version manifest
    log('Downloading versions manifest...')
    config.version_list = requests.get('https://piston-meta.mojang.com/mc/game/version_manifest_v2.json').json()[
        'versions']
    version_indices: dict[int, str] = { i: config.version_list[i]['id'] for i in range(len(config.version_list)) }


    # Find the indices of the first and last version to process
    def find_index(search: str) -> int:
        if fullmatch(r'-?\d+', search):
            literal_index = int(search)
            if 0 <= literal_index < len(config.version_list):
                return literal_index
            else:
                raise IndexError(literal_index)
        else:
            matching_indices = [version_index for version_index in version_indices.keys() if
                                version_indices[version_index] == search]
            if len(matching_indices) > 0:
                return matching_indices[0]
            else:
                raise ValueError(config.options.from_version)


    first_version_index, last_version_index = find_index(config.options.from_version), find_index(
        config.options.to_version)
    log(
            f'Processions versions #{first_version_index} ({version_indices[first_version_index]}) to #'
            f'{last_version_index} ({version_indices[last_version_index]})')
    config.version_list = config.version_list[
                          min(first_version_index, last_version_index):max(last_version_index, first_version_index) + 1]


def main(args: list[str] | dict | None):
    """Main entry point. """

    # Reset configuration
    config.reset()

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
            config.options = Namespace(**{**config.default_options, **args})

        log(
                f'Running with parameters: {config.options.threads} threads; {config.options.bandwidth}b bandwidth '
                f'limit; {config.options.retries}'
                f' max retries; from {config.options.from_version}; to {config.options.to_version}; merge: '
                f'{config.options.merge}; output: {config.options.output}')

        # Load / create results dictionary
        if config.options.merge:
            if json_data := get_json(Path(config.options.output)):
                config.version_meta = json_data
            else:
                config.version_meta = { }
        else:
            config.version_meta = { }

        # Compile list of to-be-downloaded versions
        try:
            _find_versions()
        except IndexError as index_error:
            log(f'No version with index {index_error.args[0]}', log_error)
            return
        except ValueError as unknown_version_error:
            log(f"No such version: '{unknown_version_error.args[0]}'", log_error)
            return

    except KeyboardInterrupt:
        return

    try:
        # 1. Distribute versions across workers and submit them to the process pool

        # Number of version to process per thread
        per_thread = int(ceil(len(config.version_list) / config.options.threads))

        # Populate a thread pool executor
        bandwidth_per_thread = config.options.bandwidth // config.options.threads
        config.process_pool = ProcessPoolExecutor(config.options.threads)
        for version_range in range(config.options.threads):
            config.worker_threads.append(config.process_pool.submit(WorkerProcess(
                    config.version_list[version_range * per_thread: (version_range + 1) * per_thread],
                    bandwidth_per_thread, config.options.retries).start))

        # 2. Wait for everything to complete
        for future in as_completed(config.worker_threads):
            future.result()

    except KeyboardInterrupt:
        log('Program stopped by KeyboardInterrupt: Stopping threads and saving results...')

    # Store results
    while True:
        try:
            # Yield and store results
            for future in as_completed(config.worker_threads):
                config.version_meta |= future.result()

            # Sort results
            sorted_results = { }
            for key in sorted(config.version_meta):
                sorted_results[key] = config.version_meta[key]

            # Write results
            with open(config.options.output, 'w') as output_json:
                json_write(sorted_results, output_json, indent=4, ensure_ascii=False)  # type: ignore

            break
        except KeyboardInterrupt:
            # KeyboardInterrupt just restarts the collection & storage process >:)
            # (spamming CTRL+C still ends the program eventually as it will at some
            #  point happen while this except block is executing so it won't be caught)
            log('Please wait a moment, the program is just finishing up...', log_warn)
            pass


if __name__ == '__main__':
    main(None)
