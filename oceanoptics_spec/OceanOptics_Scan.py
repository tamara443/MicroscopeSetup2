    
import sys, os
import time
import datetime

import pandas as pd
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))



import pyqtgraph as pg
import numpy as np
import pickle
from pyqtgraph.Qt import QtCore
from PyQt5.QtWidgets import QApplication
from qtpy import QtWidgets
from mcl_stage.mcl_stagescan import MCL_stagescan



class OceanOptics_Scan(MCL_stagescan):

    name = "OceanOptics_Scan"

    def setup(self):
        MCL_stagescan.setup(self)

        self.settings.New("intg_time",dtype=int, unit='ms', initial=3, vmin=3)
        self.settings.New('correct_dark_counts', dtype=bool, initial=True)
        self.settings.New("scans_to_avg", dtype=int, initial=1, vmin=1)

        self.settings.New("measure_Photocurrent", dtype=bool, initial=False)
        self.settings.New("photocurrent_device", dtype=str, initial="LIA7265", choices=["LIA7265", "KeysightB2902A"])
        self.ui.keysight_photocurrent_groupBox.hide()
        self.ui.yokogawa_photocurrent_groupBox.show()

        # setup ui for ocean optics specific settings
        self.spec_hw = self.app.hardware['oceanoptics']
        #self.yokogawa = self.app.hardware['YokogawaGS200']
        self.yokogawa = self.app.hardware['YokogawaGS200_2']
        self.keysight = self.app.hardware['KeysightB2902A']
        self.stage = self.app.hardware.mcl_xyz_stage
        self.lia = self.app.hardware['LIA7265']

    def interrupt_scan(self):
        self.interrupt_measurement_called = True
        self.interrupt_measurement()

    
    def interrupt_measurement(self):
        self.interrupt_measurement_called = True


    def setup_figure(self):
        MCL_stagescan.setup_figure(self)

        details_groupBox = self.set_details_widget(widget = self.settings.New_UI(include=["intg_time", "correct_dark_counts", "scans_to_avg"]))
        widgets = details_groupBox.findChildren(QtWidgets.QWidget)
        intg_time_spinBox = widgets[1]
        correct_dark_counts_checkBox = widgets[4]
        #scans_to_avg_spinBox = widgets[6]
        #connect settings to ui
        self.spec_hw.settings.intg_time.connect_to_widget(intg_time_spinBox)
        self.spec_hw.settings.correct_dark_counts.connect_to_widget(correct_dark_counts_checkBox)
        intg_time_spinBox.valueChanged.connect(self.update_estimated_scan_time)
        # Yokogawa
        self.yokogawa.settings.Sourcelevel.connect_to_widget(self.ui.sourceLevel_doubleSpinBox)
        self.yokogawa.settings.Limitlevel.connect_to_widget(self.ui.sourceLimit_doubleSpinBox)
        self.yokogawa.settings.Range.connect_to_widget(self.ui.sourceRange_comboBox)
        self.yokogawa.settings.OnOff.connect_to_widget(self.ui.source_on_off_comboBox)
        self.ui.source_on_off_comboBox.currentIndexChanged.connect(self.yokogawaSourceSetup)
        # self.yokogawa.settings.Range.connect_to_widget(self.ui.measRange_comboBox) # originally yokogawa_2
        # self.yokogawa.settings.Limitlevel.connect_to_widget(self.ui.measCompliance_doubleSpinBox) # originally yokogawa_2
        # self.yokogawa.settings.IntgTime.connect_to_widget(self.ui.measIntg_doubleSpinBox) # originally yokogawa_2
        # # keysight
        self.keysight.settings.SourceLevel.connect_to_widget(self.ui.keysight_sourcelevel_dsb)
        self.keysight.settings.SourceRange.connect_to_widget(self.ui.keysight_sourcerange_combobox)
        self.keysight.settings.MeasurementRange.connect_to_widget(self.ui.measurement_range_comboBox)
        self.keysight.settings.Compliance.connect_to_widget(self.ui.compliance_combobox)
        self.keysight.settings.Intg.connect_to_widget(self.ui.measIntg_doubleSpinBox)

        #  LIA Settings/UI Buttons
        self.ui.set_auto_sensitivity.clicked.connect(self.lia.set_auto_sensitivity)
        self.ui.set_auto_phase.clicked.connect(self.lia.set_auto_phase)

        self.lia.settings.AutoGain.connect_to_widget(self.ui.set_auto_gain)
        self.lia.settings.Mode.connect_to_widget(self.ui.imode_comboBox)
        self.lia.settings.Reference.connect_to_widget(self.ui.reference_comboBox)
        self.lia.settings.Coupling.connect_to_widget(self.ui.coupling_comboBox)
        self.lia.settings.Gain.connect_to_widget(self.ui.gain_doubleSpinBox)
        self.lia.settings.Sensitivity.connect_to_widget(self.ui.sensitivity_doubleSpinBox)
        self.lia.settings.Phase.connect_to_widget(self.ui.phase_doubleSpinBox)

        # Photocurrent Measurement
        self.settings.measure_Photocurrent.connect_to_widget(self.ui.photocurrent_checkBox)
        self.settings.photocurrent_device.connect_to_widget(self.ui.photocurrent_comboBox)
        self.ui.photocurrent_comboBox.currentIndexChanged.connect(self.photocurrent_device_changed)
        
        #save data buttons
        self.ui.save_image_pushButton.clicked.connect(self.save_intensities_image)
        self.ui.save_array_pushButton.clicked.connect(self.save_intensities_data)

        #spectrometer plot
        self.graph_layout=pg.GraphicsLayoutWidget()
        self.plot = self.graph_layout.addPlot(title="Spectrometer Live Reading")
        self.plot.setLabel('left', 'Intensity', unit='a.u.')
        self.plot.setLabel('bottom', 'Wavelength', unit='nm') 

        # # Create PlotDataItem object ( a scatter plot on the axes )
        self.optimize_plot_line = self.plot.plot([0])
        
        #setup imageview
        self.imv = pg.ImageView()
        self.imv.getView().setAspectLocked(lock=False, ratio=1)
        self.imv.getView().setMouseEnabled(x=True, y=True)
        self.imv.getView().invertY(False)
        roi_plot = self.imv.getRoiPlot().getPlotItem()
        roi_plot.getAxis("bottom").setLabel(text="Wavelength (nm)")

    def photocurrent_device_changed(self):
        if self.ui.photocurrent_comboBox.currentText() == "KeysightB2902A":
            self.ui.yokogawa_photocurrent_groupBox.hide()
            self.ui.keysight_photocurrent_groupBox.show()
        elif self.ui.photocurrent_comboBox.currentText() == "LIA7265":
            self.ui.keysight_photocurrent_groupBox.hide()
            self.ui.yokogawa_photocurrent_groupBox.show()
    def update_estimated_scan_time(self):
        try:
            self.overhead = self.x_range * self.y_range * .058 #determined by running scans and timing
            self.scan_time = self.x_range * self.y_range * self.settings["intg_time"] * 1e-3 + self.overhead #s
            self.ui.estimated_scan_time_label.setText("Estimated scan time: " + "%.2f" % self.scan_time + "s")
        except:
            pass

    def identify(self):
        print(self.keysight.query("*IDN?"))
    def update_display(self):
        MCL_stagescan.update_display(self)
        if hasattr(self, 'spec') and hasattr(self, 'nanodrive') and hasattr(self, 'y'): #first, check if setup has happened
            if not self.interrupt_measurement_called:
                per_pixel = self.scan_time/(self.x_range * self.y_range)
                seconds_left = per_pixel * (self.x_range * self.y_range - self.pixels_scanned)
                self.ui.estimated_time_label.setText("Estimated time remaining: " + "%.2f" % seconds_left + "s")
            #plot wavelengths vs intensity
            self.plot.plot(self.spec.wavelengths(), self.y, pen='r', clear=True) #plot wavelength vs intensity
            self.graph_layout.show()
            self.graph_layout.window().setWindowFlag(QtCore.Qt.WindowCloseButtonHint, True) #disable closing image view window

            self.img_item.setImage(self.sum_intensities_image_map) #update stage image
            
            #update imageview
            self.imv.setImage(img=self.spectrum_image_map, autoRange=False, autoLevels=True, xvals=self.spec.wavelengths()) #adjust roi plot x axis
            self.imv.show()
            self.imv.window().setWindowFlag(QtCore.Qt.WindowCloseButtonHint, True) #disable closing image view window
            
            #update progress bar
            progress = 100 * ((self.pixels_scanned+1)/np.abs(self.x_range*self.y_range))
            print(f"Progress: {progress}")
            # Changed this to cast to int, problem in the log with "setValue unknown Value float64" seems gone
            self.ui.progressBar.setValue(int(progress))
            self.set_progress(progress)

            #faulty way over pyqtgraph - archived
            #pg.QtGui.QApplication.processEvents()
            QApplication.processEvents()

  

    def pre_run(self):
        print("pre_run method called")
        MCL_stagescan.pre_run(self) #setup scan parameters
        self.check_filename("_raw_PL_spectra_data.pkl")
        self.spec = self.spec_hw.spec
        # Define empty array for saving intensities
        self.data_array = np.empty(shape=(self.x_range*self.y_range, 2068))
        print(f"data_array shape: {self.data_array.shape}")
        # Define empty array for image map
        self.sum_intensities_image_map = np.zeros((self.x_range, self.y_range), dtype=float) #store sum of intensities for each pixel
        print("sum_intensities_image_map initialized successfully")
        self.spectrum_image_map = np.zeros((2068, self.x_range, self.y_range), dtype=float) #Store spectrum for each pixel
        print(f"Spectrum shape: {self.spectrum_image_map.shape}")
        # Print shape of sum_intensities_image_map
        print(f"sum_intensities_image_map shape: {self.sum_intensities_image_map.shape}")
        
        ###
        # test per df
        ###
        self.df_data = pd.DataFrame()
        self.df_data["Wavelengths"] = self.spec.wavelengths()

        # Setup the SMU for optional Photocurrent Measurement
        if self.settings["measure_Photocurrent"]:
            # Photocurrent array
            self.current_data = pd.DataFrame()
            self.phase_data = pd.DataFrame()
            self.xy_data = pd.DataFrame()
            self.sum_current_image_map = np.zeros(shape=(self.x_range, self.y_range), dtype=float)
            self.sum_phase_image_map = np.zeros(shape=(self.x_range, self.y_range), dtype=float)
            print(f"current_data shape: {self.current_data.shape}")

            if self.settings["photocurrent_device"] == "LIA7265":
                self.prepareLIA()
            elif self.settings["photocurrent_device"] == "KeysightB2902A":
                self.keysightSourceSetup(1)
                self.keysightMeasureSetup(1)
                # measure 10 s dark current
                self.keysightDarkMeasurement(self.keysight.settings["SourceLevel"])
                # reconfigure in case anything changed for the dark current measurement
                self.keysightMeasureSetup(1)
        
        print("Initialization complete.")
        self.pixelmator = 0
    def scan_measure(self):
        """
        Data collection for each pixel.
        """
        print(f"Scanning pixel: {self.pixelmator} out of {self.x_range*self.y_range}")
        self._read_spectrometer()

        # Because the first few values of the SMU (Keysight B2902A) are not accurate, we will discard them by
        # checking for the first pixel and executing a measurement, thus just dumping the data
        # before the first real measurements happens
        if self.pixelmator == 0 and self.settings["measure_Photocurrent"] and self.settings["photocurrent_device"] == "KeysightB2902A":
            discard_values = self.keysightMeasurement(self.keysight.settings["SourceLevel"])

        print(f"Pixels Scanned: {self.pixelmator}")
        self.data_array[self.pixelmator, :] = self.y
        self.sum_intensities_image_map[self.index_x, self.index_y] = self.y.sum()
        self.spectrum_image_map[:, self.index_x, self.index_y] = self.y

        # Print current sum_intensities_image_map values
        print(f"sum_intensities_image_map at ({self.index_x}, {self.index_y}): {self.sum_intensities_image_map[self.index_x, self.index_y]}")

        self.df_data[f"Intensity set {self.pixelmator} at X {self.index_x} - Y {self.index_y}"] = self.y
        
        # keysight measurement and store on databuffer
        if self.settings["measure_Photocurrent"]:
            if self.settings["photocurrent_device"] == "LIA7265":
                wait_time = float(self.ui.wait_time_doubleSpinBox.value())
                time.sleep(wait_time)
                print("wait time", wait_time)
                pcd = []
                pcd_phase = []
                xy = []
                for i in range(5):
                    pcd.append(self.lia.measure_mag())
                    pcd_phase.append(self.lia.measure_phase())
                    xy.append(self.lia.measure_xy())
                    time.sleep(0.1)
                print("Phase: " + str(pcd_phase))
                print("XY: " + str(xy))
                a = np.array([float(x) for x in pcd])
                b = np.array([float(x) for x in pcd_phase])
                c = np.array([float(x) for sublist in xy for x in sublist])
                self.sum_current_image_map[self.index_x, self.index_y] = a.mean()
                self.current_data[f"X {self.index_x} - Y {self.index_y}"] = a
                self.sum_phase_image_map[self.index_x, self.index_y] = b.mean()
                self.phase_data[f"X {self.index_x} - Y {self.index_y}"] = b
                self.xy_data[f"X {self.index_x} - Y {self.index_y}"] = c
            elif self.settings["photocurrent_device"] == "KeysightB2902A":
                pcd = self.keysightMeasurement(self.keysight.settings["SourceLevel"])
                print(pcd)
                kek = [float(x) for x in pcd.split(",")]
                a = np.array(kek)
                # a = np.array([float(x) for x in pcd])
                #Use only the last half of the data points, because there is a strong decline in the beginning
                half_index = len(a) // 2
                last_half_a = a[half_index:]
                self.sum_current_image_map[self.index_x, self.index_y] = last_half_a.mean()
                self.current_data[f"X {self.index_x} - Y {self.index_y}"] = a


        self.pixelmator += 1


    def post_run(self):
        """
        Export data.
        """
        MCL_stagescan.post_run(self)
        self.spec = self.spec_hw.spec
        save_dict = {"Wavelengths": self.spec.wavelengths(), "Intensities": self.data_array,
                "Scan Parameters":{"Scan direction": self.settings["scan_direction"],
                        "X scan start (um)": self.x_start, "Y scan start (um)": self.y_start,
                                    "X scan size (um)": self.x_scan_size, "Y scan size (um)": self.y_scan_size,
                                    "X step size (um)": self.x_step, "Y step size (um)": self.y_step},
                                    "OceanOptics Parameters":{"Integration Time (ms)": self.spec_hw.settings['intg_time'],
                                                            "Scans Averages": self.settings['scans_to_avg'],
                                                            "Correct Dark Counts": self.spec_hw.settings['correct_dark_counts']}
                }

        # Save to a pickle file
        filename = self.app.settings['save_dir']+"/"+self.app.settings['sample']+"_raw_PL_spectra_data.pkl"
        with open(filename, 'wb') as f:
            pickle.dump(save_dict, f)

        if self.stage.settings["debug_mode"]:
            print("OceanOptics scan data saved.")

        # Load the saved data into memory
        with open(filename, 'rb') as f:
            loaded_data = pickle.load(f)

        # Print the loaded data for verification
        print(loaded_data)

        datapath = self.app.settings['save_dir']+"/"+self.app.settings['sample']+"_raw_PL_spectra_data_CSV.csv"
        self.df_data.to_csv(datapath)

        # Optional: Save photocurrent data and create image of the means
        if self.settings["measure_Photocurrent"]:
            smuFile = self.app.settings['save_dir']+"/"+self.app.settings['sample']+"_SMU_Data.csv"
            self.current_data.to_csv(smuFile)
            if self.settings["photocurrent_device"] == "KeysightB2902A":
                self.keysightSourceSetup(0)
                self.keysightMeasureSetup(0)
            elif self.settings["photocurrent_device"] == "LIA7265":
                # Save phase
                PhaseFile = self.app.settings['save_dir'] + "/" + self.app.settings['sample'] + "_Phase_Data.csv"
                self.phase_data.to_csv(PhaseFile)
                self.save_phase_data()
                # Save XY
                xyFile = self.app.settings['save_dir'] + "/" + self.app.settings['sample'] + "_XY_Data.csv"
                self.xy_data.to_csv(xyFile)
                self.yokogawa.setOutput("OFF")

            self.save_photocurrent_data()
            self.save_photocurrent_image()

        self.save_intensities_data()
        self.save_intensities_image()
        self.exportMeasurementSettings()

    def prepareLIA(self):
        self.lia.set_mode(self.lia.settings["Mode"])
        self.lia.set_reference(self.lia.settings["Reference"])
        self.lia.set_auto_gain(self.lia.settings["AutoGain"])
        self.lia.set_gain(self.lia.settings["Gain"])
        self.lia.set_coupling(self.lia.settings["Coupling"])
        self.lia.set_sensitivity(float(self.lia.settings["Sensitivity"]))
        self.lia.set_phase(self.lia.settings["Phase"])

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

    def keysightSourceSetup(self, output):
        mode = "voltage"
        range = self.keysight.settings["SourceRange"]
        level = self.keysight.settings["SourceLevel"]
        print(f"Source Level: {level}")
        if output:
            self.keysight.source_output_mode(mode)
            self.keysight.output_range(mode, "off", range)
            self.keysight.apply_output(mode, level)
            # self.keysight.output("on")
        elif not output:
            self.keysight.output("off")

    def yokogawaMeasureSetup(self, measurement):
        limit = self.yokogawa_2.settings["Limitlevel"]
        range = self.yokogawa_2.settings["Range"]
        if measurement:
            self.yokogawa_2.setMode("Current")
            self.yokogawa_2.setLimit(limit, "Current")
            self.yokogawa_2.setSourceRange(range)

        if not measurement:
            self.yokogawa_2.setMode("Current")

    def yokogawaMeasurement(self):
        intg = self.yokogawa_2.settings["IntgTime"]
        self.yokogawa_2.setMeasurement(1)
        time.sleep(0.03)
        self.yokogawa_2.setSourceLevel(0.0)
        time.sleep(0.03)
        self.yokogawa_2.setOutput(1)
        #  Therefore, the time for one measurement operation is: ((measurement delay
        #  + integration time) × 2) + software processing
        time.sleep(0.1 + (0.02 * intg + 0 * 0.001) * 2)
        measurement = self.yokogawa_2.readLineData("fetch")
        time.sleep(0.03)
        self.yokogawa_2.setOutput(0)
        time.sleep(0.03)
        self.yokogawa_2.setMeasurement(0)

        return measurement

    def keysightMeasureSetup(self, measurement):
        intg = self.keysight.settings["Intg"]
        compliance = self.keysight.settings["Compliance"]
        range = self.keysight.settings["MeasurementRange"]

        if measurement:
            # self.keysight.source_output_mode("voltage")
            # self.keysight.apply_output("Voltage", 0.0)
            self.keysight.compliance("Current", compliance)
            # self.keysight.source_output_mode("current")
            # self.keysight.apply_output("Current", 0.0)
            # self.keysight.compliance("Voltage", compliance)

            #measurement part
            # self.keysight.measurement_mode("voltage", "on")
            # self.keysight.measurement_speed("voltage", "off", intg)
            # self.keysight.measurement_auto_range_off("Voltage", "off")
            # self.keysight.measurement_range("off", "Voltage", range)

            self.keysight.measurement_range("Current", "off", range)
            self.keysight.measurement_speed("current", "off", intg)
            self.keysight.measurement_trigger_count_auto(20)

        if not measurement:
            self.keysight.measurement_mode("voltage", "on")

    def keysightMeasurement(self, level):
        self.keysight.apply_output("Voltage", level)
        self.keysight.output("on")
        self.keysight.measure()
        a = self.keysight.retrieve_data("current")
        self.keysight.output("off")
        return a

    def keysightDarkMeasurement(self, level):
        while True:
            response = input("Please switch off the laser and press Enter to confirm: ").strip()
            if response == '':
                print("Thank you! Proceeding with the code...")
                break
            else:
                print("Waiting for confirmation...")

        # Start measurement
        self.keysight.measurement_trigger_count_auto(500)
        self.keysight.apply_output("Voltage", level)
        self.keysight.output("on")
        self.keysight.measure()

        # Retrieve data
        raw_current_data = self.keysight.retrieve_data("current")
        raw_time_data = self.keysight.retrieve_data("time")
        raw_voltage_data = self.keysight.retrieve_data("voltage")
        self.keysight.output("off")

        # Split the retrieved data at commas
        current_data = raw_current_data.split(",")
        time_data = raw_time_data.split(",")
        voltage_data = raw_voltage_data.split(",")

        # Convert current data to floats for calculations
        current_data = list(map(float, current_data))

        # Calcuate the average of last halft of the current measurement
        half_index = len(current_data) // 2
        last_half_average = sum(current_data[half_index:]) / len(current_data[half_index:])

        # Define the file path for saving data
        darkcurrentFile = self.app.settings['save_dir'] + "/" + self.app.settings['sample'] + "_DarkCurrent.txt"

        # Save time and current data to the file in two columns
        with open(darkcurrentFile, 'w') as file:
            file.write(f"Average dark current: {last_half_average:.13f}\n\n")
            file.write("Time (s)\tCurrent (A)\tVoltage (v)\n")  # Write headers
            for t, c, v in zip(time_data, current_data, voltage_data):
                file.write(f"{t}\t{c}\t{v}\n")

        print("Dark current measurement complete.")
        while True:
            response = input("Please switch on the laser and press Enter to confirm: ").strip()
            if response == '':
                print("Thank you! Proceeding with the code...")
                break
            else:
                print("Waiting for confirmation...")

    
    def _read_spectrometer(self):
        '''
        Read spectrometer according to settings and update self.y (intensities array)
        '''
        if hasattr(self, 'spec'):
            intg_time_ms = self.spec_hw.settings['intg_time']
            self.spec.integration_time_micros(intg_time_ms*1e3) #seabreeze error checking

            scans_to_avg = self.settings['scans_to_avg']
            Int_array = np.zeros(shape=(2068, scans_to_avg))

        for i in range(scans_to_avg): #software average
            data = self.spec.spectrum(correct_dark_counts=self.spec_hw.settings['correct_dark_counts'])#acquire wavelengths and intensities from spec
            Int_array[:, i] = data[1]
        self.y = np.mean(Int_array, axis=-1)
        print(f"self.y={self.y}") # add this line to check that self.y is being set correctly



    def save_intensities_data(self):
        try:
            if hasattr(self, 'sum_intensities_image_map'):
                transposed = np.transpose(self.sum_intensities_image_map)
                MCL_stagescan.save_intensities_data(self, self.sum_intensities_image_map, 'oo')
            else:
                print("sum_intensities_image_map not found")
        except:
            print("Error in saving intensities data.")


    def save_intensities_image(self):
        print("save_intensities_image method called")
        try:
            if self.sum_intensities_image_map is not None:
                MCL_stagescan.save_intensities_image(self, self.sum_intensities_image_map, 'oo')
            else:
                print("sum_intensities_image_map not found")
        except:
            pass

    def save_photocurrent_data(self):
        try:
            if self.sum_current_image_map is not None:
                MCL_stagescan.save_photocurrent_data(self, self.sum_current_image_map, 'smu_pc')
            else:
                print("current_intensities_image_map not found")
        except:
            pass

    def save_photocurrent_image(self):
        try:
            if self.sum_current_image_map is not None:
                MCL_stagescan.save_photocurrent_image(self, self.sum_current_image_map, 'smu_pc')
            else:
                print("current_intensities_image_map not found")
        except:
            pass

    def save_phase_data(self):
        try:
            if self.sum_phase_image_map is not None:
                MCL_stagescan.save_phase_data(self, self.sum_phase_image_map, 'lia_phase')
            else:
                print("phase_intensities_image_map not found")
        except:
            pass

    def exportMeasurementSettings(self):
        with open (self.app.settings['save_dir']+"/"+self.app.settings['sample']+"_MeasurementSettings.txt", 'w') as f:
            f.write("Scan Parameters\n")
            f.write("Scan direction: " + str(self.settings["scan_direction"]) + "\n")
            f.write("X scan start (um): " + str(self.x_start) + "\n")
            f.write("Y scan start (um): " + str(self.y_start) + "\n")
            f.write("X scan size (um): " + str(self.x_scan_size) + "\n")
            f.write("Y scan size (um): " + str(self.y_scan_size) + "\n")
            f.write("X step size (um): " + str(self.x_step) + "\n")
            f.write("Y step size (um): " + str(self.y_step) + "\n\n")

            f.write("OceanOptics Settings\n")
            f.write("Integration Time (ms): " + str(self.spec_hw.settings['intg_time']) + "\n")
            f.write("Scans Averages: " + str(self.settings['scans_to_avg']) + "\n")
            f.write("Correct Dark Counts: " + str(self.spec_hw.settings['correct_dark_counts']) + "\n\n")

            if self.settings["measure_Photocurrent"]:
                f.write("Photocurrent Measurement: " + str(self.settings['measure_Photocurrent']) + "\n")
                f.write("Photocurrent Device: " + str(self.settings['photocurrent_device']) + "\n\n")
                if self.settings["photocurrent_device"] == "LIA7265":
                    f.write("LIA Settings\n")
                    f.write("Mode: " + str(self.lia.settings['Mode']) + "\n")
                    f.write("Reference: " + str(self.lia.settings['Reference']) + "\n")
                    f.write("Coupling: " + str(self.lia.settings['Coupling']) + "\n")
                    f.write("Gain: " + str(self.lia.settings['Gain']) + "\n")
                    f.write("Auto Gain: " + str(self.lia.settings['AutoGain']) + "\n")
                    f.write("Phase: " + str(self.lia.settings['Phase']) + "\n")
                    f.write("Sensitivity: " + str(self.lia.settings['Sensitivity']) + "\n\n")

                    f.write("Yokogawa Settings\n")
                    f.write("Source Level (V): " + str(self.yokogawa.settings['Sourcelevel']) + "\n")
                    f.write("Limit Level (V): " + str(self.yokogawa.settings['Limitlevel']) + "\n")
                    f.write("Range: " + str(self.yokogawa.settings['Range']) + "\n\n")
                elif self.settings["photocurrent_device"] == "KeysightB2902A":
                    f.write("Keysight Settings\n")
                    f.write("Source Level: " + str(self.keysight.settings['SourceLevel']) + "\n")
                    f.write("Source Range: " + str(self.keysight.settings['SourceRange']) + "\n")
                    f.write("Measurement Range: " + str(self.keysight.settings['MeasurementRange']) + "\n")
                    f.write("Compliance (V): " + str(self.keysight.settings['Compliance']) + "\n")
                    f.write("Integration Time (s): " + str(self.keysight.settings['Intg']) + "\n")


            f.write("Sample: " + str(self.app.settings['sample']) + "\n")
            f.write("Creation Date: " + str(datetime.datetime.now()) + "\n")






                




