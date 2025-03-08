from datetime import datetime
from re import match, fullmatch

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

