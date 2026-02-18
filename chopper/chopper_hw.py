from ScopeFoundry import HardwareComponent
"""try:
    import MC2000B_COMMAND_LIB as MCLib
except Exception as err:
    print("Cannot load required modules for Chopper:", err)"""

import os
import sys
import ctypes

# Get the directory of the current file
current_dir = os.path.dirname(os.path.abspath(__file__))

# Add that directory to sys.path
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Now import the library
import MC2000B_COMMAND_LIB as MCLib

class Chopper_HW(HardwareComponent):
    def setup(self):

        self.settings.New(name="BladeType", initial="MC1F10HP", dtype=str, choices=("MC1F10HP", "MC1F2"))
        self.settings.New(name="Frequency", initial=0, dtype=int)
        self.settings.New(name="OnOff", initial="OFF", dtype=str, choices=("ON", "OFF"))

        self.name = "MC2000B"

    def connect(self):
        devices = MCLib.MC2000BListDevices()
        print(devices)
        try: 
            com_port = devices [2][0] # Extract 'COM4' from second device
            self.chopper = MCLib.MC2000BOpen(com_port, nBaud=115200, timeout=3)
            print("Chopper is ready")
        except Exception as error:
            print("An error occurred (Connect):", type(error).__name__, "–", error)

        self.read_from_hardware()

    def disconnect(self):
        self.settings.disconnect_all_from_hardware

        if hasattr(self, 'chopper'):
            MCLib.MC2000BClose(self.chopper)
            del self.chopper
        print("MB2000B is disconnected")

    def set_frequency(self, freq):
        try:
            MCLib.MC2000BSetFrequency(self.chopper, freq)
        except Exception as error:
            print("An error occurred (Frequency):", type(error).__name__, "–", error)

    def set_bladetype(self, bladetype):
        try:
            MCLib.MC2000BSetBladeType(self.chopper, bladetype)
        except Exception as error:
            print("An error occurred (Blade Type):", type(error).__name__, "–", error)
    def enable(self, enable):
        try:
            MCLib.MC2000BSetEnable(self.chopper, enable)
        except Exception as error:
            print("An error occurred (Blade Type):", type(error).__name__, "–", error)

    def get_frequency(self):
        frequency=[0]
        result=MCLib.MC2000BGetReferenceOutFrequency(self.chopper, frequency)
        if(result<0):
            print("Get Frequency fail",result)
        else:
            print("Get Frequency :",frequency)
        return frequency
