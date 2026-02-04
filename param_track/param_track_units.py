class Units:
    def __init__(self, use_units=None):
        self.use_units = use_units
        self.unit_handler = None

    def handle_units(self, unit_handler):
        if not bool(unit_handler):
            self.use_units = False
            self.unit_handler = None
        else:
            self.use_units = True
            self.unit_handler = unit_handler

    def setattr(self, obj, key, val):
        print(f"IMPLEMENTING SETTING {key} TO {val} WITH UNITS...in progress")
        if not self.use_units:
            self.val = val
            setattr(obj, key, val)
        else:
            if key in self.unit_handler:
                print("Applying unit to value...")
                print("Lot's more to do here...")
                unit = self.unit_handler[key]
                val = val * unit
            self.val = val
            setattr(obj, key, val)