"""Application for extracting version.json from client.jar files"""

from .main import main
from .transform import main as transformer


aliases = {
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
}


def real_version_name(version_name: str):
    """
    Get the real name of a version

    :param version_name: The version name to resolve
    :return: The corresponding value in the aliases dictionary, or the given version name
    """

    return aliases[version_name] if version_name in aliases else version_name
