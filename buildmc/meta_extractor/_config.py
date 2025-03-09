from argparse import ArgumentParser, Namespace
from concurrent.futures import Future, ProcessPoolExecutor
from typing import Optional


# Shared variables
options: Namespace = Namespace()
default_options: dict = {
    'threads': 4,
    'bandwidth': (6 * 1024 * 1024),  # 6 MiB
    'retries': 3,
    'from_version': '0',
    'to_version': '18w47b',
    'merge': True
}
version_meta: Optional[dict[str, dict]] = None
version_list: Optional[list[dict]] = None
worker_threads: list[Future] = []
process_pool: Optional[ProcessPoolExecutor] = None
already_processed: list[str] = []


def reset():
    """Reset to default values"""
    global options, version_meta, version_list, worker_threads, process_pool, already_processed
    options = Namespace()
    version_meta = None
    version_list = None
    worker_threads = []
    process_pool = None
    already_processed = []


# Set up arg parser
parser = ArgumentParser(prog='Pack Format Extractor',
                        description='Extract the Data Pack format for each Minecraft version from the '
                                    'client.jar/server.jar',
                        epilog='Written by helmo2019')
parser.add_argument('--threads', '-T', nargs='?', type=int, default=default_options['threads'], help='Number of threads to use',
                    dest='threads')
parser.add_argument('--bandwidth-limit', '-b', nargs='?', type=int, default=default_options['bandwidth'],
                    help='Maximum downloaded bytes / second. Defaults to 6 MiB', dest='bandwidth')
parser.add_argument('--retries', '-r', nargs='?', type=int, default=default_options['retries'],
                    help='Number of retries in case of a failed download', dest='retries')
parser.add_argument('--from-version', '-f', nargs='?', type=str, default=default_options['from_version'],
                    help="Version to start from. Can be either a version name ('id' field in version manifest) or the "
                         "index in the versions list.",
                    dest='from_version')
# 17w43a introduced data packs, but version.json is only available since 18w47b
parser.add_argument('--to-version', '-t', nargs='?', type=str, default=default_options['to_version'],
                    help="Version to stop at. Can be either a version name ('id' field in version manifest) or the "
                         "index in the versions list.",
                    dest='to_version')
parser.add_argument('--merge', '-m', action='store_true', default=default_options['merge'],
                    help='Whether to merge the extracted data into an existing output file', dest='merge')
parser.add_argument('--output', '-o', type=str, help='Output file', default='version_meta.json', dest='output')
