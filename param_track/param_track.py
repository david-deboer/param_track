# -*- mode: python; coding: utf-8 -*-
# Copyright 2025 David R DeBoer
# Licensed under the MIT license. See LICENSE file in the project root for details.


"""General simple parameter tracking module."""
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
                            '_internal_self_type', '_internal_pardict'}
    _internal_only_ptdef = {'_pt_set', 'ptinit', 'ptset', 'ptget', 'ptadd', 'ptdel', 'ptshow', 'ptsu', 'ptlog',
                            'pt_to_dict', 'pt_to_csv', 'pt_from', '_pt_from_csv'}

    def __init__(self, ptnote='Parameter tracker class',
                 ptstrict=True, pterr=False, ptverbose=True, ptinit='__ignore__', 
                 pttype=False, pttypeerr=False, ptsetunits=False,
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
        ptinit : list of str or csv-list
            List of parameter names to initialize to None before setting any parameters (runs ptinit method)
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
        self._internal_self_type = type(self)
        from . import __version__
        __log__.post(f"Parameter Track:  version {__version__}", silent=True)
        __log__.post(f"Initializing Parameters: {ptnote}.", silent=True)
        self.ptsu(ptnote=ptnote, ptstrict=ptstrict, pterr=pterr, ptverbose=ptverbose,
                  pttype=pttype, pttypeerr=pttypeerr, ptsetunits=ptsetunits)
        self._internal_pardict = {}
        if ptinit != '__ignore__':
            self.ptinit(ptinit, default=None)
        self.ptadd(**kwargs)

    def __repr__(self):
        return self.ptshow(return_only=True)

    def ptinit(self, param_list, default=None, use_types=False):
        """
        Initialize parameters to 'default' from a list of keys or a filename via ptsu method, HOWEVER (and unless
        'use_types' is True) the parameter type is set as a special internal type that is only used for checking if
        the parameter is reset to a different type in ptset, but it won't be set to this type.  This allows for
        initialization of parameters without setting their type, but then later when they are set via ptset, the type
        will be initialized and checked against future resets.

        Note that if the parameter list is a filename, then the parameters will be initialized from the file and use_types
        will be set to True since the types will be set from the file.

        Parameters
        ----------
        param_list : list of str, csv-list or filename
            List of keys to initialize parameters or filename
        default : any
            Default value to set for each parameter (default is None)
        use_types : bool, optional
            If True, then handle types/units when initializing parameters (see param_track_units.py for details)

        """
        if isinstance(param_list, str):
            inp = param_list.split(':')
            from os.path import isfile
            if isfile(inp[0]):
                from .param_track_io import pt_from
                data, units = pt_from(inp[0], use_key=inp[1] if len(inp) > 1 else None)
                if units:
                    self.ptsu(ptsetunits=units)
                    use_types = True
            else:
               data = {x.strip(): default for x in param_list.split(',')}
        elif isinstance(param_list, list):
            data = {key: default for key in param_list}
        else:
            __log__.post(f"Parameter list for initialization must be a string or list, got {tn(param_list)}", silent=False)  # always print 'ignored'
            return
        __log__.post(f"Initializing parameters from {param_list}", silent=not self.ptverbose)
        self.__pt_init_flag__ = not use_types  # internal flag to indicate the initialization phase/type handling in ptsu
        self.ptsu(**data)
        self.__pt_init_flag__ = False  # reset the initialization phase flag

    def ptset(self, **kwargs):
        """
        Show or set the parameters -- this is the wrapper around the "workhorse" method _pt_set.

        If parameter tracking is used as a parent Class, then this can be redefined for custom behavior, then
        call the _pt_set method to do the actual setting.  Could call it 'update' there, instead of ptset.

        _pt_set checks for internal only variables/methods and handles strict mode and verbosity.  This checks against the
        'ptstrict' and 'pttype' parameters.  Behavior is regulated by 'pterr' and 'pttypeerr' parameters.  'ptverbose'
        regulates notice printing.

        """
        self._pt_set(**kwargs)

    def _pt_set(self, **kwargs):
        """See ptset docstring."""
        for key, val in kwargs.items():
            if key in self._internal_only_ptvar or key in self._internal_only_ptdef:
                __log__.post(f"Attempt to set internal parameter/method '{key}' -- ignored, try method 'ptsu'.", silent=False)  # always print 'ignored'
            elif key in self._internal_pardict:  # It has a history, so check type.
                __ptu__.setattr(self, key, val)
                __log__.post(f"Setting existing parameter '{key}' to <{__ptu__.val}> [was <{__ptu__.oldval}>]", silent=not self.ptverbose)
                if self._internal_pardict[key] == self._internal_self_type:  # Set via ptinit so doesn't have a type yet.
                    self._internal_pardict[key] = copy(__ptu__.type)
                    __log__.post(f"Parameter '{key}' type initialized to <{__ptu__.tn}>", silent=not self.ptverbose)
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
                __log__.post(f"Setting new parameter '{key}' to <{__ptu__.val}> of type <{__ptu__.tn}>", silent=not self.ptverbose)

    def ptadd(self, **kwargs):
        """
        Add new parameters to the parameter tracking -- only way to add new parameters if ptstrict is True.

        If ptstrict is False, then this is equivalent to ptset except that type checking is ignored and there are fewer
        messages.  It will reset the parameter type to new value type (unlike ptsu).

        Parameters
        ----------
        kwargs : key, value pairs
            Parameters to add

        """
        for key, val in kwargs.items():
            if key in self._internal_only_ptvar or key in self._internal_only_ptdef:  # Internal only, so ignore.
                __log__.post(f"Attempt to modify internal parameter/method '{key}' -- ignored.", silent=False)  # always print 'ignored'
            elif key in self._internal_pardict:  # Already exists, so replace it.
                __ptu__.setattr(self, key, val)
                __log__.post(f"Replacing parameter '{key}' with <{val}> of type <{__ptu__.tn}> [was <{__ptu__.oldval}> of type <{tn(self._internal_pardict[key])}>]",
                             silent=not self.ptverbose)
                self._internal_pardict[key] = copy(__ptu__.type)
            else:  # New parameter, so add it.
                __ptu__.setattr(self, key, val)
                __log__.post(f"Adding new parameter '{key}' as <{val}> of type <{__ptu__.tn}>", silent=not self.ptverbose)
                self._internal_pardict[key] = copy(__ptu__.type)

    def ptsu(self, **kwargs):
        """
        This sets parameters with little checking and no errors.

        This is the only way to set internal parameters if needed.  Same as ptadd except that existing internal parameters
        can be set and type won't change, unlike ptadd.

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
            elif self.__pt_init_flag__:  # During initialization phase, so set without type checking but mark type as internal self type for future checking.
                __ptu__.setattr(self, key, val)
                self._internal_pardict[key] = self._internal_self_type  # mark type as internal self type for future checking
                __log__.post(f"su: Initializing parameter '{key}' to <{__ptu__.val}> with internal self type", silent=not self.ptverbose)   
            elif key in self._internal_pardict and type(val) == self._internal_pardict[key]:  # Existing parameter of same type
                __ptu__.setattr(self, key, val)
                __log__.post(f"su: Replacing parameter '{key}' with <{__ptu__.val}> of same type <{__ptu__.tn}> [was <{__ptu__.oldval}>]",
                             silent=not self.ptverbose)
            elif key in self._internal_pardict:  # Existing parameter of different type
                __ptu__.setattr(self, key, val)
                __log__.post(f"su: Replacing parameter '{key}' with <{__ptu__.val}> of different type <{__ptu__.tn}>, " \
                             f"but retaining type <{tn(self._internal_pardict[key])}> [was <{__ptu__.oldval}> of type <{tn(__ptu__.oldval)}>]",
                             silent=not self.ptverbose)
            else:  # New parameter, so add it.
                __ptu__.setattr(self, key, val)
                self._internal_pardict[key] = copy(__ptu__.type)
                __log__.post(f"su: Adding new parameter '{key}' as <{__ptu__.val}> with type <{__ptu__.tn}>", silent=not self.ptverbose)

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
                __log__.post(f"Parameter names to delete must be strings or lists, got {tn(kval)}", silent=False)  # always print 'ignored'
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
            raise ParameterTrackError(f"Unknown action '{action}' for ptlog.")

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

    def pt_to_csv(self, include_par=None, as_row=False, include_header=False):
        """
        Return the current parameters as a CSV string.

        Parameters
        ----------
        include_par : list of str or None
            If not None, then only include these parameters in the CSV output
        as_row : bool
            If True, then return the CSV as a single row instead of key-value pairs
        include_header : bool
            If True include the header row

        Returns
        -------
        str
            CSV string of current parameters

        """
        import csv
        import io
        import json
        
        this = self.pt_to_dict(serialize='json', include_par=include_par, types_to_dict=False)

        buf = io.StringIO()
        writer = csv.writer(buf)

        if as_row:
            if include_header:
                writer.writerow([key for key, val in json.loads(this).items()])
            writer.writerow([val for key, val in json.loads(this).items()])
        else:
            if include_header:
                writer.writerow(['parameter', 'value'])
            writer.writerows([[key, val] for key, val in json.loads(this).items()])

        return buf.getvalue()
    
    def pt_from(self, filename, use_add=False, as_row=False):
        """
        Set parameters from a file, depending on tthe format of the file per tag.

        Currently csv, json and yaml formats are supported.
    
        Parameters
        ----------
        filename : str
            Path to the file containing parameters
        use_add : bool
            If True, then use ptadd to add parameters instead of ptset
        as_row : False or int (CSV format only)
            If int, then read the CSV from row 'as_row' instead of key-value pairs
            and first line is header (works since row 0 is header)

        """
        __log__.post(f"{'Adding' if use_add else 'Setting'} parameters from {filename}", silent=not self.ptverbose)
        if filename.endswith('.csv'):
            self._pt_from_csv(filename, as_row=as_row, use_add=use_add)
        elif filename.endswith('.json'):
            import json
            with open(filename, 'r') as fp:
                data = json.load(fp)
            using = self.ptadd if use_add else self.ptset
            using(**data)
        elif filename.endswith('.yaml') or filename.endswith('.yml'):
            import yaml
            with open(filename, 'r') as fp:
                data = yaml.safe_load(fp)
            using = self.ptadd if use_add else self.ptset
            using(**data)
        else:
            raise ParameterTrackError(f"Unsupported file format for parameter loading: {filename}")

    def _pt_from_csv(self, filename, use_add=False, as_row=False):
        """Set parameters from a CSV file (see pt_from)."""
        import csv
        if as_row:
            as_row = int(as_row)
            __log__.post(f"{'Adding' if use_add else 'Setting'} from row {as_row}", silent=not self.ptverbose)
        using = self.ptadd if use_add else self.ptset
        with open(filename, 'r') as fp:
            reader = csv.reader(fp)
            if as_row:
                keys = next(reader)
            for i, row in enumerate(reader):
                if as_row:
                    if i != as_row-1:
                        continue
                    for key, val in zip(keys, row):
                        using(**{key: val})
                    break
                else:
                    if len(row) != 2:
                        continue
                    key, val = row
                    using(**{key: val})