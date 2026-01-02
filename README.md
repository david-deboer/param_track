# Parameter Tracking

General parameter tracking class to keep track of groups of parameters within a class with some minor checking and viewing - typically will only use the wrapper functions `ptset` and `ptshow`.

To use, include the import:

```from param_track import Parameters```

then, e.g.,

```mypar = Parameters(ptnote="These are my parameters", par1='Hello World!')```

will print (if `ptverbose` is True)

```Setting parameter 'par1' as <str>:  Hello World!```

and may be viewed via:

```
>>> mypar.ptshow()
Parameter Tracking: These are my parameters
(ptstrict: True, pterr: False, ptverbose: True, pttype: False)
  par1 <str> : Hello World!
```

If used as a parent Class, then child Classes can define their own parameters in their __init__ methods before calling the parent Class __init__ method.  If additional checking is needed for specific parameters, then the child Class can override the `ptset` method to do custom checking, then call the parent Class _pt_set method to do the actual setting.

The arguments of `Parameters` are:

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
        kwargs : key, value pairs
            Initial parameters to set
            
        Methods
        -------
        ptset : set parameters (with some checking)
        ptadd : add new parameters (only way to add new parameters in strict mode)
        ptsu : set parameters silently (no checking, warnings or errors, except for methods)
        ptshow : show current parameters being tracked

