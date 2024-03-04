"""
    Purpose:
        Utilities for dealing with files and i/o
"""

# Python Library Imports
import logging
import json
import os
import shutil
from typing import Any, Dict, List, Optional


###
# Prepare Config Dir Functions
###


def prepare_network_manager_config_dir(config_dir: str, overwrite: bool) -> None:
    """
    Purpose:
        Prepare the base config dir.
    Args:
        config_dir: Base path to the config dir
        overwrite: Should we overwrite the config dir if it exists?
    Return:
        N/A
    """

    # Check for existing dir and overwrite
    if os.path.isdir(config_dir):
        if overwrite:
            logging.info(f"{config_dir} exists and overwrite set, removing")
            shutil.rmtree(config_dir)
        else:
            raise Exception(f"{config_dir} exists and overwrite not set, exiting")

    # Make dirs
    os.makedirs(config_dir)
    os.mkdir(f"{config_dir}/personas/")
    os.mkdir(f"{config_dir}/committees/")


def prepare_comms_config_dir(config_dir: str, overwrite: bool) -> None:
    """
    Purpose:
        Prepare the base config dir.
    Args:
        config_dir: Base path to the config dir
        overwrite: Should we overwrite the config dir if it exists?
    Return:
        N/A
    """

    # Check for existing dir and overwrite
    if os.path.isdir(config_dir):
        if overwrite:
            logging.info(f"{config_dir} exists and overwrite set, removing")
            shutil.rmtree(config_dir)
        else:
            raise Exception(f"{config_dir} exists and overwrite not set, exiting")

    # Make dirs
    os.makedirs(config_dir)


###
# Read Functions
###


def read_json(json_filename: str) -> Dict[str, Any]:
    """
    Purpose:
        Load the range config file into memory as python Dict
    Args:
        json_filename: JSON filename to read
    Raises:
        Exception: if json is invalid
        Exception: if json is not found
    Returns:
        loaded_json: Loaded JSON
    """

    try:
        with open(json_filename, "r") as json_file_onj:
            return json.load(json_file_onj)
    except Exception as load_err:
        logging.error(f"Failed loading {json_filename}")
        raise load_err


###
# Write Functions
###


def write_json(json_object: Dict[str, Any], json_file: str) -> None:
    """
    Purpose:
        Load Dictionary into JSON File
    Args:
        json_object: Dictionary to be stored in .json format
        json_file: Filename for JSON file to store (including path)
    Returns:
        N/A
    Examples:
        >>> json_file = 'some/path/to/file.json'
        >>> json_object = {
        >>>     'key': 'value'
        >>> }
        >>> write_json_into_file(json_file, json_object)
    """
    logging.info(f"Writing JSON File Into Memory: {json_file}")

    with open(json_file, "w") as file:
        json.dump(json_object, file, sort_keys=True, indent=4, separators=(",", ": "))


def write_bytes(bytes_object: Any, bytes_file: str) -> None:
    """
    Purpose:
        Load Bytes into File
    Args:
        bytes_object: bytes to be stored to the file
        bytes_file: Filename for file to store (including path)
    Returns:
        N/A
    """
    logging.info(f"Writing Bytes File Into Memory: {bytes_file}")

    with open(bytes_file, "wb") as file_obj:
        file_obj.write(bytes_object)
