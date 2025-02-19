#!/usr/bin/python3
# Script for generating a table of pack format numbers.
# Works by downloading the client.jar for each version
# since 17w43a (or server.jar since 18w47b) and extracting
# the data pack format from the 'version.json' file inside
# the .jar

import requests
from tempfile import TemporaryFile
from re import fullmatch, match
from requests import HTTPError
from sys import stderr
from zipfile import ZipFile
from json import load as json_load, dump as json_write
from math import ceil
from concurrent.futures import ProcessPoolExecutor, Future, as_completed
from hashlib import sha1
from argparse import ArgumentParser, Namespace
from os.path import isfile
from time import time_ns, sleep

class WorkerProcess:
    def __init__(self, versions: list, retries: int, bytes_per_second: int):
        # Where we'll store the results
        self.results: dict[int, list[str]] = {}

        if len(version_list) > 0:
            # The first item in the list should be the newest
            # and the last item the oldest version
            self.versions: list = versions

            # If the oldest version already has version.json in the server.jar,
            # we can already set this to True and don't need to check for every
            # version
            self.use_server_jar = WorkerProcess.should_use_server_jar(versions[-1]['id'])

            # Limits how many bytes can be downloaded in a single second
            self.bytes_per_second: int = bytes_per_second

            # How many times to retry if an HTTPError occurs
            self.retries: int = retries

    def add_element(self, pack_format: int, version_name: str):
        """Add a version to the correct pack format list"""
        # Get an existing or a new list and add the version name
        format_version_list = self.results.get(pack_format, [])
        format_version_list.append(version_name)

        # If the list was just newly created, store it in the dictionary
        if len(format_version_list) == 1:
            self.results[pack_format] = format_version_list

    @staticmethod
    def should_use_server_jar(version_name: str):
        # Full release
        if matched := match(r'^\d\.\d+(\.\d+)?', version_name): # Regex matches anything starting with 1.XX[.Y]
            # This also matches X.Y.Z-preN and X.Y.Z-rcN versions,
            # so we need to extract the release version name
            components = matched.group().split('.')
            return int(components[1]) >= 14 # The first release version after 18w47b is 1.14
        # Snapshot
        elif fullmatch(r'^\d+w\d+[a-z]$', version_name): # Regex matches XXwYYz
            year = int(version_name[:2])
            week = int(version_name[3:5])
            letter = version_name[-1]

            # Is True if version_name is 18w47b or newer
            return year > 18 or (year == 18 and (week > 47 or (week == 47 and letter == 'b')))

    def start(self):
        try:
            for version_info in self.versions:
                # If the version was alread processed, skip
                if version_info['id'] in already_processed:
                    print(f'Skipping version {version_info['id']} as it\'s already been processed')
                    continue

                # Check if we can find version.json in server.jar
                if not self.use_server_jar:
                    self.use_server_jar = WorkerProcess.should_use_server_jar(version_info['id'])

                jar_download = requests.get(version_info['url']).json()['downloads']['server' if self.use_server_jar else 'client']

                for _ in range(self.retries):
                    try:
                        with requests.get(jar_download['url'], stream=True) as r:
                            # Raise an error here if one occurred
                            r.raise_for_status()
                            with TemporaryFile('w+b') as temp_file:
                                # Download client/server jar
                                # https://requests.readthedocs.io/en/latest/user/quickstart/#raw-response-content
                                # https://stackoverflow.com/questions/16694907/download-large-file-in-python-with-requests
                                print(f'Downloading {jar_download['url']}...')

                                bytes_written: int = 0
                                start_time: int = time_ns()

                                for chunk in r.iter_content(chunk_size=1024 * 8):
                                    temp_file.write(chunk)

                                    bytes_written += 1024 * 8
                                    elapsed_time = time_ns() - start_time
                                    expected_time = bytes_written / self.bytes_per_second

                                    if expected_time > elapsed_time:
                                        # We have already downloaded the amount of
                                        # data we should have downloaded after
                                        # expected_time, so we just wait a
                                        # moment so elapsed_time == expected_time
                                        sleep(expected_time - elapsed_time)

                                # Verify SHA1 hash
                                print(f'Verifying download for version {version_info['id']} using SHA1...')
                                jar_hash = sha1()
                                temp_file.seek(0)
                                while data_block := temp_file.read(64 * 1024): # Input the data in blocks of 64KiB
                                    jar_hash.update(data_block)
                                if jar_hash.hexdigest() != jar_download['sha1']:
                                    raise ValueError

                                # Extract version.json
                                temp_file.seek(0)
                                with ZipFile(temp_file) as jar_file:
                                    with jar_file.open('version.json') as version_json:
                                        pack_version: int | dict[str,int] = json_load(version_json)['pack_version']

                                    # For older version, it's just one integer
                                    if isinstance(pack_version, int):
                                        pack_format_id = pack_version
                                    # For newer versions, it's a dict containing the 'data' and 'resource' keys
                                    else:
                                        pack_format_id = pack_version['data']

                                # Make the entry
                                print(f'Successfully extracted pack format: {version_info['id']} -> {pack_format_id}')
                                self.add_element(pack_format_id, version_info['id'])

                        # If everything went smoothly, we can break the loop and don't need
                        # to retry the procedure
                        break
                    except HTTPError as e:
                        print(f'Download for {version_info['id']} failed: {e}',file=stderr)
                    except ValueError:
                        print(f'Hash mismatch for downloaded jar for version {version_info['id']}',file=stderr)
        except KeyboardInterrupt:
            pass
        finally:
            # Return results at the end
            return self.results


