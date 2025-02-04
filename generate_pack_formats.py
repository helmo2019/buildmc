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
from sys import stderr, exit
from zipfile import ZipFile
from json import load as json_load
from math import ceil
from concurrent.futures import ThreadPoolExecutor, Future


class WorkerThread:
    def __init__(self, versions: list, download_chunk_size: int, retries: int):
        # The first item in the list should be the newest
        # and the last item the oldest version
        self.versions = versions

        # Where we'll store the results
        self.results: dict[int, list[str]] = {}

        # If the oldest version already has version.json in the server.jar,
        # we can already set this to True and don't need to check for every
        # version
        self.use_server_jar = WorkerThread.should_use_server_jar(versions[-1]['id'])

        # How large the download chunks should be
        self.chunk_size = download_chunk_size

        # How many times to retry if an HTTPError occurs
        self.retries = retries

    def add_element(self, pack_format: int, version_name: str):
        """Add a version to the correct pack format list"""
        # Get an existing or a new list and add the version name
        version_list = self.results.get(pack_format, [])
        version_list.append(version_name)

        # If the list was just newly created, store it in the dictionary
        if len(version_list) == 1:
            self.results[pack_format] = version_list

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
        for version_info in self.versions:
            # Check if we can find version.json in server.jar
            if not self.use_server_jar:
                self.use_server_jar = WorkerThread.should_use_server_jar(version_info['id'])

            jar_download = requests.get(version_info['url']).json()['downloads']['server' if self.use_server_jar else 'client']

            for _ in range(self.retries):
                try:
                    with requests.get(jar_download['url'], stream=True) as r:
                        # Raise an error here if one occurred
                        r.raise_for_status()
                        with TemporaryFile() as temp_file:
                            # Download client/server jar
                            # https://requests.readthedocs.io/en/latest/user/quickstart/#raw-response-content
                            # https://stackoverflow.com/questions/16694907/download-large-file-in-python-with-requests
                            for chunk in r.iter_content(chunk_size=self.chunk_size):
                                temp_file.write(chunk)

                            # TODO verify checksum

                            # Extract version.json
                            with ZipFile(temp_file) as jar_file:
                                with jar_file.open('version.json') as version_json:
                                    pack_version: int | dict[str,int] = json_load(version_json)

                                # For older version, it's just one integer
                                if isinstance(pack_version, int):
                                    pack_format_id = pack_version
                                # For newer versions, it's a dict containing the 'data' and 'resource' keys
                                else:
                                    pack_format_id = pack_version['data']

                            # Make the entry
                            self.add_element(pack_format_id, version_info['id'])
                    # If everything went smoothly, we can break the loop and don't need
                    # to retry the procedure
                    break
                except HTTPError as e:
                    print(f'Download for {version_info['id']} failed: {e}',file=stderr)




def main():
    # Configure to your liking
    concurrent_threads = 4
    bandwidth = 10 * (1024*1024) # 10 MiB
    retries = 3

    bandwidth_per_thread = bandwidth // concurrent_threads

    # Results
    pack_formats: dict[int,list[str]] = {}

    # Get the version manifest
    version_manifest = requests.get('https://piston-meta.mojang.com/mc/game/version_manifest_v2.json').json()
    version_list = version_manifest['versions']

    # Find the index of 17w43a, the version data packs were added
    first_version_index = -1
    for i in range(len(version_list)):
        if version_list[i]['id'] == '17w43a':
            first_version_index = i
            break

    if first_version_index != -1:
        # Delete unneeded versions from the list
        del version_list[first_version_index+1:]
    else:
        print(f'Unable to find 17w43a in the versions list!')
        exit(1)

    ## Distribute the downloads across the threads
    # Number of version to process per thread
    per_thread = int(ceil(len(version_list) / concurrent_threads))

    # Populate a thread pool executor
    thread_pool = ThreadPoolExecutor(concurrent_threads)
    worker_threads: list[Future] = []
    for version_range in range(concurrent_threads):
        worker_threads.append(thread_pool.submit(WorkerThread(
            version_list[version_range * per_thread: (version_range + 1) * per_thread],
            bandwidth_per_thread, retries).start))

    # Wait until everything is done
    while len([task for task in worker_threads if not task.done()]) > 0:
        pass

    # TODO Add results to the final list

    # TODO add cli parameters for specifying a version range to check; add option for merging results into existing file


if __name__ == '__main__':
    main()