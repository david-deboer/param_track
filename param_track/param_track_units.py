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
        print(f"SETTING {key} TO {val} WITH UNITS")
        if not self.use_units:
            self.val = val
            setattr(obj, key, val)
        else:
            print("THIS IS WHERE UNITS GET SET...")