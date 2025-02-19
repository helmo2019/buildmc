from argparse import Namespace, ArgumentParser
from concurrent.futures import Future, ProcessPoolExecutor

# Shared variables
options: Namespace = Namespace()
pack_formats: dict[int,list[str]] | None = None
version_list: list[dict] | None = None
worker_threads: list[Future] = []
process_pool: ProcessPoolExecutor | None = None
already_processed: list[str] = []

# Set up arg parser
parser = ArgumentParser(prog='Pack Format Extractor',
                        description='Extract the Data Pack format for each Minecraft version from the client.jar/server.jar',
                        epilog='Written by helmo2019')
parser.add_argument('--threads', '-T', nargs='?', type=int, default=4, help='Number of threads to use',
                    dest='threads')
parser.add_argument('--bandwidth-limit', '-b', nargs='?', type=int, default=(6 * 1024 * 1024),  # 6 MiB
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