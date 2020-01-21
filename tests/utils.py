# coding=utf-8
"""
Created on 19.1.2020

Potku is a graphical user interface for analyzation and
visualization of measurement data collected from a ToF-ERD
telescope. For physics calculations Potku uses external
analyzation components.
Copyright (C) 2013-2020 TODO

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program (file named 'LICENCE').

utils.py contains various utility functions to be used in tests
"""

__author__ = "Juhani Sundell"
__version__ = ""  # TODO

import os
import hashlib
import unittest


def get_sample_data_dir():
    """Returns the absolute path to the sample data directory"""
    # Absolute path to the directory where utils.py file is
    path_to_this_file = os.path.dirname(__file__)
    # Traverse the path to sample data
    path_to_sample_data = os.path.join(path_to_this_file,
                                       os.pardir,
                                       "sample_data")
    # Return the path as an absolute path
    return os.path.abspath(path_to_sample_data)


def get_md5_for_files(file_paths):
    """Calculates MD5 hash for the combined content of all given
    files."""
    for file_path in file_paths:
        hasher = hashlib.md5()
        with open(file_path, "rb") as file:
            buf = file.read()
            hasher.update(buf)

    return hasher.hexdigest()


def check_md5_for_files(file_paths, checksum):
    """Checks that the combined contents of all files match the
    given checksum.

    Args:
        file_paths: absolute paths to file
        checksum: hexadecimal string representation of the expected
            checksum

    Return:
        tuple where first element is a boolean value that tells if
        the given files match the checksum, and second element is a
        message that tells further details about the check.
    """
    try:
        actual_checksum = get_md5_for_files(file_paths)
        if actual_checksum == checksum:
            return True, "files match the given checksum"

        return False, "files do not match the given checksum"
    except Exception as e:
        return False, e


def verify_files(file_paths, checksum, msg=None):
    """Decorator function that can be used to verify files before
    running a test."""
    b, reason = check_md5_for_files(file_paths, checksum)
    if b:
        return lambda func: func
    if msg is not None:
        return unittest.skip("{0}: {1}.".format(msg, reason))
    return unittest.skip(reason)
