import sys
import os
from ScopeFoundry import BaseMicroscopeApp

currDir = os.path.dirname(os.path.abspath(__file__))
laser = os.path.join(currDir, "laser")
dll_path = os.path.join(laser, "NKTPDLL\\x64\\NKTPDLL.dll")
sys.path.append(laser)

class MicroscopeApp(BaseMicroscopeApp):

    # this is the name of the microscope that ScopeFoundry uses

    
    # when storing data
    name = 'microscope'
    
    # You must define a setup function that adds all the 
    # capabilities of the microscope and sets default settings
    def setup(self):
        # Add Hardware components
        from mcl_stage.mcl_xyz_stage_hardware import MclXYZStageHW
        self.add_hardware(MclXYZStageHW(self))
        from oceanoptics_spec.OceanOptics_hardware import OceanOpticsHW
        self.add_hardware(OceanOpticsHW(self))
        from smu.yokogawa_hardware import Yokogawa_HW
        self.add_hardware(Yokogawa_HW(self))
        from smu.yokogawa_2_hardware import Yokogawa_HW_2
        self.add_hardware(Yokogawa_HW_2(self))
        from smu.Keysight_Hardware import Keysight_HW
        self.add_hardware(Keysight_HW(self))
        from chopper.chopper_hw import Chopper_HW
        self.add_hardware(Chopper_HW(self))
        from LIA.LIA_HW import LIA_HW
        self.add_hardware(LIA_HW(self))

        # Add Measurement components
            # Stage
        from mcl_stage.mcl_stage_slowscan import MCLStage2DSlowScan
        self.add_measurement(MCLStage2DSlowScan(self))
        from mcl_stage.mcl_stagecontrol import PiezoStageControl
        self.add_measurement(PiezoStageControl)
            # Spectrometer
        from oceanoptics_spec.OceanOptics_measurement import OceanOpticsMeasure
        self.add_measurement(OceanOpticsMeasure(self))
        from oceanoptics_spec.OceanOptics_Scan import OceanOptics_Scan
        self.add_measurement(OceanOptics_Scan)
            # SMU
        from smu.yokogawa_measurement import Yokogawa_Measurement
        self.add_measurement(Yokogawa_Measurement)
        #from chopper.chopper_measurement import Chopper_Measurement
        #self.add_measurement(Chopper_Measurement)

        # Add the laser control component
        from laser.NKTPDLLwrapper import NKTPDLLWrapper
        from laser.gui_laser import NKTPDLLGUI
        portname = 'COM3'
        NKTPDLLWrapper = NKTPDLLWrapper(dll_path, portname)
        self.add_hardware(NKTPDLLGUI(NKTPDLLWrapper))

        # show ui
        self.ui.show()
        self.ui.activateWindow()

    def on_close(self):
        if self.hardware["MC2000B"].settings['connected']:
            self.hardware["MC2000B"].enable(0)
        if self.hardware["YokogawaGS200_2"].settings['connected']:
            self.hardware["YokogawaGS200_2"].setOutput("OFF")

        self.log.info("on_close")
        # disconnect all hardware objects
        for hw in self.hardware.values():
            self.log.info("disconnecting {}".format( hw.name))
            if hw.settings['connected']:
                try:
                    hw.disconnect()
                except Exception as err:
                    self.log.error("tried to disconnect {}: {}".format( hw.name, err) )

if __name__ == '__main__':
    import sys
    app = MicroscopeApp(sys.argv)
    sys.exit(app.exec_())
