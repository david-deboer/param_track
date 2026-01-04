# -*- mode: python; coding: utf-8 -*-
# Copyright 2025 David R DeBoer
# Licensed under the MIT license. See LICENSE file in the project root for details.


"""General simple parameter tracking module."""
from .param_track_error import ParameterTrackError, Warning
from copy import copy


class Parameters:
    """
    General parameter tracking class to keep track of groups of parameters within a class with some minor checking and
    viewing - typically will only use the wrapper functions 'ptset' and 'ptshow'.

    """
    _internal_only_ptvar = {'ptnote', 'ptstrict', 'pterr', 'ptverbose', 'pttype', 'pttypeerr'}
    _internal_only_ptmethods = {'_pt_set', 'ptset', 'ptget', 'ptadd', 'ptshow', 'ptsu'}

    def __init__(self, ptnote='Parameter tracking', ptstrict=True, pterr=False, ptverbose=True, pttype=False, pttypeerr=False, **kwargs):
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
            Flag to check parameter reset type -- only used in ptset and only provides warnings.
            Checks relative to the initial type set or when ptadd/ptsu was used.
        pttypeerr : bool
            Flag to make parameter setting raise ParameterTrackError on type change or just warning -- only used in ptset.
        kwargs : key, value pairs
            Initial parameters to set
            
        Methods
        -------
        ptset : set parameters (with checking)
        ptget : get parameter value
        ptadd : add new parameters (only way to add new parameters in strict mode)
        ptsu : set parameters silently (no checking, warnings or errors)
        ptshow : show current parameters being tracked

        """
        self.ptnote = ptnote
        self.ptstrict = False  # This is initially set to False to allow setting in ptset on initialization
        self.pterr = pterr
        self.ptverbose = ptverbose
        self.pttype = pttype
        self.pttypeerr = pttypeerr
        self._internal_pardict = {}
        self.ptset(**kwargs)
        self.ptstrict = ptstrict

    def __repr__(self):
        return self.ptshow(return_only=True)

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
            if key in self._internal_only_ptvar or key in self._internal_only_ptmethods:
                Warning(f"Attempt to set internal parameter/method '{key}' -- ignored.")
            elif key in self._internal_pardict:  # It has a history, so check type.
                oldval = copy(getattr(self, key))
                setattr(self, key, val)
                ptype = self._internal_pardict[key].__name__
                if self.ptverbose:
                    print(f"Resetting parameter '{key}' as <{type(val).__name__}>:  {val}     [previous value <{type(oldval).__name__}>: {oldval}]")
                if type(val) != self._internal_pardict[key]:
                    if self.pttype:
                        if self.pttypeerr:
                            raise ParameterTrackError(f"Parameter '{key}' reset with different type: <{ptype}> to <{type(val).__name__}>")
                        else:
                            Warning(f"Parameter '{key}' reset with different type: <{ptype}> to <{type(val).__name__}> -- retaining <{ptype}>")
                    else:
                        self._internal_pardict[key] = type(val)
                        if self.ptverbose:
                            print(f"Parameter '{key}' type updated to <{type(val).__name__}>")
            elif self.ptstrict:  # It is unknown and strict mode is on.
                if self.pterr:
                    raise ParameterTrackError(f"Unknown parameter '{key}' in strict mode.")
                else:
                    Warning(f"Unknown parameter '{key}' in strict mode -- ignored.  Use ptadd to add new parameters.")
            else:  # New parameter not in strict mode so just set it.
                setattr(self, key, val)
                self._internal_pardict[key] = type(val)
                if self.ptverbose:
                    print(f"Setting parameter '{key}' as <{type(val).__name__}>:  {val}")

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
            if key in self._internal_only_ptvar or key in self._internal_only_ptmethods:
                Warning(f"Attempt to add internal parameter/method '{key}' -- ignored.")
            else:
                setattr(self, key, val)
                self._internal_pardict[key] = type(val)
                if self.ptverbose:
                    print(f"Adding parameter '{key}' as <{type(val).__name__}>:  {val}")

    def ptsu(self, **kwargs):
        """
        This sets parameters with no checking, warnings or errors (except for methods) and no verbosity.

        This is the only way to set internal parameters if needed.  Same at ptadd except that existing parameters
        can be reset and there are no warnings or errors, except for methods.

        Parameters
        ----------
        kwargs : key, value pairs
            Parameters to set in superuser mode

        """
        for key, val in kwargs.items():
            if key in self._internal_only_ptmethods:
                Warning(f"Attempt to set internal method '{key}' -- ignored.")
            elif key in self._internal_only_ptvar:
                if type(val) != bool:
                    Warning(f"Internal parameter '{key}' should be bool -- ignored.")
                else:
                    setattr(self, key, val)
            else:
                setattr(self, key, val)
                if key not in self._internal_only_ptvar:
                    self._internal_pardict[key] = type(val)

    def ptshow(self, return_only=False):
        """
        Show the current parameters being tracked.

        Parameters
        ----------
        return_only : bool
            If True, then return the string instead of printing it (for __repr__ method)

        Returns
        -------
        str
            String representation of the current parameters

        """
        s = f"Parameter Tracking: {self.ptnote}\n"
        s += f"(ptstrict: {self.ptstrict}, pterr: {self.pterr}, ptverbose: {self.ptverbose}, pttype: {self.pttype}, pttypeerr: {self.pttypeerr})\n"
        for key in sorted(self._internal_pardict.keys()):
            val = getattr(self, key, None)
            s += f"  {key} <{type(val).__name__}> : {val}\n"
        if return_only:
            return s.strip()
        print(s.strip())
