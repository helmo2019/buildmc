"""Transforms the output of buildmc.meta_extractor.main into different arrangements"""

from argparse import ArgumentParser
from json import dumps as json_encode, load as json_load
from sys import argv
from typing import Any

_direct_data_fields = ('protocol_version','world_version','name','pack_version')
data_fields = _direct_data_fields + ('version','data_pack_version','resource_pack_version')

# 1. Make a list of all versions / iterate over .items() ?
# 2. For each version, get the index data field and...
# 2.a If it is mapped to a list: append version[index data field] to that list
# 2.b If there is nothing mapped: map new list & append version[index data field]

def get_data_field(version_id: str, version_meta: dict[str,int|str|dict[str,int]], data_field: str) -> int|str|dict[str,int]:
    """Extract a data field from version meta data"""

    if data_field in _direct_data_fields:
        return version_meta[data_field]
    elif data_field == 'version':
        return version_id
    elif data_field in ('data_pack_version','resource_pack_version'):
        if isinstance(version_meta['pack_version'], int):
            return version_meta['pack_version']
        else:
            return (version_meta['pack_version']
                ['resource' if data_field == 'resource_pack_version' else 'data'])
    else:
        raise ValueError

def main(args: list[str] | dict | None):
    # Set up parser
    parser: ArgumentParser = ArgumentParser(prog='Version Data Mapping Generator',
                            description='Generate different data mappings (e.g. version name -> data pack format) from'
                                        ' the output of the version meta extractor',
                            epilog='Written by helmo2019')
    parser.add_argument('input', help='Input file')
    parser.add_argument('index_field', choices=data_fields, help='Index data field')
    parser.add_argument('value_field', choices=data_fields, help='Value data field')
    parser.add_argument('output', help='Output JSON file')
    parser.add_argument('--unwrap', action='store_true', help='Pass to unwrap lists that only contain one element')

    # Default to sys.argv. Can't use default
    # parameter syntax because sys.argv is mutable.
    if args is None:
        args = argv[1:]

    # Parse args
    parsed = parser.parse_args(args)

    # Load source data
    with open(parsed.input) as source_file:
        source_data: dict[str,dict] = json_load(source_file)
    del source_file

    # Generate output data
    output_data: dict[int|str,list|Any] = {}

    for version, meta in source_data.items():
        index_value = get_data_field(version, meta, parsed.index_field)
        mapped_value = get_data_field(version, meta, parsed.value_field)

        # Ensure there is a list mapped
        if index_value in output_data:
            destination = output_data[index_value]
        else:
            destination = []
            output_data[index_value] = destination

        # Add mapped value
        destination.append(mapped_value)

    # Unwrap one-element lists
    if parsed.unwrap:
        output_data = {key: (output_data[key][0] if len(output_data[key]) == 1 else output_data[key])
                   for key,value in output_data.items()}


    aliases_section = ''',
    "aliases": {
        "1.14.2-pre4": "1.14.2 Pre-Release 4",
        "1.14.2-pre3": "1.14.2 Pre-Release 3",
        "1.14.2-pre2": "1.14.2 Pre-Release 2",
        "1.14.2-pre1": "1.14.2 Pre-Release 1",

        "1.14.1-pre2": "1.14.1 Pre-Release 2",
        "1.14.1-pre1": "1.14.1 Pre-Release 1",

        "1.14-pre5": "1.14 Pre-Release 5",
        "1.14-pre4": "1.14 Pre-Release 4",
        "1.14-pre3": "1.14 Pre-Release 3",
        "1.14-pre2": "1.14 Pre-Release 2",
        "1.14-pre1": "1.14 Pre-Release 1",


        "potato_update": "24w14potato",
        "vote_update": "23w13a_or_b",
        "one_block_at_a_time": "22w13oneblockatatime",
        "infinite": "20w14infinite",
        "3d_shareware": "3D Shareware v1.34"
    }\n''' if 'version' in (parsed.index_field, parsed.value_field) else ''

    # Write to file
    with open(parsed.output, 'w') as destination_file:
        # Properly indent JSON string
        json_string = json_encode(output_data, indent=4)
        json_lines = json_string.splitlines()
        for i in range(1,len(json_lines)):
            json_lines[i] = '    ' + json_lines[i]
        json_string = '\n'.join(json_lines)

        destination_file.write(f'{{\n    "data": {json_string}'
                               f'{aliases_section}}}')

if __name__ == '__main__':
    main(None)
