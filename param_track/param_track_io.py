from param_track.param_track_support import ParameterTrackError

def to_file(data, filename, include_par=None, as_row=False):
    if filename.endswith('.csv'):
        _to_csv(data=data, filename=filename, include_par=include_par, as_row=as_row, include_header=True)
    elif filename.endswith('.json') or filename.endswith('.yaml') or filename.endswith('.yml'):
        _to_json_yaml(data=data, filename=filename, include_par=include_par)
    elif filename.endswith('.npz') or filename.endswith('.npy'):
        _to_npz(data=data, filename=filename, include_par=include_par)
    else:
        raise ParameterTrackError(f"Unsupported file format for parameter loading: {filename}")

def _to_npz(data, filename, include_par=None):
    this = data.pt_to_dict(serialize='pickle', include_par=include_par, what_to_dict='parameters')
    from numpy import savez
    savez(filename, data=this)

def _to_json_yaml(data, filename, include_par=None):
    if filename.endswith('.json'):
        import json
        this = data.pt_to_dict(serialize='json', include_par=include_par, what_to_dict='parameters')
    elif filename.endswith('.yaml'):
        import yaml
        this = data.pt_to_dict(serialize='yaml', include_par=include_par, what_to_dict='parameters')
    with open(filename, 'w') as fp:
        fp.write(this)

def _to_csv(data, filename=None, include_par=None, as_row=False, include_header=False):
    """
    Return the current parameters as a CSV string.

    Parameters
    ----------
    data : Class Parameters
        The Class containing the parameters to be converted to CSV
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
    
    this = data.pt_to_dict(serialize='json', include_par=include_par, what_to_dict='parameters')

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

    if filename is None:
        return buf.getvalue()
    else:
        with open(filename, 'w') as f:
            f.write(buf.getvalue())

def from_file(filename, as_row=False, use_key=None):
    """
    Set parameters from a file, depending on the format of the file.

    Currently csv, json, yaml and npy/z formats are supported.

    If json or yaml, then the file may have one of two formats (or mixture of the two):
    1 - key-value pairs of parameters to be set, e.g.:
        {
            "param1": value1,
            "param2": value2,
            ...
        }
    2 - key-dict pairs, where the dict has a key 'value' and an optional key 'units', e.g.:
        {
            "param1": {"value": value1, "units": "s"},
            "param2": {"value": value2},
            ...    
        }
    if the 'units' parameter is passed, it contains the units to be used for interpreting the parameter values,
    if the input file is in format 2, then the 'units' parameter is ignored for those parameters that have a 'units' key in the file.


    Parameters
    ----------
    filename : str
        Path to the file containing parameters
    as_row : False or int (CSV format only)
        If int, then read the CSV from row 'as_row' instead of key-value pairs
        and first line is header (works since row 0 is header)

    Returns
    -------
    dict
        Dictionary of parameters read from the file
    dict
        Dictionary of units for the parameters read from the file (if any)

    """
    if filename.endswith('.csv'):
        return _from_csv(filename, as_row=as_row)
    elif filename.endswith('.json') or filename.endswith('.yaml') or filename.endswith('.yml'):
        return _from_json_yaml(filename, use_key=use_key)
    elif filename.endswith('.npz') or filename.endswith('.npy'):
        return _from_npz(filename, use_key=use_key)
    raise ParameterTrackError(f"Unsupported file format for parameter loading: {filename}")

def _from_npz(filename, use_key=None):
    """Set parameters from a NPZ file (see from_file)."""
    import numpy as np
    npdata = np.load(filename, allow_pickle=True)
    data = {key: npdata[key].item() for key in npdata.files}
    if isinstance(use_key, str):
        if use_key not in data:
            raise ParameterTrackError(f"Key '{use_key}' not found in file {filename}.")
        data = data[use_key]
    units = {}
    return data, units

def _from_csv(filename, as_row=False):
    """Set parameters from a CSV file (see from_file)."""
    print("Units not currently supported for CSV input.")
    import csv
    if as_row:
        as_row = int(as_row)
    data = {}
    units = {}
    with open(filename, 'r') as fp:
        reader = csv.reader(fp)
        if as_row:
            keys = next(reader)
        for i, row in enumerate(reader):
            if as_row:
                if i != as_row-1:
                    continue
                for key, val in zip(keys, row):
                    data[key] = val
                break
            else:
                if len(row) != 2:
                    continue
                key, val = row
                data[key] = val
    return data, units

def _from_json_yaml(filename, use_key=None):
    """Set parameters from a JSON or YAML file (see from_file)."""
    with open(filename, 'r') as fp:
        if filename.endswith('.json'):
            import json
            data1 = json.load(fp)
        elif filename.endswith('.yaml') or filename.endswith('.yml'):
            import yaml
            data1 = yaml.safe_load(fp)
    data = {}
    units = {}
    if use_key is not None and use_key not in data1:
        raise ParameterTrackError(f"Key '{use_key}' not found in file {filename}.")
    if use_key is not None:
        data1 = data1[use_key]
    for key, val in data1.items():
        if isinstance(val, dict):
            hasterm = False
            if '__external__' in val and val['__external__'] is True:
                continue
            if 'unit' in val:
                hasterm = True
                units[key] = val['unit'] if isinstance(val['unit'], str) else f"[{str(val['unit'][0])}]"
                data[key] = None
            if 'value' in val:
                hasterm = True
                data[key] = val['value']
            if not hasterm:
                data[key] = val
        else:
            data[key] = val
    return data, units