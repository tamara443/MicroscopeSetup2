import sys
import typing
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QLabel, QLineEdit, QPushButton
from PyQt5 import QtCore, uic
import pandas as pd
import pickle
import os

# Suppress Pandas warnings regarding performance
import warnings
warnings.simplefilter(action="ignore", category=pd.errors.PerformanceWarning)

class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()

        # Load the ui file
        uic.loadUi(os.path.join(os.path.dirname(__file__), "converter.ui"), self)

        # Define widgets
        self.inputFile = self.findChild(QPushButton, "inputFileButton")
        self.outputFile = self.findChild(QPushButton, "outputFileButton")
        self.convertB = self.findChild(QPushButton, "convertButton")
        self.inputPath = self.findChild(QLineEdit, "inputFilePath")
        self.outputPath = self.findChild(QLineEdit, "outputFilePath")

        # Code the Buttons
        iFile = self.inputFile.clicked.connect(self.openFile)
        oFile = self.outputFile.clicked.connect(self.saveFile)
        self.convertB.clicked.connect(self.convert)

        # Show App
        self.show()

    def openFile (self):
        fname = QFileDialog.getOpenFileName(self, "Choose file to open and convert", "", "PKL File (*.pkl)")
        if fname:
            self.inputPath.setText(str(fname[0]))

    def saveFile (self):
        fname= QFileDialog.getSaveFileName(self, "Choose output filename and directory", "", "Comma-separated values (*.csv)")
        if fname:
            self.outputPath.setText(str(fname[0]))
    
    def getPath(self):
        return self.lineedit.text()

    def convert(self):
        # Filepaths
        iFile = self.inputPath.text()
        oFile = self.outputPath.text()

        if iFile and oFile:
            # Load pickle file
            with open(iFile, 'rb') as f:
                data = pickle.load(f)

            # Convert data to list of dictionaries
            if isinstance(data, dict):
                data = [data]
            elif isinstance(data, list) and all(isinstance(item, dict) for item in data):
                pass
            else:
                raise ValueError("Data in pickle file is not a dictionary or list of dictionaries.")

            # Create empty dictionary to hold intensity values
            intensity_dict = {}

            # Loop over each dictionary in the data list
            for d in data:
                # Get the wavelength values
                wavelength_list = d['Wavelengths']

                # Check if the intensity values are already in the intensity_dict
                if str(d['Intensities']) in intensity_dict:
                    continue

                # Convert the intensity values to a list of lists
                intensity_values = [value.tolist() for value in d['Intensities']]

                # Add the intensity values to the intensity_dict
                intensity_dict[str(d['Intensities'])] = intensity_values

            # Create the pandas DataFrame
            df = pd.DataFrame({'Wavelength': wavelength_list})

            # Loop over the intensity_dict and add the intensity values to the DataFrame
            for i, (intensity_key, intensity_values) in enumerate(intensity_dict.items()):
                # Create a new column for each set of intensity values
                for j in range(len(intensity_values)):
                    df[f'Intensity {i+1} - Set {j+1}'] = pd.Series(intensity_values[j])

            df.to_csv(oFile)

        elif not iFile:
            print("Path to pickle-file for conversion missing")
        elif not oFile:
            print("Output-filepath missing")


# Initialize App
app = QApplication(sys.argv)
UIWindow = UI()
app.exec_()