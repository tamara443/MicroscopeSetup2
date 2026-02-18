from __future__ import division, print_function
import numpy as np
from ScopeFoundry.scanning import BaseRaster2DSlowScan, BaseRaster2DFrameSlowScan
from ScopeFoundry import Measurement, LQRange
import time
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
import pyqtgraph as pg

class PiezoStageControl(Measurement): #control
    
    name = "MCLStageControl"


    def setup(self):
        self.ui_filename = sibling_path(__file__, "stage_control.ui")
        
        #Load ui file and convert it to a live QWidget of the user interface
        self.ui = load_qt_ui_file(self.ui_filename)

        Measurement.setup(self)
        
        self.settings.New("h_axis", initial="X", dtype=str, choices=("X", "Y"))
        self.settings.New("v_axis", initial="Y", dtype=str, choices=("X", "Y"))
        self.settings.New('step_size', dtype=float, unit='um', vmin=0.001)
        self.ax_map = dict(X=0, Y=1)
        
        #Hardware
        self.stage = self.app.hardware.mcl_xyz_stage
        
    
    
    def setup_figure(self):
        #connecting settings to ui
        self.stage.settings.x_position.connect_to_widget(self.ui.x_label) # from hardware 
        self.stage.settings.y_position.connect_to_widget(self.ui.y_label) # from hardware 
        self.settings.step_size.connect_to_widget(self.ui.step_size_spinBox) #  not from hardware 

        #setup ui signals
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.up_pushButton.clicked.connect(self.move_up)
        self.ui.right_pushButton.clicked.connect(self.move_right)
        self.ui.down_pushButton.clicked.connect(self.move_down)
        self.ui.left_pushButton.clicked.connect(self.move_left)

        #plot showing stage area
        self.stage_layout=pg.GraphicsLayoutWidget()
        self.ui.stage_groupBox.layout().addWidget(self.stage_layout)
        self.stage_plot = self.stage_layout.addPlot(title="Stage view")
        self.stage_plot.setXRange(0, 100)
        self.stage_plot.setYRange(0, 100)
        self.stage_plot.setLimits(xMin=0, xMax=100, yMin=0, yMax=100) 

        #arrow indicating stage position
        self.current_stage_pos_arrow = pg.ArrowItem()
        self.current_stage_pos_arrow.setZValue(100)
        self.current_stage_pos_arrow.setPos(0, 0)
        self.stage_plot.addItem(self.current_stage_pos_arrow)

    def move_right(self):
        if hasattr(self, 'stage'):
            # current_x_pos = self.stage.settings['x_position']
            current_x_pos = self.stage.nanodrive.get_pos_ax(1)
            step_size = self.settings['step_size']
            new_x_pos = current_x_pos + step_size
            # self.stage.move_pos_fast(new_x_pos, None, None)
            self.stage.nanodrive.set_pos_ax(new_x_pos, 1)
            time.sleep(0.1)
            x_position = self.stage.nanodrive.get_pos_ax(1)
            y_position = self.stage.nanodrive.get_pos_ax(2)
            self.stage.settings.x_position.update_value(x_position)
            self.stage.settings.y_position.update_value(y_position)
            # self.current_stage_pos_arrow.setPos(self.stage.settings['x_position'], self.stage.settings['y_position'])
            self.current_stage_pos_arrow.setPos(x_position, y_position)
            self.current_stage_pos_arrow.update()
            print('New x position:', x_position)

    def move_left(self):
        if hasattr(self, 'stage'):
            # current_x_pos = self.stage.settings['x_position']
            current_x_pos = self.stage.nanodrive.get_pos_ax(1)
            step_size = self.settings['step_size']
            new_x_pos = current_x_pos - step_size
            # self.stage.move_pos_slow(new_x_pos)
            self.stage.nanodrive.set_pos_ax(new_x_pos, 1)
            time.sleep(0.1)
            x_position = self.stage.nanodrive.get_pos_ax(1)
            y_position = self.stage.nanodrive.get_pos_ax(2)
            self.stage.settings.x_position.update_value(x_position)
            self.stage.settings.y_position.update_value(y_position)
            # self.current_stage_pos_arrow.setPos(self.stage.settings['x_position'], self.stage.settings['y_position'])
            self.current_stage_pos_arrow.setPos(x_position, y_position)
            self.current_stage_pos_arrow.update()
            print('New x position:', x_position)

    def move_up(self):
        if hasattr(self, 'stage'):
            # current_y_pos = self.stage.settings['y_position']
            current_y_pos = self.stage.nanodrive.get_pos_ax(2)
            step_size = self.settings['step_size']
            new_y_pos = current_y_pos + step_size
            # self.stage.move_pos_slow(None, new_y_pos)
            self.stage.nanodrive.set_pos_ax(new_y_pos, 2)
            time.sleep(0.1)
            x_position = self.stage.nanodrive.get_pos_ax(1)
            y_position = self.stage.nanodrive.get_pos_ax(2)
            self.stage.settings.x_position.update_value(x_position)
            self.stage.settings.y_position.update_value(y_position)
            # self.current_stage_pos_arrow.setPos(self.stage.settings['x_position'], self.stage.settings['y_position'])
            self.current_stage_pos_arrow.setPos(x_position, y_position)
            self.current_stage_pos_arrow.update()
            print('New y position:', y_position)

    def move_down(self):
        if hasattr(self, 'stage'):
            # current_y_pos = self.stage.settings['y_position']
            current_y_pos = self.stage.nanodrive.get_pos_ax(2)
            step_size = self.settings['step_size']
            new_y_pos = current_y_pos - step_size
            # self.stage.move_pos_slow(None, new_y_pos)
            self.stage.nanodrive.set_pos_ax(new_y_pos, 2)
            time.sleep(0.1)
            x_position = self.stage.nanodrive.get_pos_ax(1)
            y_position = self.stage.nanodrive.get_pos_ax(2)
            self.stage.settings.x_position.update_value(x_position)
            self.stage.settings.y_position.update_value(y_position)
            # self.current_stage_pos_arrow.setPos(self.stage.settings['x_position'],self.stage.settings['y_position'])
            self.current_stage_pos_arrow.setPos(x_position, y_position)
            self.current_stage_pos_arrow.update()
            # print('New y position:', self.stage.settings['y_position'])
            print('New y position:', y_position)

    def run(self):
        self.nanodrive = self.stage.nanodrive
        self.stage.read_from_hardware()
        