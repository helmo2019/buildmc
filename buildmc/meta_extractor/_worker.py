from json import load as json_load
from tempfile import TemporaryFile
from zipfile import ZipFile

from . import _config as config
from . import _util as util
from .._util import download, download_json


class WorkerProcess:
    """A worker that processes a list of versions"""

    def __init__(self, versions: list, retries: int, bytes_per_second: int):
        # Where we'll store the results. Maps <version name> -> <version.json contents>
        self.results: dict[str, dict] = {}

        if len(versions) > 0:
            # The first item in the list should be the newest
            # and the last item the oldest version
            self.versions: list = versions

            # Limits how many bytes can be downloaded in a single second
            self.bytes_per_second: int = bytes_per_second

            # How many times to retry if an HTTPError occurs
            self.retries: int = retries

    def start(self):
        try:
            for version_info in self.versions:
                # If the version was already processed, skip
                if version_info['id'] in config.version_meta:
                    print(f"Skipping version '{version_info['id']}' as it's already been processed", flush=True)
                    continue

                # Check if we can find version.json in server.jar
                if not util.includes_version_json(version_info['releaseTime']):
                    print(f"Skipping version '{version_info['id']}' as it does not contain version.json", flush=True)
                    continue

                # Get download URL
                downloads = download_json(version_info['url'], rate_limit=self.bytes_per_second,
                                                  sha1_sum=version_info['sha1'])['downloads']


                # Choose smaller download
                jar_download = downloads[
                    'server' if downloads['server']['size'] < downloads['client']['size'] else 'client']

                with TemporaryFile('w+b') as temp_file:
                    # Download JAR file
                    print(f"Downloading '{version_info['id']}' from '{jar_download['url']}'...", flush=True)

                    if not download(temp_file, jar_download['url'], rate_limit=self.bytes_per_second,
                                  retries=self.retries, sha1_sum=jar_download['sha1']):
                        print(f"Error: Download for version '{version_info['id']}' failed!")

                    # Extract version.json
                    temp_file.seek(0)
                    with ZipFile(temp_file) as jar_file:
                        with jar_file.open('version.json') as version_json_file:
                            version_json = json_load(version_json_file)

                    # Make the entry
                    print(f"Successfully extracted version.json of '{version_info['id']}'", flush=True)
                    self.results[version_info['id']] = version_json
        except KeyboardInterrupt:
            pass
        finally:
            # Return results at the end
            return self.results
