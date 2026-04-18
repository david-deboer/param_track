import builtins
import types

# Get all attributes from the builtins module
all_builtins = dir(builtins)

# Filter for objects that are types or classes, excluding exceptions and some internal types
builtin_types = []
for name in all_builtins:
    obj = getattr(builtins, name)
    # Check if it's a type and not an exception (which are also types/classes)
    if isinstance(obj, type) and not issubclass(obj, BaseException): # and obj is not types.BuiltinImporter:
        builtin_types.append(obj)

# Sort the types alphabetically by name
builtin_types.sort(key=lambda x: x.__name__)

# Print the names of the built-in types
for builtin_type in builtin_types:
    print(builtin_type.__name__)

