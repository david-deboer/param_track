# -*- mode: python; coding: utf-8 -*-
# Copyright 2025 David R DeBoer
# Licensed under the MIT license. See LICENSE file in the project root for details.
from datetime import datetime


class ParameterTrackError(Exception):
    """Parameter track exception handling."""
    def __init__(self, message):
        self.message = message

class LogEntry:
    """A single parameter track entry."""
    def __init__(self, message, silent):
        self.time = datetime.now()
        self.silent = silent
        self.message = message

    def __str__(self):
        return f"{self.time}  --  {self.message}"


class Log:
    """Parameter track log handling."""
    def __init__(self):
        self.log = []

    def post(self, message, silent=False):
        self.log.append(LogEntry(message, silent))
        if not silent:
            print(f"Entry: {message}")

    def show(self):
        print("Log")
        print("---")
        for entry in self.log:
            print(entry)


def typemsg(key, oldtype, newtype, action):
    msg = f"Parameter types don't match for '{key}': <old: {oldtype.__name__}> vs <new: {newtype.__name__}>"
    if action == 'retain':
        msg += f" -- retaining <{oldtype.__name__}>."
    elif action == 'reset':
        msg += f" -- resetting to <{newtype.__name__}>."
    return msg


def check_serialize(serialize, val):
    if serialize is None or serialize == 'pickle':
        return val

    if serialize == 'json' or serialize == 'yaml':
        if isinstance(val, datetime):
            return val.isoformat()
        if isinstance(val, type):
            return val.__name__
        try:
            if serialize == 'json':
                import json
                _ = json.dumps({'check': val})
            elif serialize == 'yaml':
                import yaml
                _ = yaml.dump({'check': val})
        except TypeError:
            val = str(val)
    # Finally, just hope...
    return val