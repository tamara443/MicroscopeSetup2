from Keysight_B2902A import Agilent
import time
import numpy as np

keysight = Agilent()
print("Connected.")


def input_parameters():
    v = float(input("Voltage in [V]:"))
    t = float(input("Measurement time in [s]:"))
    s = float(input("Time steps in s [s]:"))
    c = int(t/s)
    return v, s, c


def measurement(v, s, c):
    file_name = input("Save as: ")
    save_file = "C:/Users/EEFM/Documents/Lokale Messdaten/Czerny/BAPI_Spaltdetektoren_24-11-26/"+file_name

    keysight.write("*RST")
    keysight.write("FORM:ELEM:SENS VOLT, CURR, TIME")

    keysight.source_output_mode('voltage')
    keysight.write(":SOUR:VOLT:TRIG "+str(v))

    keysight.measurement_mode('current', 'on')
    keysight.compliance('Current', '0.00000001')
    keysight.write(":SENS:CURR:RANG 0.00000001")
    # keysight.write(":SENS:CURR:RANG:AUTO:MODE RES")
    # keysight.write(":SENS:CURR:RANG:AUTO THR 80")
    keysight.output_trigger('0', '0')
    keysight.write(":TRIG:TIM "+str(s))
    keysight.write(":TRIG:COUN "+str(c))

    file_header = "Time [s]\tCurrent [A]\tVoltage [V]"
    with open(save_file + ".dat", 'wb') as file:
        np.savetxt(file, [], header=file_header)
        keysight.output('on')
        #time.sleep(3)
        keysight.write(":INIT (@1)")
        keysight.write("FETC:ARR:CURR? (@1)")
        time.sleep(0.5)
        currents_list = keysight.read()
        keysight.write(":FETC:ARR:TIME? (@1)")
        time.sleep(0.5)
        time_list = keysight.read()
        keysight.write(":FETC:ARR:VOLT? (@1)")
        time.sleep(0.5)
        voltages_list = keysight.read()

        currents_floats = [float(x) for x in currents_list.split(',')]
        time_floats = [float(x) for x in time_list.split(',')]
        voltages_floats = [float(x) for x in voltages_list.split(',')]

        currents_arr = np.array(currents_floats)
        time_arr = np.array(time_floats)
        voltages_arr = np.array(voltages_floats)
        data = np.column_stack((time_arr, currents_arr, voltages_arr))
        np.savetxt(file, data)
        file.flush()

    keysight.output('off')
    print("Finished.")

voltage, step, count = input_parameters()
measurement(voltage, step, count)
exit()
