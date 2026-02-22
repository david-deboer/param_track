# -*- mode: python; coding: utf-8 -*-
# Copyright 2025 David R DeBoer
# Licensed under the MIT license. See LICENSE file in the project root for details.
from datetime import datetime
try:
    from astropy.time import Time, TimeDelta
    from astropy.units import Quantity
except ImportError:
    pass


class ParameterTrackError(Exception):
    """Parameter track exception handling."""
    def __init__(self, message):
        self.message = message


class LogEntry:
    """A single parameter track log entry."""
    def __init__(self, module, message, silent):
        self.time = datetime.now()
        self.module = module
        self.silent = silent
        self.message = message

    def __str__(self):
        return f"{self.module}  --  {self.time}  --  {self.message}"


class Log:
    """Parameter track log handling."""
    def __init__(self, module='Log'):
        self.module = module
        self.log = []

    def post(self, message, silent=False):
        self.log.append(LogEntry(self.module, message, silent))
        if not silent:
            print(message)

    def show(self, file=None, search=None):
        hdr = f"Log: {self.module}"
        print(hdr, file=file)
        print("-" * len(hdr), file=file)
        for entry in self.log:
            if search is None:
                print(entry, file=file)
            elif search in entry.message:
                print(entry, file=file)

def typename(val):
    if isinstance(val, type):
        return val.__name__
    return type(val).__name__

def typemsg(key, oldt, newt, action):
    msg = f"Parameter types don't match for '{key}': old: ({typename(oldt)}) vs new: ({typename(newt)})"
    if action == 'retain':
        msg += f" -- retaining <{typename(oldt)}>."
    elif action == 'reset':
        msg += f" -- resetting to <{typename(newt)}>."
    return msg

def write_to_clipboard(output):
    """ Write output string to clipboard (macOS only). """
    import platform
    if platform.system() == 'Darwin':
        import subprocess
        process = subprocess.Popen(
            'pbcopy', env={'LANG': 'en_US.UTF-8'}, stdin=subprocess.PIPE)
        process.communicate(output.encode('utf-8'))
    else:
        print(f"Clipboard writing not supported on {platform.system()}")
        print(output)

def check_serialize(serialize, val):
    if serialize is None or serialize == 'pickle':
        return val

    if serialize == 'json' or serialize == 'yaml':
        if isinstance(val, datetime):
            return val.isoformat()
        if isinstance(val, Time):
            return val.isot
        if isinstance(val, TimeDelta):
            return f"{float(val.to_value('sec'))} sec"
        if isinstance(val, Quantity):
            return val.to_string()
        if isinstance(val, type):
            return val.__name__
        if isinstance(val, (list, tuple, set)):
            return [check_serialize(serialize, v) for v in val]
        if isinstance(val, dict):
            return {k: check_serialize(serialize, v) for k, v in val.items()}
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

def listify(x, d={}, sep=',', NoneReturn=[], dtype=None):
    """
    Convert input to list in creative ways.  (Taken from odsutils.ods_tools.listify)

    Parameters
    ----------
    x : *
        Input to listify
    d : dict
        Default/other values for conversion.
    sep : str
        Separator to use if str
    NoneReturn : *
        Return if input is None
    dtype : type or None
        Type of list elements to return (if None, no conversion)
    
    Return
    ------
    list : converted x (or d[x])

    """
    if x is None:
        return NoneReturn
    if isinstance(x, list):
        this = x
    elif isinstance(x, str) and x in d:
        this = d[x]
    elif isinstance(x, str):
        if sep == 'auto':
            sep = ','
        this = [_s.strip() for _s in x.split(sep)]
    else:
        this = [x]
    if dtype is None:
        return this
    try:
        return [dtype(z) for z in this]
    except Exception:
        return this