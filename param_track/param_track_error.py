# -*- mode: python; coding: utf-8 -*-
# Copyright 2025 David R DeBoer
# Licensed under the MIT license. See LICENSE file in the project root for details.
from datetime import datetime

class ParameterTrackError(Exception):
    """Parameter track exception handling."""
    def __init__(self, message):
        self.message = message


class aNotice:
    """A single parameter track notice."""
    def __init__(self, message, silent):
        self.time = datetime.now()
        self.silent = silent
        self.message = message

class Notices:
    """Parameter track notice handling."""
    def __init__(self):
        self.notices = []

    def post(self, message, silent=False):
        self.notices.append(aNotice(message, silent))
        if not silent:
            print(f"NOTICE: {message}")