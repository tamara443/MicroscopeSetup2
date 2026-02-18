from pymeasure.instruments.signalrecovery import DSP7265
from time import sleep

# Connect to instrument
lockin = DSP7265("GPIB::12::INSTR")
lockin.imode = "current mode"
print(lockin.mag)
