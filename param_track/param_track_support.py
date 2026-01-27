# -*- mode: python; coding: utf-8 -*-
# Copyright 2025 David R DeBoer
# Licensed under the MIT license. See LICENSE file in the project root for details.
from datetime import datetime


class ParameterTrackError(Exception):
    """Parameter track exception handling."""
    def __init__(self, message):
        self.message = message


class LogEntry:
    """A single parameter track log entry."""
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
            print(message)

    def show(self):
        print("Log")
        print("---")
        for entry in self.log:
            print(entry)


def typename(val):
    if isinstance(val, type):
        return val.__name__
    return type(val).__name__


def typemsg(key, oldt, newt, action):
    msg = f"Parameter types don't match for '{key}': <old: {typename(oldt)}> vs <new: {typename(newt)}>"
    if action == 'retain':
        msg += f" -- retaining <{typename(oldt)}>."
    elif action == 'reset':
        msg += f" -- resetting to <{typename(newt)}>."
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