# Shared variables
parsed: Namespace = Namespace()
pack_formats: dict[int,list[str]] | None = None
version_list: list[dict] | None = None
worker_threads: list[Future] = []
process_pool: ProcessPoolExecutor | None = None
already_processed: list[str] = []

def configure():
    # Set up arg parser
    parser = ArgumentParser(prog='Pack Format Extractor',
                            description='Extract the Data Pack format for each Minecraft version from the client.jar/server.jar',
                            epilog='Written by helmo2019')
    parser.add_argument('--threads', '-T', nargs='?', type=int, default=4, help='Number of threads to use',
                        dest='threads')
    parser.add_argument('--bandwidth-limit', '-b', nargs='?', type=int, default=(6 * 1024 * 1024), # 6 MiB
                        help='Maximum downloaded bytes / second. Defaults to 6 MiB', dest='bandwidth')
    parser.add_argument('--retries', '-r', nargs='?', type=int, default=3,
                        help='Number of retries in case of a failed download', dest='retries')
    parser.add_argument('--from-version', '-f', nargs='?', type=str, default='0',
                        help='Version to start from. Can be either a version name or the index in the versions list.',
                        dest='from_version')
    parser.add_argument('--to-version', '-t', nargs='?', type=str, default='17w43a',
                        help='Version to stop at. Can be either a version name or the index in the versions list.',
                        dest='to_version')
    parser.add_argument('--merge', '-m', action='store_true', default=True,
                        help='Whether to merge the extracted data into an existing output file', dest='merge')
    parser.add_argument('--output', '-o', type=str, help='Output file', default='data_pack_formats.json', dest='output')

    # Parse args
    parser.parse_args(namespace=parsed)
    print(f'Running with parameters: {parsed.threads} threads; {parsed.bandwidth}b bandwidth limit; {parsed.retries}'
          f' max retries; from {parsed.from_version}; to {parsed.to_version}; merge: {parsed.merge}; output: {parsed.output}')

    # Load / create results dictionary
    global pack_formats
    if parsed.merge:
        if isfile(parsed.output):
            with open(parsed.output, 'r') as output_file:
                # Load JSON, converting the keys from strings to integers
                pack_formats = {int(key): value for key, value in json_load(output_file).items()}

                for processed_versions in pack_formats.values():
                    already_processed.extend(processed_versions)
        else:
            pack_formats = {}
    else:
        pack_formats = {}


def find_versions():
    # Get the version manifest
    global version_list
    print('Downloading versions manifest...')
    version_list = requests.get('https://piston-meta.mojang.com/mc/game/version_manifest_v2.json').json()['versions']
    version_indices: dict[int, str] = {i: version_list[i]['id'] for i in range(len(version_list))}

    # Find the indices of the first and last version to process
    def find_index(search: str) -> int:
        if fullmatch(r'\d+', search):
            literal_index = int(search)
            if 0 <= literal_index < len(version_list):
                return literal_index
            else:
                raise IndexError(f'No version with index {literal_index}')
        else:
            matching_indices = [version_index for version_index in version_indices.keys() if
                                version_indices[version_index] == search]
            if len(matching_indices) > 0:
                return matching_indices[0]
            else:
                raise ValueError(f'No such version: {parsed.from_version}')

    first_version_index, last_version_index = find_index(parsed.from_version), find_index(parsed.to_version)
    print(
        f'Processions versions #{first_version_index} ({version_indices[first_version_index]}) to #{last_version_index} ({version_indices[last_version_index]})')
    version_list = version_list[min(first_version_index,last_version_index):max(last_version_index, first_version_index)+1]
    print(f'new list size: {len(version_list)}')


def setup_workers():
    # Number of version to process per thread
    per_thread = int(ceil(len(version_list) / parsed.threads))

    # Populate a thread pool executor
    bandwidth_per_thread = parsed.bandwidth // parsed.threads
    global process_pool
    process_pool = ProcessPoolExecutor(parsed.threads)
    for version_range in range(parsed.threads):
        worker_threads.append(process_pool.submit(WorkerProcess(
            version_list[version_range * per_thread: (version_range + 1) * per_thread],
            bandwidth_per_thread, parsed.retries).start))

def main():
    # Attempt configuration / initialization
    try:
        configure()
        find_versions()
    except KeyboardInterrupt:
        exit(0)

    # Wait until everything is done
    try:
        # Submit all workers
        setup_workers()

        # Wait for everything to complete
        for future in as_completed(worker_threads):
            future.result()

    except KeyboardInterrupt:
        print('Program stopped by KeyboardInterrupt: Stopping threads and saving results...')

    # Store results
    while True:
        try:
            # Yield and store results
            for future in as_completed(worker_threads):
                result = future.result()
                for pack_format in result:
                    # No list mapped yet; We can just use the one from the result
                    if not pack_format in pack_formats:
                        pack_formats[pack_format] = result[pack_format]
                    # Extend a previously mapped list
                    else:
                        pack_formats[pack_format].extend(result[pack_format])

            # Sort results
            sorted_results = {}
            for key in sorted(pack_formats):
                sorted_results[key] = pack_formats[key]

            # Write results
            with open(parsed.output, 'w') as output_json:
                json_write(sorted_results, output_json, indent=4, ensure_ascii=False) # type: ignore

            break
        except KeyboardInterrupt:
            # KeyboardInterrupt just restarts the collection & storage process >:)
            # (spamming CTRL+C still ends the program eventually as it will at some
            #  point happen while this except block is executing so it won't be caught)
            print('Please wait a moment, the program is just finishing up...')
            pass


if __name__ == '__main__':
    main()
