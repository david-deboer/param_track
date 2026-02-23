# -*- mode: python; coding: utf-8 -*-
# Copyright 2025 David R DeBoer
# Licensed under the MIT license. See LICENSE file in the project root for details.


"""General simple parameter tracking module."""
from .param_track_support import ParameterTrackError, Log, typemsg, check_serialize
from .param_track_support import typename as tn
from copy import copy
from param_track import param_track_units

__ptu__ = param_track_units.Units()
__ptu__.__ptuaccess__log__()
__log__ = Log(__name__)


class Parameters:
    """
    General parameter tracking class to handle groups of parameters as a class with some minor checking of
    existence and of type.  See README.md

    """
    _internal_only_ptvar = {'ptnote', 'ptstrict', 'pterr', 'ptverbose', 'pttype', 'pttypeerr', 'ptsetunits',
                            '_internal_pardict'}
    _internal_only_ptdef = {'ptset', '_pt_set', 'ptinit', 'ptadd', 'ptsu', 'ptfrom',
                            'ptget', 'ptdel', 'ptshow', 'ptlog', 'ptto', 'pt_to_dict'}
    ptnote = 'Uninitialized parameter tracking class'
    ptstrict = False
    pterr = False
    ptverbose = True
    pttype = False
    pttypeerr = False
    ptsetunits = False
    _internal_pardict = {}

    def __init__(self, ptnote='Parameter tracking class', ptinit=None,
                 ptstrict=True, pterr=False, ptverbose=True, pttype=False, pttypeerr=False, ptsetunits=False,
                 **kwargs):
        """
        General parameter tracking class to keep track of groups of parameters within a class with
        some minor checking and viewing.

        See README.md for details.

        Actions are tracked via the Log object.
        
        Parameters
        ----------
        ptnote : str
            Note to describe the parameter tracking instance, used in ptshow
        ptinit : str or csv-list or None
            if not None, calls ptinit with a default value of None
        ptstrict : bool
            Flag to make parameter setting strict (i.e. error or warn on unknown parameters)
        pterr : bool
            Flag to make parameter setting raise ParameterTrackError on unknown parameters in strict mode
        ptverbose : bool
            Flag to make parameter setting verbose
        pttype : bool
            Flag to check parameter reset type -- only used in ptset and only writes to log.
            Checks relative to the initial type set or when ptadd/ptsu was used.
        pttypeerr : bool
            Flag to make parameter setting raise ParameterTrackError on type change or just notice -- only used in ptset.
        ptsetunits : bool or unit_handler
            Flag to set units when setting parameters (see param_track_units.py for details)
        kwargs : key, value pairs
            Initial parameters to set (if any)
            
        Methods
        -------
        ptset : set parameters (with checking)
        ptinit : initialize parameters from a list of keys to default value or with a file ...
        ptadd : add new parameters (only way to add new parameters in strict mode)
        ptfrom : set parameters from a file (CSV, JSON or YAML formats supported, set by filename extension)
        ptget : get parameter value
        ptdel : delete parameters
        ptsu : set parameters silently and can change internal parameters
        ptshow : show current parameters being tracked
        ptlog : show or return the Log object
        ptto : write parameters to a file (CSV, JSON or YAML formats supported, set by filename extension)
        pt_to_dict : return current parameters as a dictionary (or serialized form), plus options for types or internal parameters

        """
        from . import __version__
        __log__.post(f"Parameter Track:  version {__version__}", silent=True)
        __log__.post(f"Parameters tracking: {ptnote}.", silent=True)
        self.ptsu(ptnote=ptnote, ptinit=ptinit, ptstrict=ptstrict, pterr=pterr, ptverbose=ptverbose,
                  pttype=pttype, pttypeerr=pttypeerr, ptsetunits=ptsetunits, **kwargs)

    def __repr__(self):
        return self.ptshow(return_only=True)
    
    def __ptaccess__ptu__(self):
        """Allow a Class copy of the param_track_units Class -- generally for debugging."""
        self.ptu = __ptu__

    def __ptaccess__log__(self):
        """Allow a Class copy of the Log class -- generally for debugging.  Use ptlog to view."""
        self.log = __log__

    def ptinit(self, ptinit=[], default=None, **kwargs):
        """
        Initialize parameters per the following:
            - if the input variable 'ptinit' is a str, it check if it is a file[:key] and will use the file, otherwise it willa assume a csv-list
            - if 'ptinit' is a list (or a str interpreted as a list per above), it will set that to the default value
            - if 'ptinit' is a dict, it will set via the key-value pairs -- note that this is there for convenience, generally use ptadd or ptsu for this
            - if 'ptinit' is None, nothing happens (helps with __init__)
        The variables in 'ptinit' (and kwargs) are then set via the ptsu method

        if a filename or dict are given, the 'default' is ignored (i.e. values used from the file) - see README.md for file formats.

        kwargs are included for completeness and flexibility

        If the default value is not None, then the parameters will be initialized to this value and the type set to the type of this value.
        If the default value is None, then the parameters will be initialized to None and the type will be set None as a marker for
        future type checking.

        Parameters
        ----------
        ptinit : list of str, csv-list, str or None
            List of keys to initialize or filename[:key].  If a filename is given, then parameters will be initialized from the file
            (CSV, JSON, YAML, NPZ/Y formats supported, set by filename extension).  If a key is given after a colon, then only that key will be used
            from the file (e.g. for YAML files with multiple keys).  See README.md for file format.
        default : any
            Default value to set for each parameter (default is None), ignored if file is used
        kwargs : key, value pairs
            Initial parameters to set (if any)

        """
        if ptinit is None:
            return
        if isinstance(ptinit, str):
            inp = ptinit.split(':')
            from os.path import isfile
            if isfile(inp[0]):
                use_key = inp[1] if len(inp) > 1 else None
                self.ptfrom(inp[0], use_key=use_key, use_option='su', as_row=False)
                return
            else:
               data = {x.strip(): default for x in ptinit.split(',')}
        elif isinstance(ptinit, list):
            data = {key: default for key in ptinit}
        elif isinstance(ptinit, dict):
            data = ptinit
        else:
            __log__.post(f"Parameter list for initialization must be a string, list, or dict -- "
                         f"got {ptinit} ({tn(ptinit)})", silent=False)  # always print 'ignored'
            return
        __log__.post(f"Initializing parameters from {ptinit}", silent=not self.ptverbose)
        data.update(kwargs)
        self.ptsu(**data)

    def ptset(self, **kwargs):
        """
        Set parameters -- this is the wrapper around the "workhorse" method _pt_set.

        If parameter tracking is used as a parent Class, then this can be redefined for custom behavior, then
        call the _pt_set method to do the actual setting.  In a parent class, one could call this function 'set'
        or 'update'.
        
        See the method _pt_set for the behavior.  The methods ptadd and ptsu provide for other ways to intereact
        with the parameters.
        
        ptinit is also available for initialization (meant to be called once on startup).
        ptfrom will add variables from a file

        """
        self._pt_set(**kwargs)

    def _pt_set(self, **kwargs):
        """
        This is the standard way to set parameters (see also ptadd and ptsu).

        Behavior:
        - if the parameter is one of the internal ones (_internal_only_ptvar, _internal_only_ptdef) the request is IGNORED
        - if the parameter already exists, the value is set, followed by type-checking per below:
            - if the value is None, type checking is IGNORED
            - if the preexisting type is None, then the type is reset silently to the type of value
            - if the type of the value and the preexisting type match, nothing else happens
            - if they don't match, what happens depends on the internal variables pttype and pttypeerr
                - if pttype is False, the type just gets reset to the value type
                - if pttype is True and 
                    - if pttypeerr is True, a ParameterTrackError is raised
                    - if pttypeerr is False, it gives a warning and does NOT reset the type
        - if the parameter doesn't already exist, what happens depends on the value of ptstrict
            - if ptstrict is True, what happens depends on the value of pterr
                - if pterr is True, a ParameterTrackError is raised
                - if pterr is False, a warning is printed and the request is IGNORED
            if ptstrict is False, the value and type are set

        """
        for key, val in kwargs.items():
            if key in self._internal_only_ptvar or key in self._internal_only_ptdef:
                __log__.post(f"Attempt to set internal parameter/method '{key}' -- ignored, try method 'ptsu'.", silent=False)  # always print 'ignored'
            elif key in self._internal_pardict:  # It has a history, so set and then check type.
                __ptu__.setattr(self, key, val)
                __log__.post(f"Setting existing parameter {__ptu__.msg}", silent=not self.ptverbose)
                if val is None:  # A value of None ignores types
                    continue
                elif self._internal_pardict[key] is None:  # None always gets updated type
                    self._internal_pardict[key] = copy(__ptu__.type)
                elif type(val) != self._internal_pardict[key]:  # Types don't match
                    if self.pttype:  # ... and I care about types.
                        if self.pttypeerr:
                            raise ParameterTrackError(typemsg(key, self._internal_pardict[key], __ptu__.tn, 'raise'))
                        else:
                            __log__.post(typemsg(key, self._internal_pardict[key], __ptu__.tn, 'retain'), silent=False)  # since I care about types
                    else:  # ... but I don't care about types.
                        self._internal_pardict[key] = copy(__ptu__.type)  # so I'll just reset it to new type
                        __log__.post(typemsg(key, self._internal_pardict[key], __ptu__.tn, 'reset'), silent=not self.ptverbose)
            elif self.ptstrict:  # Key is unknown and strict mode is on.
                if self.pterr:
                    raise ParameterTrackError(f"Unknown parameter '{key}' in strict mode.")
                else:
                    __log__.post(f"Unknown parameter '{key}' in strict mode -- ignored.  Use 'ptadd' to add new parameters.", silent=False)  # always print 'ignored'
            else:  # New parameter and not in strict mode so just set it.
                __ptu__.setattr(self, key, val)
                self._internal_pardict[key] = copy(__ptu__.type)
                __log__.post(f"Setting new parameter {__ptu__.msg}", silent=not self.ptverbose)

    def ptadd(self, **kwargs):
        """
        Add new parameters to the parameter tracking -- used to add new parameters if ptstrict is True.

        It also acts like a "replace" method -- the new one is changed in both value and type. The behavior is to always change the
        value and type (except for the internal variables in _internal_only_ptvar, _internal_only_ptdef, which are IGNORED)

        Parameters
        ----------
        kwargs : key, value pairs
            Parameters to add/replace

        """
        for key, val in kwargs.items():
            if key in self._internal_only_ptvar or key in self._internal_only_ptdef:  # Internal only, so ignore.
                __log__.post(f"Attempt to modify internal parameter/method '{key}' -- ignored, try 'ptsu'.", silent=False)  # always print 'ignored'
            else:
                action = "Replacing" if key in self._internal_pardict else "Adding"
                __ptu__.setattr(self, key, val)
                __log__.post(f"{action} parameter {__ptu__.msg}", silent=not self.ptverbose)
                self._internal_pardict[key] = copy(__ptu__.type)

    def ptsu(self, **kwargs):
        """
        This is the only way to set internal parameters.  Other parameters are handled using ptadd.

        The order is ptverbose, ptsetunits, ptnote, ptinit then others in order provided.

        Parameters
        ----------
        kwargs : key, value pairs
            Parameters to set in superuser mode

        """
        if 'ptverbose' in kwargs:
            self.ptverbose = bool(kwargs.pop('ptverbose'))
            __log__.post(f"su: Setting internal parameter 'ptverbose' to <{self.ptverbose}>", silent=not self.ptverbose)
        if 'ptsetunits' in kwargs:
            __ptu__.handle_units(kwargs.pop('ptsetunits'))
            self.ptsetunits = __ptu__.use_units
            __log__.post(f"su: Setting internal parameter 'ptsetunits' to <{self.ptsetunits}>", silent=not self.ptverbose)
        if 'ptnote' in kwargs:  # always allow ptnote to be set
            self.ptnote = kwargs.pop('ptnote')
            __log__.post(f"su: Setting internal parameter 'ptnote' to <{self.ptnote}>", silent=not self.ptverbose)
        if 'ptinit' in kwargs:
            ptinit = kwargs.pop('ptinit')
            self.ptinit(ptinit=ptinit)

        for key, val in kwargs.items():
            if key in self._internal_only_ptdef:  # Internal method, so ignore.
                __log__.post(f"su: Attempt to set internal method '{key}' -- ignored.", silent=False)  # always print 'ignored'
            elif key in self._internal_only_ptvar: # Internal variable, so only allow bools to be set.
                if key[0] == '_':  # private internal variable, so ignore
                    __log__.post(f"su: Attempt to set internal parameter '{key}' -- ignored.", silent=False)  # always print 'ignored'
                else:  # public internal variable, so only allow bools to be set
                    if type(val) != bool:
                        __log__.post(f"su: Internal parameter '{key}' must be bool -- ignored.", silent=False)  # always print 'ignored'
                    else:
                        setattr(self, key, val)
                        __log__.post(f"su: Setting internal parameter '{key}' to <{val}>", silent=not self.ptverbose)
            else:  # Add it same as ptadd
                self.ptadd(**{key: val})

    def ptget(self, key, default=ParameterTrackError):
        """
        Get the value of a parameter.  It will error if not present unless a default value is provided.

        Parameters
        ----------
        key : str
            Parameter name to get
        default : any
            Default value to return if parameter not found, if not provided, then raise ParameterTrackError
        
        """
        if key in self._internal_pardict or key in self._internal_only_ptvar:
            return getattr(self, key)
        if default is ParameterTrackError:
            raise ParameterTrackError(f"Parameter '{key}' not found.")
        return default

    def ptdel(self, *args):
        """
        Delete parameters from parameter tracking.

        Parameters
        ----------
        args : list of str or list of list of str
            Parameter names to delete

        """
        for kval in args:
            if isinstance(kval, str):
                keys = [x.strip() for x in kval.split(',')]
            elif isinstance(kval, list):
                keys = kval
            else:
                __log__.post(f"Parameter names to delete must be strings or lists, got <{kval}> ({tn(kval)})", silent=False)  # always print 'ignored'
                continue
            for k in keys:
                if k in self._internal_only_ptvar or k in self._internal_only_ptdef:
                    __log__.post(f"Attempt to delete internal parameter/method '{k}' -- ignored.", silent=False)  # always print 'ignored'
                elif k in self._internal_pardict:
                    __log__.post(f"Deleted parameter '{k}' which had value <{getattr(self, k)}>", silent=not self.ptverbose)
                    delattr(self, k)
                    del self._internal_pardict[k]
                else:
                    __log__.post(f"Attempt to delete unknown parameter '{k}' -- ignored.", silent=False)  # always print 'ignored'

    def ptshow(self, show_all=False, return_only=False, include_par=None):
        """
        Show the current parameters being tracked (and optionally their types and internal parameters).

        Parameters
        ----------
        show_all : bool
            If True, then show all parameters, types and internal parameters.
            If False, then only show parameters (no types or internal parameters).
        return_only : bool
            If True, then return the string instead of printing it (for __repr__ method)
            If False, then print the string representation
        include_par : list of str or None
            If not None, then only include these parameters in the output

        Returns
        -------
        if 'return_only' : str
            string representation of the current parameters

        """
        show = f"Parameter Tracking: {self.ptnote}\n"
        show += '-'*(len(show)-1) + "\n"
        show += self.pt_to_dict(serialize='yaml', include_par=include_par, what_to_dict="parameters")
        if show_all:
            show += "\nParameter types:\n"
            show += '-'*len("Parameter types:") + "\n"
            show += self.pt_to_dict(serialize='yaml', include_par=include_par, what_to_dict="types")
            show += "\nInternal parameters:\n"
            show += '-'*len("Internal parameters:") + "\n"
            show += self.pt_to_dict(serialize='yaml', what_to_dict="internal")
        if return_only:
            return show
        __log__.post(show, silent=False)
    
    def ptlog(self, action='show', search=None):
        """
        Do stuff with the Log object.

        Note, to have access to the Log Instance, use self.__ptaccess__log__()

        Parameters
        ----------
        action : str
            'show' : print the Log to stdout
            'clear' : clear the Log entries
            'dump' : dump the Log to a file 'param_track_log.txt'

        """
        if action == 'show':
            __log__.show(search=search)
            print('===')
            __ptu__.log.show(search=search)
        elif action == 'clear':
            __log__.log = []
            __ptu__.log.log = []
        elif action == 'dump':
            __log__.post("Dumping log to 'param_track_log.txt'/'param_track_units_log.txt'", silent=False)
            with open('param_track_log.txt', 'w') as fp:
                __log__.show(file=fp, search=search)
            with open('param_track_units_log.txt', 'w') as fp:
                __ptu__.log.show(file=fp, search=search)
        else:
            __log__.post(f"Unknown 'ptlog' action '{action}'.", silent=False)

    def pt_to_dict(self, serialize=None, include_par=None, what_to_dict="parameters"):
        """
        Return the current parameters as a dictionary.

        Parameters
        ----------
        serialize : str or None
            If 'json', then return JSON serialized string
            If 'yaml', then return YAML serialized string
            If 'pickle', then return pickle serialized bytes
            If None, then return dictionary
        include_par : csv-list, list of str or None
            If not None, then only include these parameters in the output dictionary
        what_to_dict : one of 'parameters', 'types', 'internal' (first letter is all that is needed)
            return requested set

        Returns
        -------
        dict, str, or bytes
            Dictionary or serialized form of current parameters

        """
        rec = {}
        if what_to_dict[0].lower() == "i":  # internal parameters only
            include_par = [x for x in self._internal_only_ptvar if x[0]!= '_']
        else: # normal parameters or types
            include_par = list(self._internal_pardict.keys()) if include_par is None else include_par
            if isinstance(include_par, str):
                include_par = [x.strip() for x in include_par.split(',')]
        for key in include_par:
            if key not in self._internal_pardict and key not in self._internal_only_ptvar:  # if key is unknown, ignore it and print warning
                __log__.post(f"Parameter '{key}' not found in parameter tracking -- ignored in output.", silent=False)  # always print 'ignored'
                continue
            val = self._internal_pardict.get(key) if what_to_dict[0].lower() == 't' else self.ptget(key)
            rec[key] = check_serialize(serialize, val)
        if serialize == 'json':
            import json
            return json.dumps(rec, indent=4)
        elif serialize == 'yaml':
            import yaml
            return yaml.dump(rec)
        elif serialize == 'pickle':
            import pickle
            return pickle.dumps(rec)
        return rec
    
    def ptfrom(self, filename, use_key=None, use_option='add', as_row=False):
        """
        Set parameters from a file, depending on the format of the file.

        Currently csv, json and yaml formats are supported.
    
        Parameters
        ----------
        filename : str
            Path to the file containing parameters
        use_key : str or None
            If not None, then use this key to get the parameters from the file
        use_option : str
            If 'add', then use ptadd to add parameters
            If 'set', then use ptset to set parameters
            If 'su', then use ptsu to set parameters and units
        as_row : False or int (CSV format only)
            If int, then read the CSV from row 'as_row' instead of key-value pairs
            and first line is header (works since row 0 is header)

        """
        from param_track.param_track_io import from_file
        __log__.post(f"{'Adding' if use_option == 'add' else 'Setting'} parameters from {filename}{' with key ' + use_key if use_key else ''}", silent=not self.ptverbose)
        if as_row:
            if filename.endswith('.csv'):
                __log__.post("Using 'as_row' option.", silent=self.ptverbose)
            else:
                __log__.post(f"Warning: 'as_row' option is only applicable for CSV files, ignoring 'as_row' for {filename}", silent=False)  # always print 'ignored'
        data, unit_handler = from_file(filename, use_key=use_key, as_row=as_row)
        if isinstance(unit_handler, dict) and len(unit_handler) > 0:
            self.ptsu(ptsetunits=unit_handler)
        if use_option == 'add':
            self.ptadd(**data)
        elif use_option == 'set':
            self.ptset(**data)
        elif use_option == 'su':
            self.ptsu(**data)
        else:
            __log__.post(f"Unknown option {use_option} (should be 'set', 'add' or 'su')", silent=False)

    def ptto(self, filename, include_par=None, as_row=False):
        """
        Write parameters to a file.  TBD support yaml, json, yaml, npy/z

        If include_par == 'unit_handler' save the unit_handler to filename (json or yaml)

        """
        if include_par == 'unit_handler':
            __ptu__.save_unit_handler(filename=filename)
        else:
            from param_track.param_track_io import to_file
            __log__.post(f"Writing to file {filename}")
            to_file(self, filename=filename, include_par=include_par, as_row=as_row)