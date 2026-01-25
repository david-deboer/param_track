# -*- mode: python; coding: utf-8 -*-
# Copyright 2025 David R DeBoer
# Licensed under the MIT license. See LICENSE file in the project root for details.


"""General simple parameter tracking module."""
from .param_track_error import ParameterTrackError, Notices
from copy import copy


__notice__ = Notices()


class Parameters:
    """
    General parameter tracking class to keep track of groups of parameters within a class with some minor checking and
    viewing - typically will only use the wrapper functions 'ptset' and 'ptshow'.

    """
    _internal_only_ptvar = {'ptnote', 'ptstrict', 'pterr', 'ptverbose', 'pttype', 'pttypeerr',
                            '_internal_self_type', '_internal_pardict'}
    _internal_only_ptdef = {'_pt_set', 'ptinit', 'ptset', 'ptget', 'ptadd', 'ptshow', 'ptsu',
                            'pt_to_dict', 'pt_to_csv', 'pt_from', '_pt_from_csv'}

    def __init__(self, ptnote='Parameter tracker', ptstrict=True, pterr=False, ptverbose=True, pttype=False, pttypeerr=False, **kwargs):
        """
        General parameter tracking class to keep track of groups of parameters within a class with some minor checking and
        viewing - typically will only use the methods 'ptset', 'ptget' and 'ptshow'.

        If used as a parent Class, then child Classes can define their own parameters in their __init__ methods
        before calling the parent Class __init__ method.  If additional checking is needed for specific parameters,
        then the child Class can override the 'ptset' method to do custom checking, then call the parent Class _pt_set
        method to do the actual setting.
        
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
            Flag to check parameter reset type -- only used in ptset and only provides notices.
            Checks relative to the initial type set or when ptadd/ptsu was used.
        pttypeerr : bool
            Flag to make parameter setting raise ParameterTrackError on type change or just notice -- only used in ptset.
        kwargs : key, value pairs
            Initial parameters to set
            
        Methods
        -------
        ptset : set parameters (with checking)
        ptinit : initialize parameters from a list of keys
        ptget : get parameter value
        ptadd : add new parameters (only way to add new parameters in strict mode)
        ptsu : set parameters silently and can change internal parameters listed above (no checking, notices or errors)
        ptshow : show current parameters being tracked

        """
        self._internal_self_type = type(self)
        __notice__.post(f"Initializing Parameters: {ptnote}.", silent=True)
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
            __notice__.post(f"Initializing parameter '{key}' to {default}", silent=not self.ptverbose)

    def ptset(self, **kwargs):
        """
        Show or set the parameters -- this is the wrapper around the "workhorse" method _pt_set.

        If parameter tracking is used as a parent Class, then this can be redefined for custom behavior, then
        call the _pt_set method to do the actual setting.

        _pt_set checks for internal only variables/methods and handles strict mode and verbosity.

        """
        self._pt_set(**kwargs)

    def _pt_set(self, **kwargs):
        """See ptset docstring."""
        for key, val in kwargs.items():
            if key in self._internal_only_ptvar or key in self._internal_only_ptdef:
                __notice__.post(f"Attempt to set internal parameter/method '{key}' -- ignored.", silent=False)  # always print 'ignored'
            elif key in self._internal_pardict:  # It has a history, so check type.
                oldval = copy(getattr(self, key))
                setattr(self, key, val)
                ptype = self._internal_pardict[key].__name__
                __notice__.post(f"Resetting parameter '{key}' as <{type(val).__name__}>:  {val}     [previous value <{type(oldval).__name__}>: {oldval}]", silent=not self.ptverbose)
                if self._internal_pardict[key] == self._internal_self_type:  # Set via ptinit so doesn't have a type yet.
                    self._internal_pardict[key] = type(val)
                elif type(val) != self._internal_pardict[key]:
                    if self.pttype:  # Types don't match and I care about types.
                        if self.pttypeerr:
                            raise ParameterTrackError(f"Parameter '{key}' reset with different type: <{ptype}> to <{type(val).__name__}>")
                        else:
                            __notice__.post(f"Parameter '{key}' reset with different type: <{ptype}> to <{type(val).__name__}> -- retaining <{ptype}>", silent=False)
                    else:  # Types don't match but I don't care about types.
                        self._internal_pardict[key] = type(val)
                        __notice__.post(f"Parameter '{key}' type updated to <{type(val).__name__}>", silent=not self.ptverbose)
            elif self.ptstrict:  # Key is unknown and strict mode is on.
                if self.pterr:
                    raise ParameterTrackError(f"Unknown parameter '{key}' in strict mode.")
                else:
                    __notice__.post(f"Unknown parameter '{key}' in strict mode -- ignored.  Use ptadd to add new parameters.", silent=False)  # always print 'ignored'
            else:  # New parameter not in strict mode so just set it.
                setattr(self, key, val)
                self._internal_pardict[key] = type(val)
                __notice__.post(f"Setting parameter '{key}' as <{type(val).__name__}>:  {val}", silent=not self.ptverbose)

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
                __notice__.post(f"Attempt to add internal parameter/method '{key}' -- ignored.", silent=False)  # always print 'ignored'
            else:
                setattr(self, key, val)
                self._internal_pardict[key] = type(val)
                __notice__.post(f"Adding parameter '{key}' as <{type(val).__name__}>:  {val}", silent=not self.ptverbose)

    def ptsu(self, **kwargs):
        """
        This sets parameters with little checking and no errors.

        This is the only way to set internal parameters if needed.  Same as ptadd except that existing parameters
        can be reset and there are no notices or errors, except for methods.  Also, it will only set parameter type if not
        already defined.

        Parameters
        ----------
        kwargs : key, value pairs
            Parameters to set in superuser mode

        """
        for key, val in kwargs.items():
            if key in self._internal_only_ptdef:
                __notice__.post(f"Attempt to set internal method '{key}' -- ignored.", silent=False)  # always print 'ignored'
            elif key in self._internal_only_ptvar:
                if type(val) != bool:
                    __notice__.post(f"Internal parameter '{key}' should be bool -- ignored.", silent=False)  # always print 'ignored'
                else:
                    setattr(self, key, val)
            else:
                setattr(self, key, val)
                if key not in self._internal_only_ptvar:
                    self._internal_pardict[key] = type(val)

    def ptshow(self, return_only=False, notices=False, include_par=None):
        """
        Show the current parameters being tracked.

        Parameters
        ----------
        return_only : bool
            If True and not 'notices', then return the string instead of printing it (for __repr__ method)
            If True and 'notices', then return the Notices object
            If False, then print the string representation and if 'notices' then also print the notices
        notices : bool
            If True and not 'return_only' then print the notices after the parameters.
            If True and 'return_only' then return the Notices object.
        include_par : list of str or None
            If not None, then only include these parameters in the output

        Returns
        -------
        if 'return_only' and not 'notices' : str
            JSON string representation of the current parameters
        if 'return_only' and 'notices' : Notices
            Notices object with all notices posted
        if not 'return_only' : None

        """
        if notices and return_only:
            return __notice__
        show = f"Parameter Tracking: {self.ptnote}\n"
        show += f"(ptstrict: {self.ptstrict}, pterr: {self.pterr}, ptverbose: {self.ptverbose}, pttype: {self.pttype}, pttypeerr: {self.pttypeerr})\n"
        show += self.pt_to_dict(serialize='json', include_par=include_par)
        if return_only:
            return show
        print(show)
        if notices:
            print("\nAll Notices:")
            print("-------------")
            for anotice in __notice__.notices:
                print(f"  [{anotice.time}] {anotice.message}")   
    
    def pt_to_dict(self, serialize=None, include_par=None):
        """
        Return the current parameters as a dictionary.

        Parameters
        ----------
        serialize : str or None
            If 'json', then return JSON serialized string
            If 'pickle', then return pickle serialized bytes
            If None, then return dictionary
        include_par : list of str or None
            If not None, then only include these parameters in the output dictionary

        Returns
        -------
        dict, str, or bytes
            Dictionary or serialized form of current parameters

        """
        from datetime import datetime
        rec = {}
        pars2use = self._internal_pardict.keys() if include_par is None else include_par
        for key in pars2use:
            val = copy(getattr(self, key))
            if serialize == 'json':
                if isinstance(val, datetime):
                    val = val.isoformat()
                else:
                    try:
                        _ = json.dumps({'check': val})
                    except TypeError:
                        val = str(val)        
            rec[key] = val
        if serialize is not None:
            if serialize == 'json':
                import json
                return json.dumps(rec, indent=4)
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
        __notice__.post(f"{'Adding' if use_add else 'Setting'} parameters from {filename}", silent=not self.ptverbose)
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
            __notice__.post(f"{'Adding' if use_add else 'Setting'} from row {as_row}", silent=not self.ptverbose)
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