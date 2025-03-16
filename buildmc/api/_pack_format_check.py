"""Verify the compatibility between an external pack and the project"""

from pathlib import Path
from typing import Optional

from buildmc.util import log, log_error, get_json
from . import _project as p


def pack_format_compatible(log_prefix: str, pack_mcmeta: Path, project: p.Project):
    """
    Validate the compatibility between an external pack
    and the project. If the provided pack.mcmeta reports
    the pack to be incompatible with the project or if
    there is an error at any point, the project's
    .fail() method is called and the function returns.

    :param log_prefix: Prefix for error log messages
    :param pack_mcmeta: The path to the pack.mcmeta
    :param project: The current project
    """

    # Get the project's pack format and validate it
    project_pack_format: int = project.var_get('project/pack_format')

    if project_pack_format is None or not isinstance(project_pack_format, int):
        log(f'{log_prefix}Pack format is not set or invalid!', log_error)
        project.fail()
        return

    # Make sure pack.mcmeta exists and is a file, then validate
    pack_mcmeta_json = get_json(pack_mcmeta)
    if pack_mcmeta_json is None:
        log(f"{log_prefix}pack.mcmeta at '{pack_mcmeta}' not found or invalid", log_error)
        project.fail()
        return

    # Make sure that 'pack' is in pack.mcmeta
    if 'pack' not in pack_mcmeta_json:
        log(f"{log_prefix}'pack.mcmeta' at '{pack_mcmeta}' is missing the 'pack' property!",
              log_error)
        project.fail()
        return

    # Get 'pack' property
    property_pack: dict = pack_mcmeta_json['pack']

    # Get 'pack_format' property
    if 'pack_format' not in property_pack or not isinstance(property_pack['pack_format'], int):
        log(f"{log_prefix}'pack.mcmeta' at '{pack_mcmeta}' has an invalid 'pack.pack_format'"
              f"property (missing or wrong type)!", log_error)
        project.fail()
        return

    property_pack_format: int = property_pack['pack_format']

    # Also look for 'supported_formats'
    supported_formats: Optional[tuple[int, int]] = None

    if 'supported_formats' in property_pack:
        property_supported_formats = property_pack['supported_formats']

        # Single int
        if isinstance(property_supported_formats, int):
            supported_formats = (property_supported_formats, property_supported_formats)

        # List with two integers
        elif (isinstance(property_supported_formats, list)
              and len(property_supported_formats) == 2
              and isinstance(property_supported_formats[0], int)
              and isinstance(property_supported_formats[1], int)
        ):
            supported_formats = (
                property_supported_formats[0],
                property_supported_formats[1]
            )

        # Dict with 'min_inclusive' and 'max_inclusive' each mapped to an int
        elif (isinstance(property_supported_formats, dict)
              and len(property_supported_formats) == 2
              and isinstance(property_supported_formats.get('min_inclusive', None), int)
              and isinstance(property_supported_formats.get('max_inclusive', None), int)
        ):
            supported_formats = (
                property_supported_formats['min_inclusive'],
                property_supported_formats['max_inclusive']
            )

        # Invalid property
        else:
            log(f"{log_prefix}'pack.mcmeta' at '{pack_mcmeta}' has an invalid"
                  f"'pack.supported_formats' property!", log_error)
            project.fail()
            return

    # Check validity of supported_formats
    if supported_formats is not None and not (
            supported_formats[0] <= property_pack_format <= supported_formats[1]
    ):
        log(f"{log_prefix}'pack.mcmeta' at '{pack_mcmeta}' has 'supported_formats', but it does"
              "not contain the value of 'pack_format'!", log_error)
        project.fail()
        return

    # Verify that the project's pack format is supported
    if (
            supported_formats is not None
            and not (supported_formats[0] <= project_pack_format <= supported_formats[1])
    ) or (
            supported_formats is None
            and project_pack_format != property_pack_format
    ):
        log(f"{log_prefix}Supports pack format(s) "
              f"{property_pack_format if supported_formats is None else str(supported_formats)}"
              f", making it incompatible with the project's pack format {project_pack_format}",
              log_error)
        project.fail()
