#!/usr/bin/env python3
"""
    Purpose:
        Test File for twosix_whiteboard_utils.py
"""

# Python Library Imports
import os
import sys
import pytest
from unittest import mock

# Local Library Imports
from race_python_utils import twosix_whiteboard_utils


###
# Fixtures / Mocks
###

# N/A


###
# Test Payload
###


def test_generate_local_two_six_whiteboard_details():
    generated_local_details = (
        twosix_whiteboard_utils.generate_local_two_six_whiteboard_details()
    )

    expected = {
        "authenticated_service": False,
        "hostname": "twosix-whiteboard",
        "name": "twosix-whiteboard",
        "port": 5000,
        "protocol": "http",
        "url": "twosix-whiteboard:5000",
    }

    assert expected == generated_local_details
