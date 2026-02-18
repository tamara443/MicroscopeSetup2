from ScopeFoundry import HardwareComponent
import pyvisa
import time


class Yokogawa_HW (HardwareComponent):
    def setup(self):
        self.name = "YokogawaGS200"

        self.settings.New(name="SourceMode", initial="Voltage", dtype=str, choices=("Voltage", "Current"))
        self.settings.New(name="Range", initial="10 V", dtype=str,
                          choices=("1 mA", "200 mA", "10 mV/mA", "100 mV/mA", "1 V", "10 V", "30 V"))
        self.settings.New(name="Limitlevel", initial=10.0, vmin=-30.0, vmax=30.0, dtype=float)
        self.settings.New(name='Sourcelevel', initial=1.0, vmin=-30.0, vmax=30.0, dtype=float)
        self.settings.New(name="IntgTime", initial=1, vmin=1, vmax=25, dtype=int)
        self.settings.New(name="Delay", initial=0.0, vmin=0.0, vmax=999999.0, dtype=float)


    def connect(self):
        # Establish the device connection through PyVisa
        self.rm = pyvisa.ResourceManager()
        addr = "USB0::0x0B21::0x0039::91U618773::INSTR"
        try:
            self.yokogawa = self.rm.open_resource(addr)
            time.sleep(0.025)
            self.yokogawa.write('*RST')
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
            self.yokogawa.close()
            del self.yokogawa


    def IdentifyDevice(self):
        print(self.yokogawa.query("*IDN?"))

    def ResetDevice(self):
        self.yokogawa.write("*RST")
        print("Device Reset")

    def setOutput(self, outputMode):
        if outputMode == 1:
            self.yokogawa.write(":OUTP 1")
        elif outputMode == 0:
            self.yokogawa.write(":OUTP 0")
        else:
            raise ValueError("Wrong parameter input")

    def setSourceLevel(self, level):
        self.Sourcelevel = level
        self.yokogawa.write(":SOUR:LEV " + str(self.Sourcelevel))
    def setMode(self, mode):
        self.mode = mode
        if self.mode == "Voltage":
            self.yokogawa.write(":SOUR:FUNC VOLT")
            print("Voltage Mode")
        elif self.mode == "Current":
            self.yokogawa.write(":SOUR:FUNC CURR")
            print("Current Mode")

    def setSourceRange(self, range):
        self.range = range

        if self.range == "10 mA":
            self.yokogawa.write(":SOUR:RANG 1E-3")
        elif self.range == "200 mA":
            self.yokogawa.write(":SOUR:RANG 200E-3")
        elif self.range == "10 mV/mA":
            self.yokogawa.write(":SOUR:RANG 10E-3")
        elif self.range == "100 mV/mA":
            self.yokogawa.write(":SOUR:RANG 100E-3")
        elif self.range == "1 V":
            self.yokogawa.write(":SOUR:RANG 1E+0")
        if self.range == "10 V":
            self.yokogawa.write(":SOUR:RANG 10E+0")
        elif self.range == "30 V":
            self.yokogawa.write(":SOUR:RANG 30E+0")

    # def setLimit(self, limit):
    def setMeasurement(self, measMode):
        self.measMode = measMode

        if self.measMode == 1:
            self.yokogawa.write(":SENS 1")
        elif self.measMode == 0:
            self.yokogawa.write(":SENS 0")

    def setLimit(self, limit, mode):
        self.limit = limit
        self.mode = mode

        if self.mode == "Voltage":
            self.yokogawa.write(":SOUR:PROT:VOLT " + str(limit))
        elif self.mode == "Current":
            self.yokogawa.write(":SOUR:FUNC:CURR " + str(limit))

    def setTrigger(self,trigger):
        self.trigger = trigger
        if self.trigger == "normal":
            self.yokogawa.write(":PROG:TRIG NORM")
        elif self.trigger == "MEND":
            self.yokogawa.write(":PROG:TRIG MEND")

    def setMeasurementTrigger(self, measTrig):
        self.measTrig = measTrig
        if self.measTrig == "ready":
            self.yokogawa.write(":SENS:TRIG READ")
        elif self.measTrig == "timer":
            self.yokogawa.write(":SENS:TRIG TIM")
        elif self.measTrig == "communicate":
            self.yokogawa.write(":SENS:TRIG COMM")
        elif self.measTrig == "immediate":
            self.yokogawa.write(":SENS:TRIG IMM")

    def readLineData(self, readMode):
        self.readMode = readMode
        if self.readMode == "initiate":
            return self.yokogawa.query(":INIT")
        elif self.readMode == "fetch":
            return self.yokogawa.query(":FETC?")
        elif self.readMode == "read":
            return self.yokogawa.query(":READ?")
        elif self.readMode == "measure":
            return self.yokogawa.query(":MEAS?")

    def readBufferData(self):
        return self.yokogawa.query(":TRAC:DATA:READ MF")

    def setStorage(self, storage):
        self.storage = storage
        if self.storage == "on":
            self.yokogawa.write(":TRAC ON")
        elif self.storage == "off":
            self.yokogawa.write(":TRAC OFF")

    def setDelay(self, Delay):
        self.Delay = Delay
        self.yokogawa.write(":SENS:DEL " + str(self.Delay))

    def setIntgTime(self, integration_time):
        self.IntgTime = integration_time
        self.yokogawa.write(":SENS:NPLC " + str(self.IntgTime))


