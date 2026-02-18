import pyvisa
from time import sleep

# Declare important object variables
device_addr = "USB0::0x0B21::0x0039::9012F0566::INSTR"
rm = pyvisa.ResourceManager()
print(rm.list_resources())
yokogawa = rm.open_resource(device_addr)
print(yokogawa.query('*IDN?'))
yokogawa.write('*RST')

# Setup
yokogawa.write(":SOUR:FUNC CURR")
yokogawa.write(":SOUR:PROT:VOLT 1")
yokogawa.write(":SOUR:PROT:CURR MIN")
yokogawa.write(":SOUR:RANG 100E-3")

yokogawa.write(":SENS 1")
sleep(0.03)
yokogawa.write(":SOUR:LEV 1E-6")
sleep(0.03)
yokogawa.write(":OUTP 1")

yokogawa.write(":SENS:TRIG TIM")
yokogawa.write(":SENS:INT 3")
yokogawa.write(":TRAC:STAT ON")
yokogawa.write(":TRAC:POIN 10")
yokogawa.write(":TRAC:DATA:FORM ASC")
# yokogawa.write(":TRAC:FILE:CREA 1")

# yokogawa.write("*TRG")
sleep(0.1 + (0.02 * 1 + 0 * 0.001) * 2)
print(yokogawa.query(":TRAC:ACT?"))
print(yokogawa.query(":MEAS?"))
# yokogawa.write(":TRAC:DATA:READ?")
sleep(0.03)
# a = yokogawa.read()
# print(a)
yokogawa.write(":TRAC 0")
sleep(0.03)
yokogawa.write(":OUTP 0")

