# Parameter Tracking

General parameter tracking class to keep track of groups of parameters within a class with some minor checking and viewing - typically will only use the wrapper function `ptset` and `ptshow`.

Adding or setting a parameter via one of the methods `__init__`, `ptset`, `_pt_set`, `ptinit`, `ptadd` or `ptsu` will make that an attribute of the Class and will register its type (units and types are handled in a separate Class `param_track_units.Units`).  The multitude of methods may seem confusion, but basically boils down to initialization and setting (`ptset`).  `ptadd` lets you add a new parameter in "strict" mode and `ptsu` lets you update the internal parameters.

Parameters may be installed as:

```
pip install https://github.com/david-deboer/param_track
```

Setting a parameter will add that attribute to the Class and keep track of both it and its type (sometimes you care about type and sometimes not, which is settable).

`Parameters` has some internal attributes to govern how it functions (so these can't be used as parameters by the user).  Similarly, the internal methods can't be used as parameters. The internal `ptset`/`_pt_set`, `ptadd` and `ptsu` methods should be used to add parameters to check against the various constraints and to properly track.



###Internal Parameters
The internal parameters (all bools except ptnote and ptsetunits) are:

- ptnote : Note to describe the parameter tracking instance, used in ptshow
- ptstrict : Flag to make parameter setting strict (i.e. error or warn on unknown parameters)
- pterr : Flag to make parameter setting raise ParameterTrackError on unknown parameters in strict mode or just print a warning
- ptverbose : Flag to make parameter setting verbose
- pttype : Flag to check parameter type in `_pt_set` (not used in `ptadd` or `ptsu`)
- pttypeerr : Flag to make parameter setting raise ParameterTrackError on type change or just print a warning.
- ptsetunits : False or a unit\_handler (see param\_track\_units.py for details)

###Internal Methods
The internal methods are (ones that add/edit are marked with *):

- ptinit* : initialize parameters from a list of keys to default value or with a file ...
- ptset* : set parameters (with strict and type checking)
- ptadd* : add new parameters (only way to add new parameters in strict mode)
- ptsu* : can change internal parameters
- ptfrom : set parameters from a file (CSV, JSON or YAML formats supported, set by filename extension)
- ptget : get parameter value
- ptdel : delete parameters
- ptshow : show current parameters being tracked
- ptlog : show or search the log
- ptto : write parameters to a file (CSV, JSON or YAML formats supported, set by filename extension)
- pt\_to\_dict : return current parameters as a dictionary (or serialized form), plus options for types or internal parameters

To use, include the import:

```from param_track import Parameters```

You can then use `Parameters` either as:

	- a Parent class;
	- a new Instance to group (or keep separate) the parameters from your module.

## Parameters as a Parent Class
This approach will incorporate the Parameters attributes into the Child Class.  If the Chilld Class is very big, this can get confusing to make sure that you don't inadvertantly overwrite a Parameters attribute.  In that case, it might be best to use it as a new Instance (below).

This is done in the standard way in your Class declaration.

`class myClass(Parameters):`

`Parameters` is then ready to use in a very loose but chatty mode (all bools are False, except `ptverbose`).  For more structure, it is good to initialize and set ptstrict to True.

Inititalization my be done via essentially any setting method, but principally via one of these two:

- `super.__init__(par='A Parameter, **kwargs)`  # note that `ptstrict` gets set to True as default.  This assumes the Child class `__init__` has `**kwargs` in it.
- `self.ptinit(ptstrict=True, ptinit=['A', 'B', 'C'], par='A Parameter')`

Initialization uses `ptsu`. The structure of those two differ slightly to allow `ptinit` to initialize a list of parameters to a default value (which defaults to None).  Basically, pick an approach and stick with it.  Also note that `ptinit` is a method, but also used as an intra-method variable.

After initialization, one should generally use `ptset` to interact with the parameters, or create a new wrapper to set.  Note that `ptset` is just a wrapper around `_pt_set` and one may wish to write a more comprehensive checker/wrapper that gets called and then it calls `_pt_set`.  This could be called `ptset`, but could also just be `set` or `update`...

## Parameters as a new Instance

This is useful to group a set of parameters together, and also not get "in the way" of Child Class attributes. 

`myconfig = Parameters('These are my config parameters', ptinit=['a', 'b', 'c'], d='data')`
`mystate = Parameters('These are my state parameters', status='Good', runtime=0.0)`

Obviously, these are now initialized via the `Parameters` `__init__()` method.
