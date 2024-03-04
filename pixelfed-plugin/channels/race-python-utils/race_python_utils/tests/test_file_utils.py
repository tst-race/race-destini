#!/usr/bin/env python3
"""
    Purpose:
        Test File for file_utils.py
"""

# Python Library Imports
import os
import pathlib
import pytest
import sys
from unittest import mock

# Local Library Imports
from race_python_utils import file_utils


###
# Fixtures / Mocks
###


def _get_test_file_path(file_name: str) -> str:
    """
    Test File Path
    """

    return f"{os.path.join(os.path.dirname(__file__))}/files/{file_name}"


###
# Tests
###

###
# load_file_into_memory
###


def test_load_file_into_memory_reads_json() -> int:
    """
    TODO
    """

    pass

    # bytes_file = _get_test_file_path("test.json")
    # data = file_utils.load_file_into_memory(bytes_file, "json")

    # assert type(data) is dict
    # assert len(data.keys()) == 1
    # assert len(data[list(data.keys())[0]].keys()) == 2
