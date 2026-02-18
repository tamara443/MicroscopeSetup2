import numpy as np
import pyvisa
from keithley2600 import Keithley2600
#import NKTP_DLL
import time
import timeit

echo_commands = 0


def instrument_connect(resource_mgr, instrument_resource_string, timeout, do_id_query, do_reset,
                       do_clear):
    instrument_object = resource_mgr.open_resource(instrument_resource_string)
    if do_id_query == 1:
        print(instrument_query(instrument_object, "*IDN?"))
    if do_reset == 1:
        instrument_write(instrument_object, "*RST")
    if do_clear == 1:
        instrument_object.clear()
    instrument_object.timeout = timeout
    return resource_mgr, instrument_object


def instrument_write(instrument_object, my_command):
    if echo_commands == 1:
        print(my_command)
    instrument_object.write(my_command)
    return


def instrument_query(instrument_object, my_command):
    if echo_commands == 1:
        print(my_command)
    return instrument_object.query(my_command)


def instrument_disconnect(instrument_object):
    instrument_object.close()
    return


instrument_string = "GPIB0::26::INSTR"
resource_manager = pyvisa.ResourceManager()  # Opens the resource manager
resource_manager, my_instr = instrument_connect(resource_manager, instrument_string, 20000, 1, 1, 1)
keithley = Keithley2600('GPIB0::26::INSTR', visa_library='')
voltage = 10
wavelength = 510
power = 63.2
save_file = ""
data_points = 50
repetitions = 5
integration_time = 0.1
time_v = np.linspace(0, 30, data_points)
currents = np.zeros_like(time_v)

instrument_write(my_instr, "*RST")
keithley.set_integration_time(keithley.smua, integration_time)

#NKTP_DLL.registerWriteU16('COM3', 16, 0x34, int((wavelength-5) * 10), -1)
#NKTP_DLL.registerWriteU16('COM3', 16, 0x33, int((wavelength+5) * 10), -1)
#NKTP_DLL.registerWriteU16('COM3', 15, 0x37, int(power*10), -1)
time.sleep(1)

keithley.apply_voltage(keithley.smua, voltage)
file_header = "Time[s]\tCurrent [A]\nat Voltage =" + str(voltage) + "V\t" + str(repetitions) + "repetitions per point"
with open(save_file + ".dat", 'wb') as file:
    np.savetxt(file, [], header=file_header)

    start = timeit.default_timer()

    for i in range(data_points):
        time.sleep(0.1)  # wait for 0.1 sec

        current_sum = 0  # set current sum for repetitions to 0 A
        for j in range(1, repetitions + 1, 1):  # repetitions loop
            current = keithley.measure_current(keithley.smua)
            current_sum = current_sum + current
        currents[i] = current_sum / repetitions
        time_counter = timeit.default_timer()
        time_v[i] = time_counter - start

        data = np.column_stack((time_v[i], currents[i]))
        np.savetxt(file, data)
        file.flush()
        time.sleep(0.1)
instrument_write(my_instr, "*RST")