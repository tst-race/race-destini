"""
    Purpose:
        Utilities for interacting with the Two Six Whiteboard
"""

# Python Library Imports
from typing import Dict, Union


def generate_local_two_six_whiteboard_details() -> Dict[str, Union[str, int, bool]]:
    """
    Purpose:
        Generate Two Six Whiteboard details for link creation for a local
        deployment. This assumes that connectivity will use local docker networking
        instead of the range config information.
    Args:
        N/A
    Returns:
        two_six_whiteboard_details: Two Six Whiteboard connectivity using local
        docker networking instead of the range config information
    """

    return {
        "authenticated_service": False,
        "hostname": "twosix-whiteboard",
        "name": "twosix-whiteboard",
        "port": 5000,
        "protocol": "http",
        "url": "twosix-whiteboard:5000",
    }
