from astropy import units as u
from param_track.param_track_timetools import TUNITS, interpret_date
from .param_track_support import Log
from .param_track_support import listify, typename
from copy import copy


__log__ = Log(__name__)


builtin_units = {  # Not units, but included
    float: float,
    'float': float,
    int: int,
    'int': int,
    str: str,
    'str': str,
    bool: bool,
    'bool': bool,
    dict: dict,
    'dict': dict,
    list: list,
    'list': list,
    set: set,
    'set': set,
    complex: complex,
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
            list(timedelta_units.keys()) + list(astropy_units.keys()) + \
            ['*']

class Units:
    def __init__(self):
        self.use_units = False
        self.unit_handler = None
        self.valid_unit_handler = False

    def __ptuaccess__log__(self):
        self.log = __log__

    def handle_units(self, unit_handler, action='reset'):
        """
        This sets using units and the unit_handler.

        If the supplied unit_handler is a bool, None or int it will evaluate as a bool to set using units on or off.

        The supplied unit_handler is handled in the _parse_unit_handler method.
        
        If the unit_handler is a dict, it will set using units to on, and make the Class unit_handler:
            The unit_handler is a dict with keys the parameter name and the value the unit/type to be used.
            The unit/type is a str or instance type or dict that must be one of:
                an '*' to indicate it can be any thing (so bascially ignore)
                in the 'all_units' list above
                a list by one or two methods (list elements must be of the same unit/type):
                    if a str, enclose a unit/type str in square brackets e.g. '[kg]' or '[float]' or '[*]'
                    if a str, be a string with one entry e.g. ['kg'] or [float] or ['*']
                a set with same format as list using curly brackets
                a dict already in the full unit_handler format
        If the unit_handler is a str, it will check for a file of that name and load if found.

        Internally, the unit_handler is a dict with key of the parameter name, but the val is a dict:
            islist: bool
            isset: bool
            type: one of the types in 'all_units' above
        This is built in _parse_unit_handler

        Parameters
        ----------
        unit_handler : dict or bool or None
            If dict, then this is the unit handler to be used. Keys are parameter names, values are unit strings.
            If bool/None/int, then this sets the use_units as bool(.) but does not change the existing unit handler.
        action : str
            If unit_handler is a dict, then this determines what to do with existing parameters
                'reset' will reset the existing unit handler.
                'update' will update the existing unit handler.
                 
        """
        if isinstance(unit_handler, dict):
            self.use_units = True
            self._parse_unit_handler(unit_handler, action=action)
        elif isinstance(unit_handler, str):
            from os.path import isfile
            if isfile(unit_handler):
                self.use_units = True
                self.load_unit_handler(filename=unit_handler, action=action)
            else:
                raise FileNotFoundError(unit_handler)
        elif isinstance(unit_handler, (bool, type(None), int)):
            self.use_units = bool(unit_handler)  # This will toggle but not delete existing handler
        else:
            raise ValueError(f"Invalid unit_handler input {unit_handler}")

    def _parse_unit_handler(self, unit_handler, action='reset'):
        """
        This checks the provided unit_handler dict for valid units and ignores invalid ones.

        Valid are those in builtin_units, time_units, timedelta_units, and astropy_units or in built_units values (i.e. actual types).
        
        """
        if action not in ['reset', 'update']:
            raise ValueError(f"Invalid action for unit handler parsing: {action}. Must be 'reset' or 'update'.")
        _uh = {}
        for key, val in unit_handler.items():
            _uh[key] = {'islist': False, 'isset': False, 'type': None}
            if isinstance(val, list):
                _uh[key]['islist'] = True
                _uh[key]['type'] = val[0]
            elif isinstance(val, set):
                _uh[key]['isset'] = True
                _uh[key]['type'] = val[0]
            elif isinstance(val, str):
                if val[0] == '[':
                    _uh[key]['islist'] = True
                elif val[0] == '{':
                    _uh[key]['isset'] = True
                _uh[key]['type'] = val.strip('[]').strip('{}')
            elif isinstance(val, type):
                _uh[key]['type'] = val
            elif isinstance(val, dict):
                if 'islist' in val and 'isset' in val and 'type' in val:
                    _uh = copy(val)
                else:
                    raise ValueError("A unit_handler dict must be in full format")
            else:
                raise ValueError(f"Invalid unit/type {val}")
            if _uh[key]['type'] not in all_units:
                raise ValueError(f"{_uh[key]['type']} not valid")
        if action == 'reset':
            self.unit_handler = _uh
        elif action == 'update':
            self.unit_handler.update(_uh)
        self.valid_unit_handler = True

    def setattr(self, obj, key, val):
        self.oldval = copy(getattr(obj, key, None))
        self.oldtype = obj._internal_pardict.get(key, None)
        if not self.use_units:
            self.val = val
        elif not self.valid_unit_handler:
            self.val = val
        elif key in self.unit_handler:
            self._make_quantity(key, val)
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

    def _make_quantity(self, key, val):
        unit = self.unit_handler[key]['type']
        if unit is None or unit == '*':
            self.val = val
        elif unit in builtin_units:
            try:
                if self.unit_handler[key]['islist'] or self.unit_handler[key]['isset']:
                    val = listify(val, dtype=builtin_units[unit])
                    self.val = set(self.val) if self.unit_handler[key]['isset'] else val
                else:
                    self.val = builtin_units[unit](val)
            except:
                if val is not None:
                    __log__.post(f"param_track_units warning: could not convert value <{val}> to type <{unit}>.", silent=False)
                self.val = val
        elif unit in time_units or unit in timedelta_units:
            try:
                if self.unit_handler[key]['islist'] or self.unit_handler[key]['isset']:
                    val = [interpret_date(x, fmt=unit) for x in listify(val)]
                    self.val = set(val) if self.unit_handler[key]['isset'] else val
                else:
                    self.val = interpret_date(val, fmt=unit)
            except:
                if val is not None:
                    __log__.post(f"param_track_units warning: could not convert value <{val}> to Time.", silent=False)
                    __log__.post("Returning original value...???", silent=False)
                self.val = val
        elif unit in astropy_units:
            try:
                if self.unit_handler[key]['islist'] or self.unit_handler[key]['isset']:
                    val = u.Quantity(listify(val), unit)
                    self.val = set(val) if self.unit_handler[key]['isset'] else val
                else:
                    self.val = u.Quantity(val, unit)
            except:
                if val is not None:
                    __log__.post(f"param_track_units warning: could not convert value <{val}> to Quantity with unit <{unit}>.", silent=False)
                self.val = val
        elif val is not None:
            __log__.post(f"param_track_units warning: could not convert value <{val}> to Quantity with unit <{unit}>.", silent=False)
            self.val = val

    def save_unit_handler(self, filename):
        """
        Write the unit_handler to filename.
        
        This will likely be rare, since generally done from a ptinit file.

        """
        if filename.endswith('.json'):
            import json
            with open(filename, 'w') as fp:
                json.dump(self.unit_handler, fp)
        elif filename.endswith('.yaml') or filename.endswith('yml'):
            import yaml
            with open(filename, 'w') as fp:
                yaml.dump(self.unit_handler, fp)

    def load_unit_handler(self, filename, action='update'):
        """
        Load a unit_hander from filename.

        This will likely be rare, since gnerally done from a ptinit file.

        """
        if filename.endswith('.json'):
            import json
            with open(filename, 'r') as fp:
                unit_handler = json.load(fp)
        elif filename.endswith('.yaml') or filename.endswith('yml'):
            import yaml
            with open(filename, 'r') as fp:
                unit_handler = yaml.safe_load(fp)
        self._parse_unit_handler(unit_handler=unit_handler, action=action)