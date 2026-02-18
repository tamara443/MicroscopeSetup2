
from ScopeFoundry import BaseMicroscopeApp

class MicroscopeApp(BaseMicroscopeApp):

	# this is the name of the microscope that ScopeFoundry uses 
	# when storing datay
	name = 'microscope'
	
	# You must define a setup function that adds all the 
	#capablities of the microscope and sets default settings
	def setup(self):
	
		#Add Hardware components
		from mcl_xyz_stage_hardware import MclXYZStageHW
		self.add_hardware(MclXYZStageHW(self))

		#Add Measurement components
		from mcl_stage_slowscan import MCLStage2DSlowScan
		self.add_measurement(MCLStage2DSlowScan(self))
		#from PiezoStage_independent_movement import PiezoStageIndependentMovement
		#self.add_measurement(PiezoStageIndependentMovement)
		#from PiezoStage_control import PiezoStageControl
		#self.add_measurement(PiezoStageControl)
		from mcl_stagecontrol import PiezoStageControl
		self.add_measurement(PiezoStageControl)

		# show ui
		self.ui.show()
		self.ui.activateWindow()

	def on_close(self): #temp fix for properly closing the additional imageview window
		BaseMicroscopeApp.on_close(self)
		try:
			oo_scan = self.measurements["OceanOptics_Scan"]
			oo_scan.imv.close()
			oo_scan.graph_layout.close()
		except:
			pass

if __name__ == '__main__':
	import sys
	
	app = MicroscopeApp(sys.argv)

	sys.exit(app.exec_())