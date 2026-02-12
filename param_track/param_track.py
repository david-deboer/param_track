# -*- mode: python; coding: utf-8 -*-
# Copyright 2025 David R DeBoer
# Licensed under the MIT license. See LICENSE file in the project root for details.


"""General simple parameter tracking module."""
from param_track.param_track_io import from_file
from .param_track_support import ParameterTrackError, Log, typemsg, check_serialize
from .param_track_support import typename as tn
from copy import copy
from param_track import param_track_units

__ptu__ = param_track_units.Units()
__log__ = Log()


class Parameters:
    """
    General parameter tracking class to keep track of groups of parameters within a class with 
    some minor checking and viewing.

    """
    _internal_only_ptvar = {'ptnote', 'ptstrict', 'pterr', 'ptverbose', 'pttype', 'pttypeerr', 'ptsetunits',
                            '_internal_pardict'}
    _internal_only_ptdef = {'_pt_set', 'ptinit', 'ptset', 'ptget', 'ptadd', 'ptdel', 'ptshow', 'ptsu', 'ptlog',
                            'pt_to_dict', 'pt_to_csv', 'pt_from', '_pt_from_csv'}

    def __init__(self, ptnote='Parameter tracker class', ptinit='__ignore__',
                 ptstrict=True, pterr=False, ptverbose=True, pttype=False, pttypeerr=False, ptsetunits=False,
                 **kwargs):
        """
        General parameter tracking class to keep track of groups of parameters within a class with
        some minor checking and viewing.

        If used as a parent Class, then child Classes can define their own parameters in their __init__ methods
        before calling the parent Class __init__ method.  If additional checking is needed for specific parameters,
        then the child Class can override the 'ptset' method to do custom checking, then call the parent Class _pt_set
        method to do the actual setting.

        Actions are tracked via the Log object.
        
        Parameters
        ----------
        ptnote : str
            Note to describe the parameter tracking instance, used in ptshow
        ptinit : str or csv-list
            see ptinit method for details
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
        ptsetunits : bool
            Flag to set units when setting parameters (see param_track_units.py for details)
        kwargs : key, value pairs
            Initial parameters to set (if any)
            
        Methods
        -------
        ptset : set parameters (with checking)
        ptinit : initialize parameters from a list of keys to default value (don't set type yet)
        ptget : get parameter value
        ptadd : add new parameters (only way to add new parameters in strict mode)
        ptdel : delete parameters
        ptsu : set parameters silently and can change internal parameters listed above (no checking, log entries or errors)
        ptshow : show current parameters being tracked
        ptlog : show or return the Log object
        pt_to_dict : return current parameters as a dictionary (or serialized form), plus options for types or internal parameters
        pt_to_csv : return current parameters as a CSV string
        pt_from : set parameters from a file (CSV, JSON or YAML formats supported, set by filename extension)

        """
        from . import __version__
        __log__.post(f"Parameter Track:  version {__version__}", silent=True)
        __log__.post(f"Parameters tracking: {ptnote}.", silent=True)
        self.ptsu(ptnote=ptnote, ptstrict=ptstrict, pterr=pterr, ptverbose=ptverbose,
                  pttype=pttype, pttypeerr=pttypeerr, ptsetunits=ptsetunits)
        self._internal_pardict = {}
        if ptinit != '__ignore__':
            self.ptinit(ptinit, default=None)
        self.ptadd(**kwargs)

    def __repr__(self):
        return self.ptshow(return_only=True)

    def ptinit(self, param_list, default=None):
        """
        Initialize parameters to 'default' from a list of keys or a filename via ptsu method.

        If the default value is not None, then the parameters will be initialized to this value and the type set to the type of this value.
        If the default value is None, then the parameters will be initialized to None and the type will be set None as a marker for
        future type checking.

        Parameters
        ----------
        param_list : list of str, csv-list or str
            List of keys to initialize parameters or filename[:key].  If a filename is given, then parameters will be initialized from the file
            (CSV, JSON, YAML, NPZ/Y formats supported, set by filename extension).  If a key is given after a colon, then only that key will be used
            from the file (e.g. for YAML files with multiple keys).
        default : any
            Default value to set for each parameter (default is None)

        """
        if isinstance(param_list, str):
            inp = param_list.split(':')
            from os.path import isfile
            if isfile(inp[0]):
                use_key = inp[1] if len(inp) > 1 else None
                self.pt_from(inp[0], use_key=use_key, use_option='su', as_row=False)
                return
            else:
               data = {x.strip(): default for x in param_list.split(',')}
        elif isinstance(param_list, list):
            data = {key: default for key in param_list}
        else:
            __log__.post(f"Parameter list for initialization must be a string or list, "
                         f"got {param_list} ({tn(param_list)})", silent=False)  # always print 'ignored'
            return
        __log__.post(f"Initializing parameters from {param_list}", silent=not self.ptverbose)
        self.ptsu(**data)

    def ptset(self, **kwargs):
        """
        Show or set the parameters -- this is the wrapper around the "workhorse" method _pt_set.

        If parameter tracking is used as a parent Class, then this can be redefined for custom behavior, then
        call the _pt_set method to do the actual setting.  Could call it 'update' there, instead of ptset.

        _pt_set checks for internal only variables/methods (ignores) and handles strict mode and verbosity.  This checks
        against the 'ptstrict' and 'pttype' parameters.  Behavior is regulated by 'pterr' and 'pttypeerr' parameters.

        """
        self._pt_set(**kwargs)

    def _pt_set(self, **kwargs):
        """See ptset docstring."""
        for key, val in kwargs.items():
            if key in self._internal_only_ptvar or key in self._internal_only_ptdef:
                __log__.post(f"Attempt to set internal parameter/method '{key}' -- ignored, try method 'ptsu'.", silent=False)  # always print 'ignored'
            elif key in self._internal_pardict:  # It has a history, so check type.
                __ptu__.setattr(self, key, val)
                __log__.post(f"Setting existing parameter {__ptu__.msg}", silent=not self.ptverbose)
                if self._internal_pardict[key] is None:  # None always gets updated type
                    self._internal_pardict[key] = copy(__ptu__.type)
                elif type(val) != self._internal_pardict[key]:  # Types don't match
                    if self.pttype:  # ... and I care about types.
                        if self.pttypeerr:
                            raise ParameterTrackError(typemsg(key, self._internal_pardict[key], __ptu__.tn, 'raise'))
                        else:
                            __log__.post(typemsg(key, self._internal_pardict[key], __ptu__.tn, 'retain'), silent=False)  # since I care about types
                    else:  # ... but I don't care about types.
                        self._internal_pardict[key] = copy(__ptu__.type)  # so I'll just reset it to new type
                        __log__.post(typemsg(key, self._internal_pardict[key], __ptu__.tn, 'reset'), silent=True)  # silent since I don't care about types
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

        It also acts like a "replace" method -- the new one is changed in both value and type.

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
        This is the only way to set internal parameters.  Other parameters are handled like ptadd except that it doesn't change the
        type of existing parmaeters.

        Parameters
        ----------
        kwargs : key, value pairs
            Parameters to set in superuser mode

        """
        if 'ptverbose' in kwargs:
            self.ptverbose = bool(kwargs.pop('ptverbose'))
            __log__.post(f"su: Setting internal parameter 'ptverbose' to <{self.ptverbose}>", silent=not self.ptverbose)
        if 'ptnote' in kwargs:  # always allow ptnote to be set
            self.ptnote = bool(kwargs.pop('ptnote'))
            __log__.post(f"su: Setting internal parameter 'ptnote' to <{self.ptnote}>", silent=not self.ptverbose)
        if 'ptsetunits' in kwargs:
            __ptu__.handle_units(kwargs.pop('ptsetunits'))
            self.ptsetunits = __ptu__.use_units
            __log__.post(f"su: Setting internal parameter 'ptsetunits' to <{self.ptsetunits}>", silent=not self.ptverbose)

        for key, val in kwargs.items():
            if key in self._internal_only_ptdef:  # Internal method, so ignore.
                __log__.post(f"su: Attempt to set internal method '{key}' -- ignored.", silent=False)  # always print 'ignored'
            elif key in self._internal_only_ptvar: # Internal variable, so only allow bools to be set.
                if key[0] == '_':  # private internal variable, so ignore
                    __log__.post(f"su: Attempt to set internal parameter '{key}' -- ignored.", silent=False)  # always print 'ignored'
                else:  # public internal variable, so only allow bools to be set
                    if type(val) != bool:
                        __log__.post(f"su: Internal parameter '{key}' should be bool -- ignored.", silent=False)  # always print 'ignored'
                    else:
                        setattr(self, key, val)
                        __log__.post(f"su: Setting internal parameter '{key}' to <{val}>", silent=not self.ptverbose)
            elif key in self._internal_pardict:
                __ptu__.setattr(self, key, val)
                __log__.post(f"su: Changing '{key}' to <{__ptu__.val}> retaining ({__ptu__.tn})", silent=not self.ptverbose)
            else:  # Add it same as ptadd
                self.ptadd(**{key: val})

    def ptget(self, key, default=ParameterTrackError):
        """
        Get the value of a parameter.

        Parameters
        ----------
        key : str
            Parameter name to get
        default : any
            Default value to return if parameter not found, if not provided, then raise ParameterTrackError
        
        """
        if key in self._internal_pardict:
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
                key = [x.strip() for x in kval.split(',')]
            elif isinstance(kval, list):
                key = kval
            else:
                __log__.post(f"Parameter names to delete must be strings or lists, got <{kval}> ({tn(kval)})", silent=False)  # always print 'ignored'
                continue
            for k in key:
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
        show += self.pt_to_dict(serialize='yaml', include_par=include_par, types_to_dict=False)
        if show_all:
            show += "\nParameter types:\n"
            show += '-'*len("Parameter types:") + "\n"
            show += self.pt_to_dict(serialize='yaml', include_par=include_par, types_to_dict=True)
            show += "\nInternal parameters:\n"
            show += '-'*len("Internal parameters:") + "\n"
            show += self.pt_to_dict(serialize='yaml', types_to_dict="__internal__")
        if return_only:
            return show
        print(show)
    
    def ptlog(self, action='show'):
        """
        Do stuff with the Log object.

        Parameters
        ----------
        action : str
            'return' : return the Log object
            'show' : print the Log to stdout
            'clear' : clear the Log entries
            'dump' : dump the Log to a file 'param_track_log.txt'

        """
        if action == 'return':
            return __log__
        elif action == 'show':
            __log__.show()
        elif action == 'clear':
            __log__.log = []
        elif action == 'dump':
            with open('param_track_log.txt', 'w') as fp:
                __log__.show(file=fp)
        else:
            print(f"Unknown 'ptlog' action '{action}'.")

    def pt_to_dict(self, serialize=None, include_par=None, types_to_dict=False):
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
        types_to_dict : bool or '__internal__'
            If True, then return the types of the parameters instead of their values
            If '__internal__', then return the internal parameters instead of the tracked parameters

        Returns
        -------
        dict, str, or bytes
            Dictionary or serialized form of current parameters

        """
        rec = {}
        if isinstance(types_to_dict, str) and types_to_dict == "__internal__":  # internal parameters only
            include_par = [x for x in self._internal_only_ptvar if x[0]!= '_']
            types_to_dict = False  # ignore types_to_dict for internal
        else: # normal parameters or types
            include_par = self._internal_pardict.keys() if include_par is None else include_par
            if isinstance(include_par, str):
                include_par = [x.strip() for x in include_par.split(',')]
        for key in include_par:
            val = copy(getattr(self, key))
            if types_to_dict:
                val = self._internal_pardict.get(key)
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
    
    def pt_from(self, filename, use_key=None, use_option='add', as_row=False):
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
        data, units = from_file(filename, use_key=use_key, as_row=as_row)
        if units:
            self.ptsu(ptsetunits=units)
        if use_option == 'add':
            self.ptadd(**data)
        elif use_option == 'set':
            self.ptset(**data)
        elif use_option == 'su':
            self.ptsu(**data)
        else:
            print("Unknown option 'use_option'")