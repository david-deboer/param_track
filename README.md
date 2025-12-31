Parameter Tracking

General parameter tracking class to keep track of groups of parameters within a class with some minor checking and viewing - typically will only use the wrapper functions `ptset` and `ptshow`.

If used as a parent Class, then child Classes can define their own parameters in their __init__ methods before calling the parent Class __init__ method.  If additional checking is needed for specific parameters, then the child Class can override the `ptset` method to do custom checking, then call the parent Class _pt_set method to do the actual setting.
        
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

