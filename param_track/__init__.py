# -*- mode: python; coding: utf-8 -*-
# Copyright 2025 David R DeBoer
# Licensed under the MIT license. See LICENSE file in the project root for details.


"""A simple parameter tracking class"""

from .param_track import Parameters
from importlib.metadata import version
__version__ = version('param_track')
from datetime import datetime

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

def typemsg(key, oldtype, newtype, action):
    msg = f"Parameter types don't match for '{key}': <old: {oldtype.__name__}> vs <new: {newtype.__name__}>"
    if action == 'retain':
        msg += f" -- retaining <{oldtype.__name__}>."
    elif action == 'reset':
        msg += f" -- resetting to <{newtype.__name__}>."
    return msg