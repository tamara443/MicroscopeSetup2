import pyvisa

# Declare important object variables
device_addr = "USB0::0x0B21::0x0039::91U618773::INSTR"
class YokogawaGS200SMU(object):
    def __init__(self, addr=device_addr, debug=False, name=None):
        self.addr = addr
        self.rm = pyvisa.ResourceManager()


        # try self.yokogawa = self.rm.open_resource(addr): ????
        try:
            self.yokogawa = self.rm.open_resource(addr)
            #print(self.yokogawa.write('*RST'))
            print(self.yokogawa.query('*IDN?'))
            print("Yokogawa GS200 connected")
        except Exception as error:
            print("An error occurred:", type(error).__name__, "–", error)