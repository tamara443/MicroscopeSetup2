from ScopeFoundry import HardwareComponent
from keithley2600 import Keithley2600

import sys, os

keithley_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(keithley_path)
from keithley_interface import Keithley_Interface



class Keithley_HW(HardwareComponent):
    def setup(self):
        self.name = "Keithley2601A"


        self.settings.New(name='voltage', initial=7.0, dtype=float, ro=False)
        self.settings.New(name='current', initial=1.0, dtype=float, ro=False)

    def connect(self):
        # Open connection to the device:
        self.keith = Keithley_Interface()

        #self.settings.voltage.connect_to_hardware(set_v = self.keith.set_voltage)
        #self.settings.current.c

        self.read_from_hardware()


    # Measure Voltage
    def get_voltage(self):
        print(self.keith.measure_voltage(self.keith.smua))

    def disconnect(self):
        self.settings.disconnect_all_from_hardware()

        # Don't just stare at it, clean up your objects when you're done!
        if hasattr(self, 'keith'):
            del self.keith
