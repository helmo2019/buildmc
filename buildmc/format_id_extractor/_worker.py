from hashlib import sha1
from json import load as json_load
from re import fullmatch, match
from sys import stderr
from tempfile import TemporaryFile
from time import time_ns, sleep
from zipfile import ZipFile

import requests

from . import _config as config


class WorkerProcess:
    """A worker that processes a list of versions"""

    def __init__(self, versions: list, retries: int, bytes_per_second: int):
        # Where we'll store the results
        self.results: dict[int, list[str]] = {}

        if len(versions) > 0:
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
        if matched := match(r'^\d\.\d+(\.\d+)?', version_name):  # Regex matches anything starting with 1.XX[.Y]
            # This also matches X.Y.Z-preN and X.Y.Z-rcN versions,
            # so we need to extract the release version name
            components = matched.group().split('.')
            return int(components[1]) >= 14  # The first release version after 18w47b is 1.14
        # Snapshot
        elif fullmatch(r'^\d+w\d+[a-z]$', version_name):  # Regex matches XXwYYz
            year = int(version_name[:2])
            week = int(version_name[3:5])
            letter = version_name[-1]

            # Is True if version_name is 18w47b or newer
            return year > 18 or (year == 18 and (week > 47 or (week == 47 and letter == 'b')))

    def start(self):
        try:
            for version_info in self.versions:
                # If the version was already processed, skip
                if version_info['id'] in config.already_processed:
                    print(f'Skipping version {version_info['id']} as it\'s already been processed')
                    continue

                # Check if we can find version.json in server.jar
                if not self.use_server_jar:
                    self.use_server_jar = WorkerProcess.should_use_server_jar(version_info['id'])

                jar_download = requests.get(version_info['url']).json()['downloads'][
                    'server' if self.use_server_jar else 'client']

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
                                while data_block := temp_file.read(64 * 1024):  # Input the data in blocks of 64KiB
                                    jar_hash.update(data_block)
                                if jar_hash.hexdigest() != jar_download['sha1']:
                                    raise ValueError

                                # Extract version.json
                                temp_file.seek(0)
                                with ZipFile(temp_file) as jar_file:
                                    with jar_file.open('version.json') as version_json:
                                        pack_version: int | dict[str, int] = json_load(version_json)['pack_version']

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
                    except requests.HTTPError as e:
                        print(f'Download for {version_info['id']} failed: {e}', file=stderr)
                    except ValueError:
                        print(f'Hash mismatch for downloaded jar for version {version_info['id']}', file=stderr)
        except KeyboardInterrupt:
            pass
        finally:
            # Return results at the end
            return self.results
