"""
    Purpose:
        Client Class. Represents RACE client nodes with an entrance and exit committee
"""

# Python Library Imports
from typing import List, Dict, Any

# Fixes circular dependencies in MyPy typing
MYPY = False
if MYPY:
    from race_python_utils.network_manager import Server  # NOQA


class Client:
    """
    Client Class. Represents RACE client nodes with an entrance and exit committee
    """

    def __init__(self, name: str = ""):
        """
        Purpose:
            Initializer method for the client
        Args:
            name (String): name of the client
        Returns:
            N/A
        """
        self.name = name
        self.reachable_servers: List[Server] = []
        self.entrance_committee: List[Server] = []
        self.exit_committee: List[Server] = []

    def __repr__(self) -> str:
        """
        Purpose:
            Repr for this client to enable Set usage
        Args:
            N/A
        Returns:
            The name of the client
        """
        return self.name

    def json_config(self) -> Dict[str, Any]:
        """
        Purpose:
            Produces the Network Manager committee config for this client in JSON format to be written
                to a deployment
        Args:
            N/A
        Returns:
            Dictionary ready to be JSON-stringified
        """
        return {
            "entranceCommittee": [server.name for server in self.entrance_committee],
            "exitCommittee": [server.name for server in self.exit_committee],
        }
