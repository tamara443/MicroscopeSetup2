from ScopeFoundry import HardwareComponent
import seabreeze
import libusb_package
import usb.core, usb.backend.libusb1
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
libusb1_backend = usb.backend.libusb1.get_backend(find_library=libusb_package.find_library)
seabreeze.use('pyseabreeze')
from seabreeze.spectrometers import list_devices, Spectrometer

class OceanOpticsHW(HardwareComponent):
    
    def setup(self):
        # Define your hardware settings here.
        # These settings will be displayed in the GUI and auto-saved with data files
        self.name = 'oceanoptics'
        self.settings.New('intg_time', dtype=int, unit='ms', initial=6, vmin=6)
        self.settings.New('correct_dark_counts', dtype=bool, initial=False)

    def connect(self):
        # Open connection to the device:
        devices = list_devices()

        try:
            self.spec = Spectrometer(devices[0])
        except Exception as error:
            print("Spectrometer connection failed: ", type(error).__name__, "–", error)

        #Connect settings to hardware:
        self.settings.intg_time.connect_to_hardware(
            self.spec.integration_time_micros(self.settings['intg_time']*10000))
    
        #Take an initial sample of the data.
        self.read_from_hardware()
        
    def disconnect(self):
        #Disconnect the device and remove connections from settings
        self.settings.disconnect_all_from_hardware()
        if hasattr(self, 'spec'):
            self.spec.close()
            del self.spec
            self.spec = None