from ScopeFoundry import HardwareComponent
from pymeasure.instruments.signalrecovery import DSP7265

class LIA_HW(HardwareComponent):
    def setup(self):
        self.settings.New(name="Mode", initial="low noise current mode", dtype=str, choices=("voltage mode", "``current mode", "low noise current mode"))
        self.settings.New(name="Reference", initial="external front", dtype=str, choices=("internal", "external rear", "external front"))
        self.settings.New(name="Coupling", initial="AC", dtype=str, choices=("AC", "DC"))
        self.settings.New(name="Gain", initial=0, dtype=int)
        self.settings.New(name="AutoGain", initial="ON", dtype=str, choices=("ON", "OFF"))
        self.settings.New(name="Phase", initial=0, dtype=int, vmin=0, vmax=360)
        self.settings.New(name="Sensitivity", initial=0.0, dtype=float)

        self.name = "LIA7265"

    def connect(self):
        try:
            self.lia = DSP7265("GPIB::12::INSTR")
            print("LIA is ready")
        except Exception as error:
            print("An error occurred (Connect):", type(error).__name__, "–", error)

        self.read_from_hardware()

    def disconnect(self):
        self.settings.disconnect_all_from_hardware

        if hasattr(self, 'lia'):
            self.lia.shutdown()
            del self.lia
        print("LIA7265 is disconnected")

    def set_mode(self, mode):
        try:
            self.lia.imode = mode
        except Exception as error:
            print("An error occurred (Mode):", type(error).__name__, "–", error)

    def set_reference(self, reference):
        try:
            self.lia.reference = reference
        except Exception as error:
            print("An error occurred (Reference):", type(error).__name__, "–", error)

    def set_auto_gain(self, setting):
        try:
            if setting == "ON":
                self.lia.auto_gain = 1
            else:
                self.lia.auto_gain = 0
        except Exception as error:
            print("An error occurred (Auto_Gain):", type(error).__name__, "–", error)

    def set_auto_phase(self):
        try:
            self.lia.auto_phase()
        except Exception as error:
            print("An error occurred (Auto_phase):", type(error).__name__, "–", error)

    def set_auto_sensitivity(self):
        try:
            self.lia.auto_sensitivity()
        except Exception as error:
            print("An error occurred (Auto_Sensitivity):", type(error).__name__, "–", error)

    def set_gain(self, gain):
        try:
            if gain == 0:
                return
            self.lia.gain = gain
        except Exception as error:
            print("An error occurred (Gain):", type(error).__name__, "–", error)

    def set_coupling(self, coupling):
        try:
            data = 1
            if coupling == "AC":
                data = 0
            self.lia.coupling = data
        except Exception as error:
            print("An error occurred (Coupling):", type(error).__name__, "–", error)

    def measure_mag(self):
        try:
            mag = self.lia.mag
            # print("Magnitude: " + str(mag))
            return mag
        except Exception as error:
            print("An error occurred (Coupling):", type(error).__name__, "–", error)

    def set_sensitivity(self, sensitivity):
        try:
            if sensitivity == 0:
                return
            self.lia.sensitivity = sensitivity
        except Exception as error:
            print("An error occurred (Sensitivity):", type(error).__name__, "–", error)

    def set_phase(self, phase):
        try:
            if phase == 0:
                return
            self.lia.reference_phase = phase
        except Exception as error:
            print("An error occurred (Phase):", type(error).__name__, "–", error)

    def measure_phase(self):
        try:
            phase = self.lia.phase
            # print("Phase: " + str(phase))
            return phase
        except Exception as error:
            print("An error occurred (Read Phase):", type(error).__name__, "–", error)

    def measure_xy(self):
        try:
            xy = self.lia.xy
            print("XY is ready: " + str(xy))
            return xy
        except Exception as error:
            print("An error occurred (Read XY):", type(error).__name__, "–", error)