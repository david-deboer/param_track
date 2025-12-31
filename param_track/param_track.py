# -*- mode: python; coding: utf-8 -*-
# Copyright 2025 David R DeBoer
# Licensed under the BSD license. See LICENSE.txt file in the project root for details.
"""General simple parameter tracking module."""
from .param_track_error import ParameterTrackError, Warning
from copy import copy


class Parameters:
    """
    General parameter tracking class to keep track of groups of parameters within a class with some minor checking and
    viewing - typically will only use the wrapper functions 'ptset' and 'ptshow'.

    """
    _internal_only_ptvar = {'ptnote', 'ptstrict', 'pterr', 'ptverbose', '_internal_parset'}
    _internal_only_ptmethods = {'_pt_set', 'ptset', 'ptadd', 'ptshow', 'ptsu'}

    def __init__(self, ptnote='Parameter tracking', ptstrict=False, pterr=False, ptverbose=True, **kwargs):
        """
        General parameter tracking class to keep track of groups of parameters within a class with some minor checking and
        viewing - typically will only use the wrapper functions 'ptset' and 'ptshow'.

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
        kwargs : key, value pairs
            Initial parameters to set
            
        Methods
        -------
        ptset : set parameters (with checking)
        ptadd : add new parameters (only way to add new parameters in strict mode)
        ptsu : set parameters silently (no checking, warnings or errors)
        ptshow : show current parameters being tracked

        """
        self.ptnote = ptnote
        self.ptstrict = False  # This is initially set to False to allow setting in ptset on initialization
        self.pterr = pterr
        self.ptverbose = ptverbose
        self._internal_parset = set()
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
            elif key in self._internal_parset:
                oldval = copy(getattr(self, key))
                setattr(self, key, val)
                if self.ptverbose:
                    print(f"Resetting parameter '{key}' as <{type(val).__name__}>:  {val}     [previous value <{type(oldval).__name__}>: {oldval}]")
            elif self.ptstrict:
                if self.pterr:
                    raise ParameterTrackError(f"Unknown parameter '{key}' in strict mode.")
                else:
                    Warning(f"Unknown parameter '{key}' in strict mode -- ignored.  Use ptadd to add new parameters.")
            else:
                setattr(self, key, val)
                self._internal_parset.add(key)
                if self.ptverbose:
                    print(f"Setting parameter '{key}' as <{type(val).__name__}>:  {val}")

    def ptadd(self, **kwargs):
        """
        Add new parameters to the parameter tracking -- only way to add new parameters if ptstrict is True.

        If ptstrict is False, then this is equivalent to ptset.

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
                self._internal_parset.add(key)
                if self.ptverbose:
                    print(f"Adding parameter '{key}' as <{type(val).__name__}>:  {val}")

    def ptsu(self, **kwargs):
        """
        This sets parameters with no checking, warnings or errors (except for methods) and no verbosity.

        This is the only way to set internal parameters if needed.

        Parameters
        ----------
        kwargs : key, value pairs
            Parameters to set in superuser mode

        """
        for key, val in kwargs.items():
            if key in self._internal_only_ptmethods:
                Warning(f"Attempt to set internal method '{key}' -- ignored.")
            else:
                setattr(self, key, val)
                if key not in self._internal_only_ptvar:
                    self._internal_parset.add(key)

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
        s += f"ptstrict: {self.ptstrict}, pterr: {self.pterr}, ptverbose: {self.ptverbose}\n"
        for key in sorted(self._internal_parset):
            val = getattr(self, key, None)
            s += f"  {key} <{type(val).__name__}> : {val}\n"
        if return_only:
            return s.strip()
        print(s.strip())