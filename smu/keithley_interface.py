from keithley2600 import Keithley2600
import pyvisa

class Keithley2600SMU(object):
    def __init__(self, addr="GPIB0::26::INSTR", debug=False, name=None):
        self.addr = addr
        self.rm = pyvisa.ResourceManager()
        self.keith_visa = self.rm.open_resource(addr)
        self.keith = Keithley2600(addr, visa="")

        if self.keith.connected:
            print("Keithley 2601A ready")
        else:
            print("Keithley 2601A NOT ready")

    # Set Voltage
    def set_voltage(self, voltage):
        self.voltage = voltage
        self.keith.apply_voltage(self.keith.smua, self.voltage)
    # Set Current
    def set_current(self, current):
        self.current = current
        self.keith.apply_current(self.keith.smua, self.current)
    # Measure Voltage
    def get_voltage(self):
        return self.keith.measure_voltage(self.keith.smua)
    # Measure Current
    def get_current(self):
        return self.keith.measure_current(self.keith.smua)

    # Voltage Sweep
    def voltage_sweep(self, voltageRange, integration_time, delaySweep, pulsedMode):
        self.voltageRange = voltageRange
        self.delaySweep = delaySweep
        self.pulsedMode = pulsedMode
        return self.keith.voltage_sweep_single_smu(self.keith.smua,  self.voltageRange, self.intg_time, self.delaySweep, self.pulsedMode)

    # Ramp to voltage
    # def voltage_Ramp(self, targetVoltage, stepSize, delayRamp):
    #     self.targetVoltage = targetVoltage
    #     self.stepSize = stepSize
    #     self.delayRamp = delayRamp
    #     self.keith.ramp_to_voltage(self.keith.smua, self.targetVoltage, self.stepSize, self.delayRamp)

    # Integrationtime
    def set_intg_time_keith(self, integration_time):
        self.intg_time = float(integration_time)
        self.keith.set_integration_time(self.keith.smua, self.intg_time)

    # Reset
    def reset_keith(self):
        self.keith_visa.write("*RST")
        print("Reset OK")
    # Identification
    def identify_device(self):
        return self.keith_visa.query("*IDN?")