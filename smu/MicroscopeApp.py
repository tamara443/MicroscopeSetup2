from ScopeFoundry import BaseMicroscopeApp


class MicroscopeApp(BaseMicroscopeApp):

    # this ist the name of the microscope that ScopeFoundry uses when storing data
    name = 'smu_microscope'

    # You must define a setup function that adds all the capabilities of the microscope and sets default settings
    def setup(self):

        # Add App wide settings
        # Add hardware components0
        from yokogawa_hardware import Yokogawa_HW
        self.add_hardware(Yokogawa_HW(self))

        # Add measurement components
        from yokogawa_measurement import Yokogawa_Measurement
        self.add_measurement(Yokogawa_Measurement(self))
        self.ui.show()
        self.ui.activateWindow()


if __name__ == '__main__':
    import sys

    app = MicroscopeApp(sys.argv)
    sys.exit(app.exec_())
