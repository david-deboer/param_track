# -*- mode: python; coding: utf-8 -*-
# Copyright 2025 David R DeBoer
# Licensed under the BSD license. See LICENSE.txt file in the project root for details.

class ParameterTrackError(Exception):
    """Parameter track exception handling."""
    def __init__(self, message):
        self.message = message


def Warning(message):
    """Parameter track warning handling."""
    print(f"Warning: {message}")