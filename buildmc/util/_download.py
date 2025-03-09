"""Utilities related to downloading & verifying files"""

import json
from hashlib import sha1
from io import BytesIO
from time import sleep, time_ns
from typing import Optional

import requests

from . import _logging as l


def download(fp, url: str, rate_limit: int = -1, retries: int = 3, sha1_sum: Optional[str] = None) -> bool:
    """
    Download a file from a URL with a download rate limit (bytes / s) and verify using a SHA1 sum

    :param fp: The file to write to
    :param url: The URL to download from
    :param rate_limit: Maximum number of bytes to download in one second
    :param retries: How many times to retry the download in case of failure
    :param sha1_sum: The SHA1 checksum to use for download validation
    :return: Whether the download was successful
    """

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
            if sha1_sum is not None and not _verify_sha1(fp, sha1_sum):
                # This error is caught in the second except clause below
                raise ChecksumMismatchError()

            # Return True if the download was successful
            return True
        except requests.HTTPError as e:
            l.log(f"HTTP error occurred for '{url}': {e}", l.log_warn)
        except ChecksumMismatchError:
            l.log(f"SHA1 mismatch for download of '{url}'", l.log_warn)

    l.log(f"Download of '{url}' failed after {retries} attempts", l.log_error)
    return False


def download_json(url: str, rate_limit: int = -1, sha1_sum: Optional[str] = None) -> dict:
    """
    Download a JSON file from a URL with a download rate limit (bytes / s) and verify using a SHA1 sum.
    The file is downloaded into an io.BytesIO object.

    :param url: The URL to download from
    :param rate_limit: Maximum number of bytes to download in one second
    :param sha1_sum: The SHA1 checksum to use for download validation
    """

    with BytesIO() as in_memory_file:
        # Download & verify file
        if download(in_memory_file, url, rate_limit=rate_limit, sha1_sum=sha1_sum):
            # Parse json
            in_memory_file.seek(0)  # IMPORTANT!!!
            return json.load(in_memory_file)
        else:
            return { }


class ChecksumMismatchError(Exception):
    """Exception raised for checksum mismatches"""


    def __init__(self):
        super().__init__()


def _verify_sha1(fp, expected: str) -> bool:
    """

    :param fp:
    :param expected:
    :return:
    """

    file_hash = sha1()
    fp.seek(0)
    while data_block := fp.read(64 * 1024):  # Input the data in blocks of 64KiB
        file_hash.update(data_block)

    return file_hash.hexdigest() == expected
