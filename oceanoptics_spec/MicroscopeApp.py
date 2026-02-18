from ScopeFoundry import BaseMicroscopeApp


class InvertedMicroscopeApp(BaseMicroscopeApp):

    # this ist the name of the microscope that ScopeFoundry uses when storing data
    name = 'inverted_microscope'

    # You must define a setup function that adds all the capabilities of the microscope and sets default settings
    def setup(self):

        # Add App wide settings
        # Add hardware components0
        from OceanOptics_hardware import OceanOpticsHW 
        self.add_hardware(OceanOpticsHW(self))

        # Add measurement components
        from OceanOptics_measurement import OceanOpticsMeasure
        self.add_measurement(OceanOpticsMeasure(self))
        self.ui.show()
        self.ui.activateWindow()


if __name__ == '__main__':
    import sys

    app = InvertedMicroscopeApp(sys.argv)
    sys.exit(app.exec_())
