from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from keithley2600 import Keithley2600

class Keithley_Measurement(Measurement):
    def setup(self):
        self.name = "Keithley_Measurement"
        self.ui_filename = sibling_path(__file__, "strommesser.ui")
        self.ui = load_qt_ui_file(self.ui_filename)
        #self.keithi = Keithley2600(addr="GPIB0::26::INSTR", visa_library="")

        self.display_update_period = 0.1
        self.keithley = self.app.hardware['Keithley2601A']

    def setup_figure(self):
        print("ko")
        # Connect settings to UI
        #self.smu.voltage.connect_to_widget(self.ui.setVoltage_spinBox)
        #self.smu.current.connect_to_widget(self.ui.setCurrent_spinBox)
        self.ui.setVoltage_pushButton.clicked.connect(lambda: self.keithley.get_voltage())
        #self.ui.IDN_pushButton.clicked.connect(self.identify_device())


    #
    #
    # # Reset
    # def reset_keith(self):
    #     self.keith_visa.write("*RST")
    #     print("Reset OK")
    # # Identification
    # def identify_device(self):
    #     return self.keith_visa.query("*IDN?")