from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
import pyqtgraph as pg
import numpy as np
import time
import pickle
import os.path
from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph.Point import Point
import customplotting.mscope as cpm
import sys, os

oceanopticsPath = os.path.dirname(os.path.abspath(__file__))
sys.path.append(oceanopticsPath)

class MCL_stagescan(Measurement):
    name = "MCL_stagescan"

    
    def setup(self):
        """
        Runs once during App initialization.
        This is the place to load a user interface file,
        define settings, and set up data structures. 
        """
        # Define ui file to be used as a graphical interface
        # This file can be edited graphically with Qt Creator
        # sibling_path function allows python to find a file in the same folder
        # as this python module
        self.ui_filename = sibling_path(__file__, "stage_scan.ui")
        
        #Load ui file and convert it to a live QWidget of the user interface
        self.ui = load_qt_ui_file(self.ui_filename)

        # Measurement Specific Settings
        # This setting allows the option to save data to an h5 data file during a run
        # All settings are automatically added to the Microscope user interface
        self.settings.New("scan_direction", dtype=str, choices=[('XY', 'XY'), ('YX', 'YX')], initial='XY')

        self.settings.New('x_start', dtype=float,  unit='um', vmin=0)
        self.settings.New('y_start', dtype=float,  unit='um', vmin=0)
    
        self.settings.New('x_size', dtype=float, initial=1, unit='um', vmin=0)
        self.settings.New('y_size', dtype=float, initial=1, unit='um', vmin=0)

        self.settings.New('x_step', dtype=float, initial=1, unit='um', vmin=-99, vmax=99)#vmin=.001#-99)
        self.settings.New('y_step', dtype=float, initial=1, unit='um', vmin=-99, vmax=99)#vmin=.001#-99)

        self.settings.New('x_clicked', dtype=float, initial=0, unit='um', vmin=0, vmax=100, ro=True)
        self.settings.New('y_clicked', dtype=float, initial=0, unit='um', vmin=0, vmax=100, ro=True)

        self.settings.New('lock_position', dtype=bool, initial=False)
        self.settings.New('save_positions', dtype=bool, initial=False)
        self.settings.New("step_size", dtype=float, initial=1.0, vmin=0.001, vmax=100.0, ro=True)#0.001

        self.update_ranges()
        
        # Define how often to update display during a run
        self.display_update_period = .3
        
        # Convenient reference to the hardware used in the measurement
        self.stage = self.app.hardware.mcl_xyz_stage

        self.scan_complete = False

        self.selected_positions = np.zeros((1000, 2))
        self.selected_count = 0 #number of points selected
    
        self.chopper = self.app.hardware['MC2000B']

    def setup_figure(self):
        """
        Runs once during App initialization, after setup()
        This is the place to make all graphical interface initializations,
        build plots, etc.
        """
        
        # connect settings to ui
        self.stage.settings.x_position.connect_to_widget(self.ui.x_pos_doubleSpinBox)
        self.stage.settings.y_position.connect_to_widget(self.ui.y_pos_doubleSpinBox)
        # die zeile drunter war auskommentiert?
        self.settings.scan_direction.connect_to_widget(self.ui.scan_comboBox)
        self.settings.x_start.connect_to_widget(self.ui.x_start_doubleSpinBox)
        self.settings.y_start.connect_to_widget(self.ui.y_start_doubleSpinBox)    
        self.settings.x_size.connect_to_widget(self.ui.x_size_doubleSpinBox)
        self.settings.y_size.connect_to_widget(self.ui.y_size_doubleSpinBox)
        self.settings.x_step.connect_to_widget(self.ui.x_step_doubleSpinBox)
        self.settings.y_step.connect_to_widget(self.ui.y_step_doubleSpinBox)
        self.settings.x_clicked.connect_to_widget(self.ui.x_clicked_doubleSpinBox)
        self.settings.y_clicked.connect_to_widget(self.ui.y_clicked_doubleSpinBox)
        self.settings.lock_position.connect_to_widget(self.ui.lock_position_checkBox)
        self.settings.save_positions.connect_to_widget(self.ui.save_positions_checkBox)
        self.settings.progress.connect_to_widget(self.ui.progressBar)
        

        #stage ui base
        self.stage_layout=pg.GraphicsLayoutWidget()
        self.ui.stage_groupBox.layout().addWidget(self.stage_layout)
        self.stage_plot = self.stage_layout.addPlot(title="Stage view")
        self.stage_plot.setXRange(0, 100)
        self.stage_plot.setYRange(0, 100)
        self.stage_plot.setLimits(xMin=0, xMax=100, yMin=0, yMax=100)
        



        self.scan_roi = pg.ROI([0,0],[25, 25], movable=True)
        self.handle1 = self.scan_roi.addScaleHandle([1, 1], [0, 0])
        self.handle2 = self.scan_roi.addScaleHandle([0, 0], [1, 1])        
        self.scan_roi.sigRegionChangeFinished.connect(self.mouse_update_scan_roi)
        self.scan_roi.sigRegionChangeFinished.connect(self.update_ranges)
        self.stage_plot.addItem(self.scan_roi) #region of interest - allows user to select scan area

        #setup ui signals
        self.ui.start_scan_pushButton.clicked.connect(self.start)
        # self.ui.interrupt_scan_pushButton.clicked.connect(self.interrupt)
        self.ui.interrupt_scan_pushButton.clicked.connect(self.interrupt_scan)
        self.ui.zeroStage_pushButton.clicked.connect(self.return_Home)

        self.ui.move_to_selected_pushButton.clicked.connect(self.move_to_selected)
        self.ui.export_positions_pushButton.clicked.connect(self.export_positions)

        self.ui.x_start_doubleSpinBox.valueChanged.connect(self.update_roi_start)
        self.ui.y_start_doubleSpinBox.valueChanged.connect(self.update_roi_start)
        self.ui.x_size_doubleSpinBox.valueChanged.connect(self.update_roi_size)
        self.ui.y_size_doubleSpinBox.valueChanged.connect(self.update_roi_size)
        self.ui.x_step_doubleSpinBox.valueChanged.connect(self.update_roi_start)
        self.ui.y_step_doubleSpinBox.valueChanged.connect(self.update_roi_start)

        self.ui.x_size_doubleSpinBox.valueChanged.connect(self.update_ranges)
        self.ui.y_size_doubleSpinBox.valueChanged.connect(self.update_ranges)
        self.ui.x_step_doubleSpinBox.valueChanged.connect(self.update_ranges)
        self.ui.y_step_doubleSpinBox.valueChanged.connect(self.update_ranges)

        #histogram for image
        self.hist_lut = pg.HistogramLUTItem()
        self.stage_layout.addItem(self.hist_lut)

        #image on stage plot, will show intensity sums
        self.img_item = pg.ImageItem()
        self.stage_plot.addItem(self.img_item)
        blank = np.zeros((3,3))
        self.img_item.setImage(image=blank) #placeholder image
        
        self.hist_lut.setImageItem(self.img_item) #setup histogram

        #arrow showing stage location
        self.current_stage_pos_arrow = pg.ArrowItem()
        self.current_stage_pos_arrow.setZValue(100)
        self.stage_plot.addItem(self.current_stage_pos_arrow)
        self.stage.settings.x_position.updated_value.connect(self.update_arrow_pos, QtCore.Qt.UniqueConnection)
        self.stage.settings.y_position.updated_value.connect(self.update_arrow_pos, QtCore.Qt.UniqueConnection)

        #Define crosshairs that will show up after scan, event handling.
        self.vLine = pg.InfiniteLine(angle=90, movable=False, pen='r')
        self.hLine = pg.InfiniteLine(angle=0, movable=False, pen='r')
        self.stage_plot.scene().sigMouseClicked.connect(self.ch_click)

        #  from Chopper Hardware
        self.chopper.settings.Frequency.connect_to_widget(self.ui.frequency_doubleSpinBox)
        self.chopper.settings.BladeType.connect_to_widget(self.ui.bladeType_comboBox)
        self.chopper.settings.OnOff.connect_to_widget(self.ui.chopper_on_off_comboBox)

        self.ui.frequency_doubleSpinBox.valueChanged.connect(self.setFrequency)
        self.ui.bladeType_comboBox.currentIndexChanged.connect(self.setBladeType)
        self.ui.chopper_on_off_comboBox.currentIndexChanged.connect(self.enable)

    def ch_click(self, event):
        '''
        Handle crosshair clicking, which toggles movement on and off.
        '''
        pos = event.scenePos()
        if not self.settings['lock_position'] and self.stage_plot.sceneBoundingRect().contains(pos):
            mousePoint = self.stage_plot.vb.mapSceneToView(pos)
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())
            self.settings['x_clicked'] = mousePoint.x()
            self.settings['y_clicked'] = mousePoint.y()
            if self.settings['save_positions']:
                self.selected_positions[self.selected_count, 0] = mousePoint.x()
                self.selected_positions[self.selected_count, 1] = mousePoint.y()
                self.selected_count += 1
                if self.stage.settings["debug_mode"]:
                    print("Point appended.")

    def export_positions(self):
        """ Export selected positions into txt. """
        self.check_filename("_selected_positions.txt")
        trimmed = self.selected_positions[~np.all(self.selected_positions == 0, axis=1)] #get rid of empty rows
        np.savetxt(self.app.settings['save_dir']+"/"+ self.app.settings['sample'] + "_selected_positions.txt", trimmed, fmt='%f')
        if self.stage.settings["debug_mode"]:
            print("Selected points saved.")
            
    def move_to_selected(self):
        """Move stage to position selected by crosshairs."""
        if self.scan_complete and hasattr(self, 'pi_device'):
            x = self.settings['x_clicked']
            y = self.settings['y_clicked']
            self.pi_device.MOV(axes=self.axes, values=[x, y])
            self.stage.read_from_hardware()

    def mouse_update_scan_roi(self):
        """Update settings and spinboxes to reflect region of interest."""
        x0,y0 =  self.scan_roi.pos()
        w, h =  self.scan_roi.size()
        if self.settings['x_step'] > 0: 
            self.settings['x_start'] = x0
        else: 
            self.settings['x_start'] = x0 + w

        if self.settings['y_step'] > 0:
            self.settings['y_start'] = y0
        else:
            self.settings['y_start'] = y0 + h 

        self.settings['x_size'] = w
        self.settings['y_size'] = h

    def update_roi_start(self):
        """Update region of interest start position according to spinboxes"""
        x_roi = self.settings['x_start'] #default start values that work with positive x and y steps
        y_roi = self.settings['y_start']
        if self.settings['x_step'] < 0:
            x_roi = self.settings['x_start'] - self.settings['x_size']
        if self.settings['y_step'] < 0:
            y_roi = self.settings['y_start'] - self.settings['y_size']
        self.scan_roi.setPos(x_roi, y_roi)

    def update_roi_size(self):
        ''' Update region of interest size according to spinboxes '''
        self.scan_roi.setSize((self.settings['x_size'], self.settings['y_size']))

    def update_ranges(self):
        """ 
        Update # of pixels calculation (x_range and y_range) when spinboxes change
        This is important in getting estimated scan time before scan starts.
        """
        self.x_scan_size = self.settings['x_size']
        self.y_scan_size = self.settings['y_size']
        
        self.x_step = self.settings['x_step']
        self.y_step = self.settings['y_step']

        if self.y_scan_size == 0:
            self.y_scan_size = 1
            self.y_step = 1
        
        if self.x_scan_size == 0:
            self.x_scan_size = 1
            self.x_step = 1
        
        if self.y_step == 0:
            self.y_step = 1
            
        if self.x_step == 0:
            self.x_step = 1

        self.x_range = np.abs(int(np.ceil(self.x_scan_size/self.x_step)))
        self.y_range = np.abs(int(np.ceil(self.y_scan_size/self.y_step)))
        self.update_estimated_scan_time()

    def return_Home(self):
        # Stage kommt nicht immer auf einen Wert von 0.00 bei X/Y aber immer <0.10 µm
        # Das kann eine Eigenart der Hardware sein, da ein manuelles Verfahren auf genau 0.00 enden kann
        # wenn die Achsen nacheinander 0 angenähert werden
        x = self.stage.settings['x_position']
        y = self.stage.settings['y_position']
        if x != 0:
            # self.stage.move_pos_slow(0, None, None)
            self.stage.nanodrive.set_pos_ax(0, 1)
            time.sleep(0.1)
            x_position = self.stage.nanodrive.get_pos_ax(1)
            y_position = self.stage.nanodrive.get_pos_ax(2)
            self.stage.settings.x_position.update_value(x_position)
            self.stage.settings.y_position.update_value(y_position)
        if y != 0:
            # self.stage.move_pos_slow(None, 0, None)
            self.stage.nanodrive.set_pos_ax(0, 2)
            time.sleep(0.1)
            x_position = self.stage.nanodrive.get_pos_ax(1)
            y_position = self.stage.nanodrive.get_pos_ax(2)
            self.stage.settings.x_position.update_value(x_position)
            self.stage.settings.y_position.update_value(y_position)
        print(f"Returned stage to Position ({self.stage.settings['x_position']}, {self.stage.settings['y_position']})")



    def update_estimated_scan_time(self):
        """implemented in hard-specific scan programs"""
        pass

    def update_arrow_pos(self):
        '''
        Update arrow position on image to stage position
        '''
        x = self.stage.settings['x_position']
        y = self.stage.settings['y_position']
        self.current_stage_pos_arrow.setPos(x,y)

    def pre_run(self):
        """
        Define devices, scan parameters, and move stage to start.
        """
        self.nanodrive = self.stage.nanodrive
        # Disable ROI and spinboxes during scan
        self.scan_roi.removeHandle(self.handle1)
        self.scan_roi.removeHandle(self.handle2)
        self.scan_roi.translatable = False
        for lqname in "scan_direction x_start y_start x_size y_size x_step y_step".split():
            self.settings.as_dict()[lqname].change_readonly(True)

        # Get starting positions from settings
        self.x_start = self.settings['x_start']
        self.y_start = self.settings['y_start']

        # Move to starting positions
        current_x_pos = self.stage.settings['x_position']
        current_y_pos = self.stage.settings['y_position']
        step_size = self.settings['step_size']
        new_x_pos = self.x_start
        new_y_pos = self.y_start
        self.nanodrive.set_pos(new_x_pos, new_y_pos, None)
        time.sleep(0.1)
        """if current_x_pos < new_x_pos:
            while current_x_pos < new_x_pos:
                current_x_pos += step_size
                self.stage.move_pos_slow(current_x_pos, None, None)
                # self.wait_for_move()
        else:
            while current_x_pos > new_x_pos:
                current_x_pos -= step_size
                self.stage.move_pos_slow(current_x_pos, None, None)
                # self.wait_for_move()
        if current_y_pos < new_y_pos:
            while current_y_pos < new_y_pos:
                current_y_pos += step_size
                self.stage.move_pos_slow(None, current_y_pos, None)
                # self.wait_for_move()
        else:
            while current_y_pos > new_y_pos:
                current_y_pos -= step_size
                self.stage.move_pos_slow(None, current_y_pos, None)
                # self.wait_for_move()"""
        self.stage.read_from_hardware()



    def update_display(self):
        """
        Displays (plots) the numpy array self.buffer. 
        This function runs repeatedly and automatically during the measurement run.
        its update frequency is defined by self.display_update_period
        """
        self.stage.read_from_hardware()
        roi_pos = self.scan_roi.pos()
        self.img_item_rect = QtCore.QRectF(roi_pos[0], roi_pos[1], self.settings['x_size'], self.settings['y_size'])
        self.img_item.setRect(self.img_item_rect)

        if self.scan_complete:
            self.ui.estimated_time_label.setText("Estimated time remaining: 0s")
            self.ui.progressBar.setValue(100)
            self.set_progress(100)
            self.stage_plot.addItem(self.hLine)
            self.stage_plot.addItem(self.vLine)

            x, y = self.scan_roi.pos()
            middle_x = x + self.settings['x_size']/2
            middle_y = y + self.settings['y_size']/2
            self.hLine.setPos(middle_y)
            self.vLine.setPos(middle_x)

    def run(self):
        self.scan_complete = False
        self.pixels_scanned = 0
        t2 = time.time()
        step_size = self.settings["step_size"]

        # Chopper
        get_frequency = []
        get_frequency.append(self.chopper.get_frequency())

        # Read initial origin positions once
        origin_x = self.nanodrive.get_pos_ax(1)
        origin_y = self.nanodrive.get_pos_ax(2)

        if self.settings['scan_direction'] == 'XY':
            for i in range(self.y_range):
                # Determine Y position based on index and step
                if self.y_step > 0:
                    y_pos = origin_y + i * self.y_step
                    self.index_y = i
                else:
                    y_pos = origin_y + (self.y_range - i - 1) * self.y_step
                    self.index_y = self.y_range - i - 1

                self.nanodrive.set_pos(None, y_pos, None)
                self.stage.settings['y_position'] = y_pos
                time.sleep(0.1)  # Optional settle time for Y move

                for j in range(self.x_range):
                    t0 = time.time()
                    if self.interrupt_measurement_called:
                        break

                    # Determine X position based on index and step
                    if self.x_step > 0:
                        x_pos = origin_x + j * self.x_step
                        self.index_x = j
                    else:
                        x_pos = origin_x + (self.x_range - j - 1) * self.x_step
                        self.index_x = self.x_range - j - 1

                    # Move to the absolute X position
                    self.nanodrive.set_pos(x_pos, None, None)
                    self.stage.settings['x_position'] = x_pos
                    time.sleep(0.1)  # Optional settle time

                    t1 = time.time()
                    self.scan_measure()
                    if self.stage.settings["debug_mode"]:
                        print("Scan measure time: " + str(time.time() - t1))

                self.pixels_scanned += 1

                if self.interrupt_measurement_called:
                    break
        # Read initial positions once as origin
        origin_x = self.nanodrive.get_pos_ax(1)
        origin_y = self.nanodrive.get_pos_ax(2)

        if self.settings['scan_direction'] == 'YX':
            for i in range(self.x_range):
                # Determine absolute X position for this column
                if self.x_step > 0:
                    x_pos = origin_x + i * self.x_step
                    self.index_x = i
                else:
                    x_pos = origin_x + (self.x_range - i - 1) * self.x_step
                    self.index_x = self.x_range - i - 1

                self.nanodrive.set_pos(x_pos, None, None)
                self.stage.settings['x_position'] = x_pos
                time.sleep(0.1)  # Optional settle

                for j in range(self.y_range):
                    t0 = time.time()
                    if self.interrupt_measurement_called:
                        break

                    # Determine absolute Y position
                    if self.y_step > 0:
                        y_pos = origin_y + j * self.y_step
                        self.index_y = j
                    else:
                        y_pos = origin_y + (self.y_range - j - 1) * self.y_step
                        self.index_y = self.y_range - j - 1

                    self.nanodrive.set_pos(None, y_pos, None)
                    self.stage.settings['y_position'] = y_pos
                    time.sleep(0.1)  # Optional settle

                # Perform the measurement
                    self.scan_measure()
                    if self.stage.settings["debug_mode"]:
                        print("Scan measure time: " + str(time.time() - t0))

                    self.pixels_scanned += 1

                    if self.stage.settings["debug_mode"]:
                        print("Pixel scan time: " + str(time.time() - t0))

                if self.interrupt_measurement_called:
                    break
        get_frequency.append(self.chopper.get_frequency())
        self.ui.get_Frequency_Text.setText(str(get_frequency))

    def post_run(self):
        """Re-enable roi and spinboxes. """
        self.handle1 = self.scan_roi.addScaleHandle([1, 1], [0, 0])
        self.handle2 = self.scan_roi.addScaleHandle([0, 0], [1, 1])
        self.scan_roi.translatable = True
        for lqname in "scan_direction x_start y_start x_size y_size x_step y_step".split():
            self.settings.as_dict()[lqname].change_readonly(False)
        if self.stage.settings["debug_mode"]:
            print("Scan complete.")
            
    def scan_measure(self):
        """
        Not defined in this class. This is defined in hardware-specific scans that inherit this class.
        """
        pass

    def check_filename(self, append):
        """
        If no sample name given or duplicate sample name given, fix the problem by appending a unique number.
        append - string to add to sample name (including file extension)
        """
        samplename = self.app.settings['sample']
        filename = samplename + append
        directory = self.app.settings['save_dir']
        if samplename == "":
            self.app.settings['sample'] = int(time.time())
        if (os.path.exists(directory+"/"+filename)):
            self.app.settings['sample'] = samplename + str(int(time.time()))
    
    def set_details_widget(self, widget = None, ui_filename=None):
        """ Helper function for setting up ui elements for settings. """
        #print('LOADING DETAIL UI')
        if ui_filename is not None:
            details_ui = load_qt_ui_file(ui_filename)
        if widget is not None:
            details_ui = widget
        if hasattr(self, 'details_ui'):
            if self.details_ui is not None:
                self.details_ui.deleteLater()
                self.ui.details_groupBox.layout().removeWidget(self.details_ui)
                #self.details_ui.hide()
                del self.details_ui
        self.details_ui = details_ui
        #return replace_widget_in_layout(self.ui.details_groupBox,details_ui)
        self.ui.details_groupBox.layout().addWidget(self.details_ui)
        return self.details_ui

    def save_intensities_data(self, intensities_array, hw_name):
        """
        intensities_array - array of intensities to save
        hw_name - string that describes intensities source (ie. oo for oceanoptics, ph for picoharp) 
        """
        append = '_' + hw_name + '_intensity_sums.txt' #string to append to sample name
        self.check_filename(append)
        transposed = np.transpose(intensities_array)
        np.savetxt(self.app.settings['save_dir']+"/"+ self.app.settings['sample'] + append, transposed, fmt='%f')

        if self.stage.settings["debug_mode"]:
            print("Intensities array saved.")

    def save_intensities_image(self, intensities_array, hw_name):
        """
        intensities_array - array of intensities to save as image
        hw_name - string that describes intensities source (ie. oo for oceanoptics, ph for picoharp) 
        """
        append = '_' + hw_name + '_intensity_sums.png'
        cpm.plot_confocal(intensities_array, stepsize=np.abs(self.settings['x_step']))
        self.check_filename(append)
        cpm.plt.savefig(self.app.settings['save_dir'] + '/' + self.app.settings['sample'] + append, bbox_inches='tight', dpi=300)
        if self.stage.settings["debug_mode"]:
            print("Intensities image saved.")

    def save_photocurrent_data(self, photocurrent_array, hw_name):
        """
        photocurrent_array - array of photocurrent to save
        hw_name - string that describes photocurrent source (ie. smu for smu, ph for picoharp)
        """
        append = '_' + hw_name + '_photocurrent_means.txt'
        self.check_filename(append)
        transposed = np.transpose(photocurrent_array)
        np.savetxt(self.app.settings['save_dir']+"/"+ self.app.settings['sample'] + append, transposed)

        if self.stage.settings["debug_mode"]:
            print("Photocurrent array saved.")

    def save_photocurrent_image(self, photocurrent_array, hw_name):
        """
        photocurrent_array - array of photocurrent to save as image
        hw_name - string that describes photocurrent source (ie. smu for smu, ph for picoharp)
        """
        append = '_' + hw_name + '_photocurrent_means.png'
        cpm.plot_confocal(photocurrent_array, stepsize=np.abs(self.settings['x_step']), units='um', cbar_label="Photocurrent (A)")
        self.check_filename(append)
        cpm.plt.savefig(self.app.settings['save_dir'] + '/' + self.app.settings['sample'] + append, bbox_inches='tight', dpi=300)
        if self.stage.settings["debug_mode"]:
            print("Photocurrent image saved.")

    def save_phase_data(self, phase_array, hw_name):
        """
        phase_array - array of phase to save
        hw_name - string that describes phase source (ie. smu for smu, ph for picoharp, lia for lock-in-amplifier)
        """
        append = '_' + hw_name + '_phase_means.txt'
        self.check_filename(append)
        transposed = np.transpose(phase_array)
        np.savetxt(self.app.settings['save_dir']+"/"+ self.app.settings['sample'] + append, transposed)

        if self.stage.settings["debug_mode"]:
            print("Phase array saved.")

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
