from astropy import units as u
from param_track.param_track_timetools import TUNITS, interpret_date
from .param_track_support import listify, typename
from copy import copy


builtin_units = {  # Not units, but included
    'float': float,
    'int': int,
    'str': str,
    'bool': bool,
    'complex': complex
}
time_units = {  # Also, not units
    'Time': 'Time',
    'astropy:time': 'Time',
    'datetime': 'datetime'
}
timedelta_units = TUNITS.copy()

astropy_units = {
    'm': 'astropy:length',
    'deg': 'astropy:angle',
    'Hz': 'astropy:frequency',
    'm/s': 'astropy:velocity',
    'kg': 'astropy:mass',
    'hourangle': 'astropy:angle',
    'rad': 'astropy:angle',
    'radian': 'astropy:angle'
}
astropy_prefixes = ['T', 'G', 'M', 'k', 'h', 'da', 'd', 'c', 'm', 'u', 'n', 'p', 'f']

for key, val in astropy_units.copy().items():
    for prefix in astropy_prefixes:
        new_key = prefix + key
        astropy_units[new_key] = val

all_units = list(builtin_units.keys()) + list(time_units.keys()) + \
            list(timedelta_units.keys()) + list(astropy_units.keys())

class Units:
    def __init__(self):
        self.use_units = False
        self.unit_handler = None
        self.valid_unit_handler = False

    def handle_units(self, unit_handler, action='reset'):
        """
        Parameters
        ----------
        unit_handler : dict or bool or None
            If dict, then this is the unit handler to be used. Keys are parameter names, values are unit strings.
            If bool/None/int, then this sets the use of units but does not change the existing unit handler.
            If other, then this turns off the use of units but does not change the existing unit handler.
        action : str
            If unit_handler is a dict, then this determines what to do with existing parameters
            'reset' will reset the existing unit handler.
            'update' will update the existing unit handler.

        """
        if isinstance(unit_handler, dict):
            self.use_units = True
            self._parse_unit_handler(unit_handler, action=action)
        elif isinstance(unit_handler, (bool, type(None), int)):
            self.use_units = bool(unit_handler)  # This will toggle but not delete existing handler
        else:
            self.use_units = False

    def _parse_unit_handler(self, unit_handler, action='reset'):
        """
        This checks the provided unit_handler dict for valid units and ignores invalid ones.

        Valid are those in builtin_units, time_units, timedelta_units, and astropy_units or in built_units values (i.e. actual types).
        
        """
        _uh = {}
        for key, val in unit_handler.items():
            is_list = True if val[0] == '[' else False
            val = val.strip('[]') if isinstance(val, str) else val
            if val in all_units:
                _uh[key] = f"[{val}]" if is_list else val
            else:
                for kk, vv in builtin_units.items():
                    if val == vv:
                        _uh[key] = f"[{kk}]" if is_list else kk
                        break
        if action == 'reset':
            self.unit_handler = _uh
        elif action == 'update':
            self.unit_handler.update(_uh)
        else:
            raise ValueError(f"Invalid action for unit handler parsing: {action}. Must be 'reset' or 'update'.")
        self.valid_unit_handler = True

    def setattr(self, obj, key, val):
        self.unit = None
        self.oldval = copy(getattr(obj, key, None))
        self.oldtype = obj._internal_pardict.get(key, None)
        if not self.use_units:
            self.val = val
        elif not self.valid_unit_handler:
            self.val = val
        elif key in self.unit_handler:
            self.unit = self.unit_handler[key]
            self.val = self._make_quantity(val, self.unit)
        else:
            self.val = val
        self.type = None if self.val is None else type(self.val)
        self.tn = 'None' if self.type is None else typename(self.val)
        setattr(obj, key, self.val)
        self.msg = f"'{key}' to <{self.val}> ({self.tn})"
        if self.oldval is not None:
            self.msg += f" [was <{self.oldval}>"
            if self.oldtype is not None:
                self.msg += f" ({typename(self.oldtype)})"
            self.msg += "]"

    def _make_quantity(self, val, unit):
        if unit == '*' or not isinstance(unit, (str, type)):
            return val
        is_list = False
        if str(unit[0]) == '[' or isinstance(val, list):
            is_list = True
            unit = unit.strip('[]')
        if unit in builtin_units:
            try:
                if is_list:
                    return listify(val, dtype=builtin_units[unit])
                else:
                    return builtin_units[unit](val)
            except:
                if val is not None:
                    print(f"param_track_units warning: could not convert value <{val}> to type <{unit}>.")
                return val
        if unit in time_units or unit in timedelta_units:
            try:
                if is_list:
                    val = [interpret_date(x, fmt=unit) for x in listify(val)]
                    return val
                else:
                    return interpret_date(val, fmt=unit)
            except:
                if val is not None:
                    print(f"param_track_units warning: could not convert value <{val}> to Time.")
                    print("Returning original value...???")
                return val
        if unit in astropy_units:
            try:
                if is_list:
                    val = u.Quantity(listify(val), unit)
                else:
                    val = u.Quantity(val, unit)
            except:
                if val is not None:
                    print(f"param_track_units warning: could not convert value <{val}> to Quantity with unit <{unit}>.")
            return val

        if val is not None:
            print(f"param_track_units warning: could not convert value <{val}> to Quantity with unit <{unit}>.")
        return val