import pyvisa
from time import sleep, time


# Declare important object variables
device_addr = "USB0::0x0B21::0x0039::9012F0566::INSTR"
rm = pyvisa.ResourceManager()
print(rm.list_resources())
yokogawa = rm.open_resource(device_addr)
print(yokogawa.query('*IDN?'))
yokogawa.write('*RST')

# Source Setup
yokogawa.write(":SOUR:FUNC VOLT")
yokogawa.write(":SOUR:RANG 30")
yokogawa.write(":SOUR:LEV 30")
yokogawa.write(":OUTP 1")

start_time = time()

for i in range(10):
    # yokogawa.write(":OUTP 1")
    yokogawa.write(":SENS 1")
    sleep(0.03)
    print(yokogawa.query(":READ?"))
    measurement_time = time() - start_time
    print(f"Measurement time: {measurement_time}")
    sleep(0.03)
    # yokogawa.write(":OUTP 0")

yokogawa.write(":OUTP 0")
