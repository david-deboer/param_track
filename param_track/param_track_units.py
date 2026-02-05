from astropy import units as u
from param_track.param_track_timetools import TUNITS, interpret_date
from .param_track_support import listify


builtin_units = {
    'float': float,  # Technically not a unit, but included for completeness
    'int': int,  # Technically not a unit, but included for completeness
    'str': str,  # Technically not a unit, but included for completeness
    'bool': bool, # Technically not a unit, but included for completeness
    'complex': complex  # Technically not a unit, but included for completeness
}
time_units = {  # Also, technically not a unit
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
    'kg': 'astropy:mass'
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

    def handle_units(self, unit_handler):
        if isinstance(unit_handler, dict):
            self.use_units = True
            self._parse_unit_handler(unit_handler)
        elif isinstance(unit_handler, (bool, type(None))):
            self.use_units = bool(unit_handler)  # This will toggle but not delete existing handler
        else:
            print("param_track_units warning: unit_handler must be a dict, bool, or None.")
            self.use_units = False

    def _parse_unit_handler(self, unit_handler):
        """
        This checks the provided unit_handler dict for valid units and ignores invalid ones.

        Valid are those in builtin_units, time_units, timedelta_units, and astropy_units or in built_units values (i.e. actual types).
        
        """
        print('currently this flushes the old unit handler and creates a new one, maybe update?')
        _uh = {}
        for key, val in unit_handler.items():
            if val in all_units:
                _uh[key] = val
            else:
                for kk, vv in builtin_units.items():
                    if val == vv:
                        _uh[key] = kk
                        break
        self.unit_handler = _uh

    def setattr(self, obj, key, val):
        self.unit = None
        if not self.use_units:
            self.val = val
            setattr(obj, key, val)
        elif not isinstance(self.unit_handler, dict):
            self.val = val
            setattr(obj, key, val)
            print("param_track_units warning: unit_handler must be a dict -- ignoring units but setting value.")
        elif key in self.unit_handler:
            self.unit = self.unit_handler[key]
            self.val = self._make_quantity(val, self.unit)
            setattr(obj, key, self.val)

    def _make_quantity(self, val, unit):
        if unit == '*':
            return val
        is_list = False
        if unit[0] == '[':
            is_list = True
            unit = unit.strip('[]')
        if unit in builtin_units:
            try:
                if is_list:
                    return listify(val, dtype=builtin_units[unit])
                else:
                    return builtin_units[unit](val)
            except:
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
                print(f"param_track_units warning: could not convert value <{val}> to Quantity with unit <{unit}>.")
            return val

        print(f"param_track_units warning: could not convert value <{val}> to Quantity with unit <{unit}>.")
        return val

# THIS STUFF IS PASTED IN FROM ON_TRACK.PY:
#         newargs = {}
#         for key, value in kwargs.items():
#             dtype_info = self.track_field_structure['fields'][key]['type']
#             if self.units is not None and key in self.units:
#                     if self.units[key] == 'Time':
#                         value = ttools.interpret_date(value, fmt='Time')
#                         continue
#                     if self.units[key] in ttools.TUNITS:
#                         value *= (ttools.TUNITS[self.units[key]] * u.s)
#                         continue
#                     unit_is_quantity = True                    
#                     try:
#                         _ = 1.0 * u.Unit(self.units[key].strip('[]'))
#                     except:
#                         unit_is_quantity = False
#                     if unit_is_quantity:
#                         if self.units[key][0] == '[':
#                             value = u.Quantity(listify(value, dtype='float'), self.units[key].strip('[]'))
#                         else:
#                             value = u.Quantity(float(value), self.units[key])
#                     else:
#                         try:
#                             value = eval(self.units[key])(value)
#                         except:
#                             print(f"Could not convert {key} with unit {self.units[key]} and value {value}")
#             elif key in self.field_types['list']:
#                 if len(dtype_info) == 2:
#                     ind = 0 if dtype_info[1] == 'list' else 1
#                     newargs[key] = listify(value, dtype=dtype_info[ind])
#                 else:
#                     newargs[key] = listify(value)
#             elif len(dtype_info) == 1:
#                 if dtype_info[0] in ['Time', 'TimeDelta']:
#                     newargs[key] = ttools.interpret_date(value, fmt=dtype_info[0])
#                 elif key in self.field_types['*']:
#                     newargs[key] = value
#                 else:
#                     newargs[key] = eval(dtype_info[0])(value)
#             else:
#                 newargs[key] = value