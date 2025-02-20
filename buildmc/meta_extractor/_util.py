from datetime import datetime
from hashlib import sha1
from io import BytesIO
from json import load
from re import match, fullmatch
from time import sleep, time_ns

import requests

__snapshot_18w47b_release = datetime.fromisoformat('2018-11-23T10:46:41+00:00')

def includes_version_json(version_release_time: str) -> bool:
    return datetime.fromisoformat(version_release_time) >= __snapshot_18w47b_release

def includes_version_json_old(version_name: str) -> bool:
    """Checks if a version is 18w47b or newer"""

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
    else:
        print(f"Error: includes_version_json: Invalid version '{version_name}'")
        return False

def download(fp, url: str, rate_limit: int = -1, retries: int = 3,  sha1_sum: str | None = None) -> bool:
    """Download a file from a URL with a download rate limit (bytes / s) and verify using a SHA1 sum"""

    # Download data
    for _ in range(retries):
        try:
            with requests.get(url, stream=True) as download_stream:
                # Raise an error here if one occurred
                download_stream.raise_for_status()

                # Download file
                # https://requests.readthedocs.io/en/latest/user/quickstart/#raw-response-content
                # https://stackoverflow.com/questions/16694907/download-large-file-in-python-with-requests

                bytes_written: int = 0
                start_time: int = time_ns()
                fp.seek(0)

                for chunk in download_stream.iter_content(chunk_size=1024 * 8):
                    fp.write(chunk)

                    # Anything less than 1 disables the rate limiting
                    if rate_limit > 0:
                        bytes_written += 1024 * 8
                        elapsed_time = time_ns() - start_time

                        expected_time = bytes_written / rate_limit

                        if expected_time > elapsed_time:
                            print(f'sleeping for {expected_time - elapsed_time}')
                            # We have already downloaded the amount of
                            # data we should have downloaded after
                            # expected_time, so we just wait a
                            # moment so elapsed_time == expected_time
                            sleep(expected_time - elapsed_time)

            # Verify hash
            if sha1_sum is not None and not verify_sha1(fp, sha1_sum):
                raise ValueError

            # Return True if the download was successful
            return True
        except requests.HTTPError as e:
            print(f"Warning: HTTP error occurred for '{url}': {e}")
        except ValueError:
            print(f"Warning: Hash mismatch for '{url}'")

    return False



def download_json(url: str, rate_limit: int = -1, sha1_sum: str | None = None) -> dict:
    """
    Download a JSON file from a URL with a download rate limit (bytes / s) and verify using a SHA1 sum.
    The file is downloaded into an io.StringIO object.
    """

    with BytesIO() as in_memory_file:
        # Download & verify file
        if download(in_memory_file, url, rate_limit=rate_limit, sha1_sum=sha1_sum):
            # Parse json
            in_memory_file.seek(0) # IMPORTANT!!!
            return load(in_memory_file)
        else:
            return {}

def verify_sha1(fp, expected: str) -> bool:
    """Compute the SHA1 hash of a file and compare it with a given hash"""

    file_hash = sha1()
    fp.seek(0)
    while data_block := fp.read(64 * 1024):  # Input the data in blocks of 64KiB
        file_hash.update(data_block)

    return file_hash.hexdigest() == expected