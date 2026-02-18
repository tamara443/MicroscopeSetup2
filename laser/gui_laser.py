from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QComboBox, QSpinBox
from PyQt5.QtWidgets import QTreeWidgetItem
import _ctypes
import os
import sys
import ctypes

currDir = os.path.dirname(os.path.abspath(__file__))
wrapperPath = os.path.join(currDir, "NKTPDLLwrapper")
dll_path = os.path.join(currDir, "NKTPDLL\\x64\\NKTPDLL.dll")
sys.path.append(wrapperPath)

from NKTPDLLwrapper import NKTPDLLWrapper  # Import the NKTPDLLWrapper class from the provided module


class NKTPDLLGUI(QWidget):
    def __init__(self, NKTPDLLWrapper):
        super().__init__()

        self.wrapper = NKTPDLLWrapper
        # Add a name attribute for the GUI object
        self.name = "NKTPDLLGUI"

        # Initialize the NKTPDLLWrapper
        portname = 'COM3'
        self.wrapper = NKTPDLLWrapper

        # Set up the UI
        layout = QVBoxLayout()

        self.status_label = QLabel('Status: Ready')
        layout.addWidget(self.status_label)

        # Power Level
        self.power_level_spinbox = QSpinBox()
        self.power_level_spinbox.setRange(0, 1000)
        self.power_level_spinbox.setValue(200)
        self.set_power_level_button = QPushButton('Set Power Level')
        self.set_power_level_button.clicked.connect(self.set_power_level)

        # #Swp level
        # self.swp_spinbox = QSpinBox()
        # self.swp_spinbox.setRange(0, 10000) # set the allowed range for the SWP value
        # self.swp_spinbox.setValue(1200) # set the initial value for the SWP value
        # self.set_swp_button = QPushButton('Set SWP Value') # create a button to set the new SWP value
        # self.set_swp_button.clicked.connect(self.set_swp_value) # connect the button to the function that sets the SWP value
        # layout.addWidget(QLabel('SWP Value (tenths of a nm):'))
        # layout.addWidget(self.swp_spinbox)
        # layout.addWidget(self.set_swp_button)

        # Desired Wavelength
        self.desired_wavelength_input = QLineEdit('100')
        layout.addWidget(QLabel('Desired Wavelength (nm):'))
        layout.addWidget(self.desired_wavelength_input)
        self.set_desired_wavelength_button = QPushButton('Set Desired Wavelength')
        layout.addWidget(self.set_desired_wavelength_button)
        self.set_desired_wavelength_button.clicked.connect(self.set_desired_wavelength)

        layout.addWidget(QLabel('Power Level (tenths of a percent):'))
        layout.addWidget(self.power_level_spinbox)
        layout.addWidget(self.set_power_level_button)

        # Emission Control
        self.emission_on_button = QPushButton('Emission On')
        self.emission_on_button.clicked.connect(self.emission_on)
        self.emission_off_button = QPushButton('Emission Off')
        self.emission_off_button.clicked.connect(self.emission_off)

        layout.addWidget(QLabel('Emission Control:'))
        layout.addWidget(self.emission_on_button)
        layout.addWidget(self.emission_off_button)

        # Read Register
        self.module_address_input = QLineEdit('0x10')
        self.reg_id_input = QLineEdit('0x32')
        self.index_input = QLineEdit('-1')
        self.read_register_button = QPushButton('Read Register')
        self.read_register_button.clicked.connect(self.read_register)
        self.register_value_label = QLabel('Register Value:')

        layout.addWidget(QLabel('Module Address:'))
        layout.addWidget(self.module_address_input)
        layout.addWidget(QLabel('Register ID:'))
        layout.addWidget(self.reg_id_input)
        layout.addWidget(QLabel('Index:'))
        layout.addWidget(self.index_input)
        layout.addWidget(self.read_register_button)
        layout.addWidget(self.register_value_label)

        self.setLayout(layout)
        self.swp_status = ""
        self.lwp_status = ""

    def setup_figure(self):
        pass

    def set_power_level(self):
        module_address = 0x0F  # or the appropriate module address for your device
        reg_id = 0x37  # or the appropriate register ID for your device
        power_level = self.power_level_spinbox.value()
        result = self.wrapper.set_power_level(module_address, reg_id, power_level)
        if result == 0:
            self.status_label.setText(f"Status: New power level set to {power_level / 10.0}%")
        else:
            self.status_label.setText("Status: Error setting new power level")

    def emission_on(self):
        module_address = 0x0F  # or the appropriate module address for your device
        reg_id = 0x30  # register ID for controlling the emission state
        state = 3  # value for turning emission on
        result = self.wrapper.set_emission_state(module_address, reg_id, state)
        if result == 0:
            self.status_label.setText("Status: Emission turned on")
        else:
            self.status_label.setText("Status: Error turning emission on")

    def set_desired_wavelength(self):
        try:
            desired_wavelength = float(self.desired_wavelength_input.text())
        except ValueError:
            self.status_label.setText("Status: Invalid desired wavelength value")
            return

        # Validate the desired_wavelength value if needed
        if desired_wavelength < 395 or desired_wavelength > 850:
            self.status_label.setText("Status: Desired wavelength is out of range")
            return

        swp_value = int((desired_wavelength + 5) * 10)  # Convert to tenths of a nm
        lwp_value = int((desired_wavelength - 5) * 10)  # LWP SWP calculation

        # Set SWP and LWP values
        self.set_swp_value(swp_value)
        self.set_lwp_value(lwp_value)
        self.status_label.setText(f"Status: {self.swp_status}; {self.lwp_status}")

    # def set_swp_value(self, swp_value):
    #     module_address = 0x10 # module address for SuperK VARIA (A301)
    #     reg_id = 0x33 # register ID for SWP setpoint
    #     index = -1 # index of the register (usually -1)
    #     result, swp_value_read = self.wrapper.write_register(module_address, reg_id, swp_value, index)
    #     if result == 0:
    #         self.status_label.setText(f"Status: New SWP value set to {swp_value/10.0} nm")
    #     else:
    #         self.status_label.setText("Status: Error setting new SWP value")

    def set_swp_value(self, swp_value):
        module_address = 0x10  # module address for SuperK VARIA (A301)
        reg_id = 0x33  # register ID for SWP setpoint
        index = -1  # index of the register (usually -1)
        result, swp_value_read = self.wrapper.write_register(module_address, reg_id, swp_value, index)
        if result == 0:
            self.swp_status = f"New SWP value set to {swp_value / 10.0} nm"
        else:
            self.swp_status = f"Error setting new SWP value: {result}"

    # def set_lwp_value(self, lwp_value):
    #     module_address = 0x10 # module address for SuperK VARIA (A301)
    #     reg_id = 0x34 # register ID for LWP setpoint
    #     index = -1 # index of the register (usually -1)
    #     result, lwp_value_read = self.wrapper.write_register(module_address, reg_id, lwp_value, index)
    #     if result == 0:
    #         self.status_label.setText(f"Status: New LWP value set to {lwp_value/10.0} nm")
    #     else:
    #         self.status_label.setText("Status: Error setting new LWP value")

    def set_lwp_value(self, lwp_value):
        module_address = 0x10  # module address for SuperK VARIA (A301)
        reg_id = 0x34  # register ID for LWP setpoint
        index = -1  # index of the register (usually -1)
        result, lwp_value_read = self.wrapper.write_register(module_address, reg_id, lwp_value, index)
        if result == 0:
            self.lwp_status = f"New LWP value set to {lwp_value / 10.0} nm"
        else:
            self.lwp_status = f"Error setting new LWP value: {result}"

    def emission_off(self):
        module_address = 0x0F  # or the appropriate module address for your device
        reg_id = 0x30  # register ID for controlling the emission state
        state = 0  # value for turning emission off
        result = self.wrapper.set_emission_state(module_address, reg_id, state)
        if result == 0:
            self.status_label.setText("Status: Emission turned off")
        else:
            self.status_label.setText("Status: Error turning emission off")

    def read_register(self):
        module_address = int(self.module_address_input.text(), 16)
        reg_id = int(self.reg_id_input.text(), 16)
        index = int(self.index_input.text())
        result, register_value = self.wrapper.read_register(module_address, reg_id, index)
        if result == 0:
            self.register_value_label.setText(f"Register Value: {register_value / 10.0}%")
            self.status_label.setText("Status: Register value read successfully")
        else:
            self.status_label.setText(f"Status: Error reading register value: {result}")

    def add_widgets_to_tree(self, tree):
        laser_item = QTreeWidgetItem(tree)
        # laser_item.setText(0, "Laser Control")

        tree.setItemWidget(laser_item, 0, self)


if __name__ == '__main__':
    # Initialize the NKTPDLLWrapper
    portname = 'COM3'
    NKTPDLLWrapper = NKTPDLLWrapper(dll_path, portname)

    # Create and show the PyQt5 application
    app = QApplication(sys.argv)
    window = NKTPDLLGUI(NKTPDLLWrapper)
    window.setWindowTitle('NKTPDLL GUI')
    window.show()
    sys.exit(app.exec_())
