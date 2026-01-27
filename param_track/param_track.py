# -*- mode: python; coding: utf-8 -*-
# Copyright 2025 David R DeBoer
# Licensed under the MIT license. See LICENSE file in the project root for details.


"""General simple parameter tracking module."""
from .param_track_support import ParameterTrackError, Log, typemsg, check_serialize, typename
from copy import copy


__log__ = Log()


class Parameters:
    """
    General parameter tracking class to keep track of groups of parameters within a class with 
    some minor checking and viewing.

    """
    _internal_only_ptvar = {'ptnote', 'ptstrict', 'pterr', 'ptverbose', 'pttype', 'pttypeerr',
                            '_internal_self_type', '_internal_pardict'}
    _internal_only_ptdef = {'_pt_set', 'ptinit', 'ptset', 'ptget', 'ptadd', 'ptdel', 'ptshow', 'ptsu', 'ptlog',
                            'pt_to_dict', 'pt_to_csv', 'pt_from', '_pt_from_csv', '_internal_par_to_dict'}

    def __init__(self, ptnote='Parameter tracker class', ptstrict=True, pterr=False, ptverbose=True, pttype=False, pttypeerr=False, **kwargs):
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
        pt_to_dict : return current parameters as a dictionary (or serialized form)
        pt_to_csv : return current parameters as a CSV string
        pt_from : set parameters from a file (CSV, JSON or YAML formats supported, set by filename extension)

        """
        self._internal_self_type = type(self)
        from . import __version__
        __log__.post(f"Parameter Track:  version {__version__}", silent=True)
        __log__.post(f"Initializing Parameters: {ptnote}.", silent=True)
        self.ptnote = ptnote
        self.ptstrict = ptstrict
        self.pterr = pterr
        self.ptverbose = ptverbose
        self.pttype = pttype
        self.pttypeerr = pttypeerr
        self._internal_pardict = {}
        self.ptadd(**kwargs)

    def __repr__(self):
        return self.ptshow(return_only=True)

    def ptinit(self, param_list, default=None):
        """
        Initialize parameters to 'default' from a list of keys.

        If initialized this way, the type is then set when first set via ptset, ptadd or ptsu.

        Parameters
        ----------
        param_list : list of str
            List of keys to initialize parameters
        default : any
            Default value to set for each parameter (default is None)

        """
        for key in param_list:
            setattr(self, key, default)
            self._internal_pardict[key] = self._internal_self_type
            __log__.post(f"Initializing parameter '{key}' to <{default}>", silent=not self.ptverbose)

    def ptset(self, **kwargs):
        """
        Show or set the parameters -- this is the wrapper around the "workhorse" method _pt_set.

        If parameter tracking is used as a parent Class, then this can be redefined for custom behavior, then
        call the _pt_set method to do the actual setting.

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
                oldval = copy(getattr(self, key))
                setattr(self, key, val)
                __log__.post(f"Setting existing parameter '{key}' to <{val}> [was <{oldval}>]", silent=not self.ptverbose)
                if self._internal_pardict[key] == self._internal_self_type:  # Set via ptinit so doesn't have a type yet.
                    self._internal_pardict[key] = type(val)
                    __log__.post(f"Parameter '{key}' type initialized to <{typename(val)}>", silent=not self.ptverbose)
                elif type(val) != self._internal_pardict[key]:  # Types don't match
                    if self.pttype:  # ... and I care about types.
                        if self.pttypeerr:
                            raise ParameterTrackError(typemsg(key, self._internal_pardict[key], type(val), 'raise'))
                        else:
                            __log__.post(typemsg(key, self._internal_pardict[key], type(val), 'retain'), not self.ptverbose)
                    else:  # ... but I don't care about types.
                        self._internal_pardict[key] = type(val)
                        __log__.post(typemsg(key, self._internal_pardict[key], type(val), 'reset'), silent=True)
            elif self.ptstrict:  # Key is unknown and strict mode is on.
                if self.pterr:
                    raise ParameterTrackError(f"Unknown parameter '{key}' in strict mode.")
                else:
                    __log__.post(f"Unknown parameter '{key}' in strict mode -- ignored.  Use 'ptadd' to add new parameters.", silent=False)  # always print 'ignored'
            else:  # New parameter not in strict mode so just set it.
                setattr(self, key, val)
                self._internal_pardict[key] = type(val)
                __log__.post(f"Setting new parameter '{key}' to <{val}> of type <{typename(val)}>", silent=not self.ptverbose)

    def ptget(self, key, default=None, raise_err=False):
        """
        Get the value of a parameter.

        Parameters
        ----------
        key : str
            Parameter name to get
        default : any
            Default value to return if parameter not found (if raise_err is False)
        raise_err : bool
            If True, then raise ParameterTrackError if parameter not found
        
        """
        if hasattr(self, key):
            return getattr(self, key)
        if raise_err:
            raise ParameterTrackError(f"Parameter '{key}' not found.")
        return default

    def ptadd(self, **kwargs):
        """
        Add new parameters to the parameter tracking -- only way to add new parameters if ptstrict is True.

        If ptstrict is False, then this is equivalent to ptset except that type checking is ignored and there are fewer
        messages.  It will reset the parameter type to new value type.

        Parameters
        ----------
        kwargs : key, value pairs
            Parameters to add

        """
        for key, val in kwargs.items():
            if key in self._internal_only_ptvar or key in self._internal_only_ptdef:
                __log__.post(f"Attempt to modify internal parameter/method '{key}' -- ignored.", silent=False)  # always print 'ignored'
            elif key in self._internal_pardict:
                __log__.post(f"Replacing parameter '{key}' with <{val}> of type <{typename(val)}> [was <{getattr(self, key)}> of type <{typename(self._internal_pardict[key])}>]",
                             silent=not self.ptverbose)
                setattr(self, key, val)
                self._internal_pardict[key] = type(val)
            else:
                __log__.post(f"Adding new parameter '{key}' as <{val}> of type <{typename(val)}>", silent=not self.ptverbose)
                setattr(self, key, val)
                self._internal_pardict[key] = type(val)

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
                __log__.post(f"Parameter names to delete must be strings or lists, got {typename(kval)}", silent=False)  # always print 'ignored'
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

    def ptsu(self, **kwargs):
        """
        This sets parameters with little checking and no errors.

        This is the only way to set internal parameters if needed.  Same as ptadd except that existing internal parameters
        can be set and type won't change.

        Parameters
        ----------
        kwargs : key, value pairs
            Parameters to set in superuser mode

        """
        for key, val in kwargs.items():
            if key == 'ptnote':
                setattr(self, key, val)
                __log__.post(f"su: Setting 'ptnote' to <{val}>", silent=not self.ptverbose)
            elif key in self._internal_only_ptdef:
                __log__.post(f"su: Attempt to set internal method '{key}' -- ignored.", silent=False)  # always print 'ignored'
            elif key in self._internal_only_ptvar:
                if key[0] == '_':
                    __log__.post(f"su: Attempt to set internal parameter '{key}' -- ignored.", silent=False)  # always print 'ignored'
                else:
                    if type(val) != bool:
                        __log__.post(f"su: Internal parameter '{key}' should be bool -- ignored.", silent=False)  # always print 'ignored'
                    else:
                        setattr(self, key, val)
                        __log__.post(f"su: Setting internal parameter '{key}' to <{val}>", silent=not self.ptverbose)
            elif key in self._internal_pardict and type(val) == self._internal_pardict[key]:
                oldval = copy(getattr(self, key))
                __log__.post(f"su: Replacing parameter '{key}' with <{val}> of same type <{typename(self._internal_pardict[key])}> [was <{oldval}>]",
                             silent=not self.ptverbose)
                setattr(self, key, val)
            elif key in self._internal_pardict:
                oldval = copy(getattr(self, key))
                __log__.post(f"su: Replacing parameter '{key}' with <{val}> of different type <{typename(val)}>, " \
                             f"but retaining type <{typename(self._internal_pardict[key])}> [was <{oldval}> of type <{typename(oldval)}>]",
                             silent=not self.ptverbose)
                setattr(self, key, val)
            else:
                self._internal_pardict[key] = type(val)
                __log__.post(f"su: Adding new parameter '{key}' as <{val}> with type <{typename(val)}>", silent=not self.ptverbose)
                setattr(self, key, val)

    def ptshow(self, return_only=False, vals_only=False, include_par=None):
        """
        Show the current parameters being tracked (or their types).

        Parameters
        ----------
        return_only : bool
            If True, then return the string instead of printing it (for __repr__ method)
            If False, then print the string representation
        vals_only : bool
            If True, then only show the parameter values (types and internal parameters are not shown)
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
        if not vals_only:
            show += "\nParameter types:\n"
            show += '-'*len("Parameter types:") + "\n"
            show += self.pt_to_dict(serialize='yaml', include_par=include_par, types_to_dict=True)
            show += "\nInternal parameters:\n"
            show += '-'*len("Internal parameters:") + "\n"
            show += self._internal_par_to_dict(serialize='yaml')
        if return_only:
            return show
        print(show)
    
    def ptlog(self, return_only=False):
        """
        Return/print the Log object.

        Parameters
        ----------
        return_only : bool
            If True, then return the Log object and don't print anything.

        """
        if return_only:
            return __log__
        __log__.show()

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
        include_par : list of str or None
            If not None, then only include these parameters in the output dictionary
        types_to_dict : bool
            If True, then return the types of the parameters instead of their values

        Returns
        -------
        dict, str, or bytes
            Dictionary or serialized form of current parameters

        """
        rec = {}
        pars2use = self._internal_pardict.keys() if include_par is None else include_par
        for key in pars2use:
            val = copy(getattr(self, key))
            if types_to_dict:
                val = type(val)
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
    
    def _internal_par_to_dict(self, serialize=None):
        """
        Internal method to return the current internal parameters.

        Parameters
        ----------
        serialize : str or None
            If 'json', then return JSON serialized string
            If 'yaml', then return YAML serialized string
            If None, then return dictionary

        Returns
        -------
        dict or str
            Dictionary or serialized form of current parameters

        """
        rec = {}
        for key in self._internal_only_ptvar:
            if key[0] == '_':
                continue
            val = copy(getattr(self, key))
            rec[key] = val
        if serialize == 'json':
            import json
            return json.dumps(rec, indent=4)
        elif serialize == 'yaml':
            import yaml
            return yaml.dump(rec)
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
        
        this = self.pt_to_dict(serialize='json', include_par=include_par)

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