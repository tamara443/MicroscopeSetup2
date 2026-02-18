from ScopeFoundry import HardwareComponent
import pyvisa
import time


class Yokogawa_HW_2 (HardwareComponent):
    def setup(self):
        self.name = "YokogawaGS200_2"

        self.settings.New(name="SourceMode", initial="Voltage", dtype=str, choices=("Voltage", "Current"))
        self.settings.New(name="Range", initial="1 V", dtype=str,
                          choices=("1 mA", "200 mA", "10 mV/mA", "100 mV/mA", "1 V", "10 V", "30 V"))
        self.settings.New(name="Limitlevel", initial=0.2, vmin=0.001, vmax=0.2, dtype=float)
        self.settings.New(name='Sourcelevel', initial=0.0, vmin=-1, vmax=1, dtype=float)
        self.settings.New(name="IntgTime", initial=1, vmin=1, vmax=25, dtype=int)
        self.settings.New(name="Delay", initial=0.0, vmin=0.0, vmax=999999.0, dtype=float)
        self.settings.New(name="OnOff", initial="OFF", dtype=str, choices=("ON", "OFF"))

        # Attach a callback to the Range setting
        self.settings.Range.add_listener(self.update_sourcelevel_limits)

    def connect(self):
        # Establish the device connection through PyVisa
        self.rm = pyvisa.ResourceManager()
        addr = "USB0::0x0B21::0x0039::9012F0566::INSTR"
        try:
            self.yokogawa_2 = self.rm.open_resource(addr)
            time.sleep(0.025)
            self.yokogawa_2.write('*RST')
            time.sleep(0.025)
            self.setTrigger("MEND")
            time.sleep(0.025)
            self.setMeasurementTrigger("ready")
            print("Yokogawa GS200 ready")
        except Exception as error:
            print("An error occurred:", type(error).__name__, "–", error)

        # Initial measurement
        self.read_from_hardware()

    def disconnect(self):
        self.settings.disconnect_all_from_hardware()

        # Don't just stare at it, clean up your objects when you're done!
        if hasattr(self, 'yokogawa'):
            self.yokogawa_2.close()
            del self.yokogawa_2
        print("YokogawaGS200_2 is disconnected")

    def IdentifyDevice(self):
        print(self.yokogawa_2.query("*IDN?"))

    def ResetDevice(self):
        self.yokogawa_2.write("*RST")
        print("Device Reset")

    def setOutput(self, outputMode):
        if outputMode == "ON":
            self.yokogawa_2.write(":OUTP 1")
        elif outputMode == "OFF":
            self.yokogawa_2.write(":OUTP 0")
        else:
            raise ValueError("Wrong parameter input")

    def setSourceLevel(self, level):
        self.Sourcelevel = level
        self.yokogawa_2.write(":SOUR:LEV " + str(self.Sourcelevel))
    def setMode(self, mode):
        self.mode = mode
        if self.mode == "Voltage":
            self.yokogawa_2.write(":SOUR:FUNC VOLT")
            print("Voltage Mode")
        elif self.mode == "Current":
            self.yokogawa_2.write(":SOUR:FUNC CURR")
            print("Current Mode")

    def setSourceRange(self, range):
        self.range = range

        if self.range == "10 mA":
            self.yokogawa_2.write(":SOUR:RANG 1E-3")
        elif self.range == "200 mA":
            self.yokogawa_2.write(":SOUR:RANG 200E-3")
        elif self.range == "10 mV/mA":
            self.yokogawa_2.write(":SOUR:RANG 10E-3")
        elif self.range == "100 mV/mA":
            self.yokogawa_2.write(":SOUR:RANG 100E-3")
        elif self.range == "1 V":
            self.yokogawa_2.write(":SOUR:RANG 1E+0")
        if self.range == "10 V":
            self.yokogawa_2.write(":SOUR:RANG 10E+0")
        elif self.range == "30 V":
            self.yokogawa_2.write(":SOUR:RANG 30E+0")

    # def setLimit(self, limit):
    def setMeasurement(self, measMode):
        self.measMode = measMode

        if self.measMode == 1:
            self.yokogawa_2.write(":SENS 1")
        elif self.measMode == 0:
            self.yokogawa_2.write(":SENS 0")

    def setLimit(self, limit, mode):
        self.limit = limit
        self.mode = mode

        if self.mode == "Voltage":
            self.yokogawa_2.write(":SOUR:PROT:CURR " + str(limit))
        elif self.mode == "Current":
            self.yokogawa_2.write(":SOUR:PROT:VOLT " + str(limit))

    def setTrigger(self,trigger):
        self.trigger = trigger
        if self.trigger == "normal":
            self.yokogawa_2.write(":PROG:TRIG NORM")
        elif self.trigger == "MEND":
            self.yokogawa_2.write(":PROG:TRIG MEND")

    def setMeasurementTrigger(self, measTrig):
        self.measTrig = measTrig
        if self.measTrig == "ready":
            self.yokogawa_2.write(":SENS:TRIG READ")
        elif self.measTrig == "timer":
            self.yokogawa_2.write(":SENS:TRIG TIM")
        elif self.measTrig == "communicate":
            self.yokogawa_2.write(":SENS:TRIG COMM")
        elif self.measTrig == "immediate":
            self.yokogawa_2.write(":SENS:TRIG IMM")

    def readLineData(self, readMode):
        self.readMode = readMode
        if self.readMode == "initiate":
            return self.yokogawa_2.query(":INIT")
        elif self.readMode == "fetch":
            return self.yokogawa_2.query(":FETC?")
        elif self.readMode == "read":
            return self.yokogawa_2.query(":READ?")
        elif self.readMode == "measure":
            return self.yokogawa_2.query(":MEAS?")

    def readBufferData(self):
        return self.yokogawa.query(":TRAC:DATA:READ MF")

    def setStorage(self, storage):
        self.storage = storage
        if self.storage == "on":
            self.yokogawa_2.write(":TRAC ON")
        elif self.storage == "off":
            self.yokogawa_2.write(":TRAC OFF")

    def setDelay(self, Delay):
        self.Delay = Delay
        self.yokogawa_2.write(":SENS:DEL " + str(self.Delay))

    def setIntgTime(self, integration_time):
        self.IntgTime = integration_time
        self.yokogawa_2.write(":SENS:NPLC " + str(self.IntgTime))

    def update_sourcelevel_limits(self):
        # Adjust vmin and vmax of Sourcelevel based on the current Range value
        range_value = self.settings.Range.value
        if range_value == "1 mA":
            vmin, vmax = -0.001, 0.001
        elif range_value == "200 mA":
            vmin, vmax = -0.2, 0.2
        elif range_value == "10 mV/mA":
            vmin, vmax = -0.01, 0.01
        elif range_value == "100 mV/mA":
            vmin, vmax = -0.1, 0.1
        elif range_value == "1 V":
            vmin, vmax = -1.0, 1.0
        elif range_value == "10 V":
            vmin, vmax = -10.0, 10.0
        elif range_value == "30 V":
            vmin, vmax = -30.0, 30.0
        else:
            # Default limits if range is not recognized
            vmin, vmax = -0.2, 0.2

        # Update Sourcelevel's vmin and vmax with the new limits
        self.settings.Sourcelevel.change_min_max(vmin, vmax)
