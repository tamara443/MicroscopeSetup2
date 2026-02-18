from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
import pandas as pd
import numpy as np
import time
import pyqtgraph as pg
import matplotlib.pyplot as plt
from datetime import datetime
from PyQt5.QtCore import QCoreApplication



class Yokogawa_Measurement(Measurement):

    def setup(self):
        self.name = "SMU_Measurement"
        self.ui_filename = sibling_path(__file__, "smu_measurement.ui")
        self.ui = load_qt_ui_file(self.ui_filename)

        self.settings.New(name="Duration", initial=10, dtype=int)
        self.settings.New(name="Interval", initial=0.5, dtype=float)

        self.measurement_df = pd.DataFrame()
        self.interrupt_flag = False

        self.yokogawa = self.app.hardware['YokogawaGS200_2']
        self.chopper = self.app.hardware['MC2000B']
        self.lia = self.app.hardware['LIA7265']

    def setup_figure(self):
        # Connect settings to UI
        # from Yokogawa Hardware
        self.yokogawa.settings.SourceMode.connect_to_widget(self.ui.sourceMode_comboBox)
        self.yokogawa.settings.Range.connect_to_widget(self.ui.sourceRange_comboBox)
        self.yokogawa.settings.Limitlevel.connect_to_widget(self.ui.limitLevel_doubleSpinBox)
        self.yokogawa.settings.Sourcelevel.connect_to_widget(self.ui.setSource_doubleSpinBox)
        self.yokogawa.settings.OnOff.connect_to_widget(self.ui.source_on_off_comboBox1)

        #  from Chopper Hardware
        self.chopper.settings.Frequency.connect_to_widget(self.ui.frequency_doubleSpinBox)
        self.chopper.settings.BladeType.connect_to_widget(self.ui.bladeType_comboBox)
        self.chopper.settings.OnOff.connect_to_widget(self.ui.chopper_on_off_comboBox)

        # from LIA Hardware
        self.lia.settings.AutoGain.connect_to_widget(self.ui.set_auto_gain)
        self.lia.settings.Mode.connect_to_widget(self.ui.imode_comboBox)
        self.lia.settings.Reference.connect_to_widget(self.ui.reference_comboBox)
        self.lia.settings.Coupling.connect_to_widget(self.ui.coupling_comboBox)
        self.lia.settings.Gain.connect_to_widget(self.ui.gain_doubleSpinBox)
        self.lia.settings.Sensitivity.connect_to_widget(self.ui.sensitivity_doubleSpinBox)
        self.lia.settings.Phase.connect_to_widget(self.ui.phase_doubleSpinBox)

        # from Measurement
        self.settings.Duration.connect_to_widget(self.ui.measurementTime_doubleSpinBox)
        self.settings.Interval.connect_to_widget(self.ui.measurementInterval_doubleSpinBox)

        # Connect functions to UI
        self.ui.setSource_doubleSpinBox.setDecimals(5)
        #  Yokogawa
        self.ui.source_on_off_comboBox1.currentIndexChanged.connect(self.yokogawaSourceSetup)
        #  Chopper
        self.ui.frequency_doubleSpinBox.valueChanged.connect(self.setFrequency)
        self.ui.bladeType_comboBox.currentIndexChanged.connect(self.setBladeType)
        self.ui.chopper_on_off_comboBox.currentIndexChanged.connect(self.enable)
        #  LIA
        self.ui.set_auto_sensitivity.clicked.connect(self.lia.set_auto_sensitivity)
        self.ui.set_auto_phase.clicked.connect(self.lia.set_auto_phase)
        self.ui.start_Button.clicked.connect(self.mag_measurement)
        self.ui.interrupt_Button.clicked.connect(self.interrupt_loop)
        #  Graph
        self.ui.clear_graph_button.clicked.connect(self.clear_graph)

        #Graph Settings
        self.plot_graph = pg.PlotWidget()
        self.ui.plot_groupBox.layout().addWidget(self.plot_graph)
        self.plot_graph.setTitle("Magnitude Measurement 1")
        self.plot_graph.setLabel("left", "Magnitude (V)")
        self.plot_graph.setLabel("bottom", "Time (s)")
        self.plot_graph.showGrid(x=True, y=True)
        self.graph_iteration = 0
        self.colors = [
            (255, 0, 0),  # Red
            (0, 255, 0),  # Green
            (255, 255, 255), # White
            (0, 0, 255),  # Blue
            (255, 255, 0),  # Yellow
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Cyan
        ]
        self.symbols = ["o", "t", "s", "d", "+", "x", "star"]

    def interrupt_loop(self):
        self.interrupt_flag = True

    def clear_graph(self):
        self.plot_graph.clear()
        self.graph_iteration = 0
    def SaveMeasurement(self, save_dict):
        path = self.app.settings["save_dir"]
        sample = self.app.settings["sample"]
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        keys = list(save_dict.keys())
        values1 = save_dict[keys[0]]
        values2 = save_dict[keys[1]]

        merged_dict = {**self.settings, **self.yokogawa.settings, **self.chopper.settings, **self.lia.settings}
        for key in ["activation", "run_state", "progress", "profile", "connected", "debug_mode", "IntgTime", "Delay"]:
            merged_dict.pop(key, None)
        max_key_length = max(len(key) for key in merged_dict.keys())
        merged_dict["Frequency"] = self.chopper.get_frequency()

        with open(path + "\\" + sample + str(ts) + "_MeasurementSettings.txt", "w") as file:
            for key, value in merged_dict.items():
                # Format key-value with spacing
                line = f"{key}{' ' * (max_key_length - len(key) + 10)}{value}\n"
                file.write(line)

        # Open the file and write the keys as headers, followed by each value pair
        with open(path + "\\" + sample + str(ts) + ".txt", "w") as file:
            # Write the headers
            file.write(f"{keys[0]}\t{keys[1]}\n")

            # Write each row of values under the corresponding column
            for v1, v2 in zip(values1, values2):
                file.write(f"{v1}\t\t{v2}\n")

        print("Measurement Saved")

    # Yokogawa Functions
    def yokogawaSourceSetup(self):
        mode = "Voltage"
        range = self.yokogawa.settings["Range"]
        level = self.yokogawa.settings["Sourcelevel"]
        limit = self.yokogawa.settings["Limitlevel"]
        if self.yokogawa.settings["OnOff"] == "ON":
            self.yokogawa.setMode(mode)
            self.yokogawa.setSourceRange(range)
            self.yokogawa.setLimit(limit, mode)
            self.yokogawa.setSourceLevel(level)
            self.yokogawa.setOutput("ON")
        else:
            self.yokogawa.setOutput("OFF")

    # Chopper Functions
    def setFrequency(self):
        self.chopper.set_frequency(int(self.chopper.settings["Frequency"]))

    def setBladeType(self):
        blade = self.ui.bladeType_comboBox.currentText()
        if blade == "MC1F10HP":
            self.chopper.set_bladetype(6)
        elif blade == "MC1F2":
            self.chopper.set_bladetype(0)
    # Blade type 0:MC1F2, 1:MC1F10, 2:MC1F15, 3:MC1F30, 4:MC1F60, 5:MC1F100, 6:MC1F10HP, 7:MC1F2P10, 8:MC1F6P10, 9:MC1F10A, 10:MC2F330, 11:MC2F47, 12:MC2F57B, 13:MC2F860, 14:MC2F5360

    def enable(self):
        state = self.ui.chopper_on_off_comboBox.currentText()
        if state == "ON":
            enable = 1
        else:
            enable = 0
        self.chopper.enable(enable)

    # LIA Functions
    def prepareLIA(self):
        self.lia.set_mode(self.lia.settings["Mode"])
        self.lia.set_reference(self.lia.settings["Reference"])
        self.lia.set_auto_gain(self.lia.settings["AutoGain"])
        self.lia.set_gain(self.lia.settings["Gain"])
        self.lia.set_coupling(self.lia.settings["Coupling"])
        self.lia.set_sensitivity(float(self.lia.settings["Sensitivity"]))
        self.lia.set_phase(self.lia.settings["Phase"])

    def mag_measurement(self):
        interval = float(self.settings["Interval"])
        duration = int(self.settings["Duration"])

        mag = {"interval": [], "magnitude": []}
        get_frequency = []

        line = self.plot_graph.plot(
            pen=self.colors[self.graph_iteration],
            symbol=self.symbols[self.graph_iteration],
            symbolSize=15,
            symbolBrush="b",
        )

        self.prepareLIA()
        self.yokogawaSourceSetup()
        get_frequency.append(self.chopper.get_frequency())
        time.sleep(1)

        iteration_times = [] # for time accuracy plot
        start_time = time.time()
        for i in np.arange(0, duration, interval):
            loop_start_time = time.time()

            if self.interrupt_flag:  # Check if the interrupt flag is set
                print("Measurement interrupted!")
                self.interrupt_flag = False
                break

            mag["interval"].append(i)
            mag["magnitude"].append(self.lia.measure_mag())
            line.setData(mag["interval"], mag["magnitude"])

            QCoreApplication.processEvents() # Process events to update the UI

            sleep_time = interval - (time.time() - loop_start_time)
            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                print("Loop execution exceeded interval!")
            iteration_times.append(time.time() - loop_start_time) # for time accuracy plot

        print("Total Duration: ", time.time() - start_time)

        # COMMENT OUT IF DONT WANT TIME ACCURACY PLOT
        plt.plot(iteration_times, marker='o', linestyle='-', color='b',
                 label='Iteration Time')
        plt.ylabel("Time per iteration (seconds)")
        plt.title("Iteration Time")
        plt.grid(True)
        avg_time = np.mean(iteration_times)
        plt.axhline(y=avg_time, color='r', linestyle='--', label=f'Average Time: {avg_time:.3f}s')
        plt.legend()
        plt.show()
        #####

        self.graph_iteration += 1
        if self.graph_iteration == 7:
            self.graph_iteration = 0

        get_frequency.append(self.chopper.get_frequency())
        self.ui.get_Frequency_Text.setText(str(get_frequency))
        self.SaveMeasurement(mag)



