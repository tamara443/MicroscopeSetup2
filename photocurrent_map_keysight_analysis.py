import numpy as np
import tkinter as tk
from tkinter import filedialog


def select_directory():
    # Create a Tkinter root window
    root = tk.Tk()
    root.withdraw()  # Hide the root window

    # Open a directory selection dialog
    directory_path = filedialog.askdirectory()
    return directory_path


def select_file():
    # Create a Tkinter root window
    root = tk.Tk()
    root.withdraw()  # Hide the root window

    # Open a file selection dialog
    file_path = filedialog.askopenfilename()
    return file_path


def open_file():
    file_path = select_file()
    if file_path:
        print(f"Selected file: {file_path}")
        return file_path
    else:
        print("No file selected.")
        return None


# Step 1: Get the file paths from the user
print("Select a dark current file.")
dark_current_file_path = open_file()
if dark_current_file_path is None:
    exit("Dark current file not selected.")

print("Select a current file to analyze.")
current_file_path = open_file()
if current_file_path is None:
    exit("Current file not selected.")

print("Select a measurement settings file.")
meas_set_file_path = open_file()
if meas_set_file_path is None:
    exit("Measurement settings file not selected.")

# Step 2: Read the value to subtract from the dark current file
with open(dark_current_file_path, 'r') as file:
    dark_current = file.readline().strip()  # Read the first line and strip any extra whitespace
    # Extract the numeric value from the dark current line
    value_to_subtract = float(dark_current.split(':')[-1].strip())

# Step 3: Read the current data from the current file
current = np.loadtxt(current_file_path, delimiter=' ')

# Step 4: Subtract the extracted value from the matrix
photocurrent = current - value_to_subtract

# Step 5: Read scan parameters from the scan parameters file
with open(meas_set_file_path, 'r') as file:
    lines = file.readlines()
    x_scan_size = float([line for line in lines if "X scan size" in line][0].split(':')[-1].strip().replace('um', ''))
    y_scan_size = float([line for line in lines if "Y scan size" in line][0].split(':')[-1].strip().replace('um', ''))
    x_step_size = float([line for line in lines if "X step size" in line][0].split(':')[-1].strip().replace('um', ''))
    y_step_size = float([line for line in lines if "Y step size" in line][0].split(':')[-1].strip().replace('um', ''))

# Step 6: Calculate the number of steps in X and Y directions
x_steps = int(x_scan_size / x_step_size) + 1  # Adding 1 to include the start position
y_steps = int(y_scan_size / y_step_size) + 1  # Adding 1 to include the start position

# Step 7: Create a new matrix including the x_steps and y_steps
rows, cols = photocurrent.shape

# Create a new matrix with extra row and column
extended_photocurrent = np.zeros((rows + 1, cols + 1))

# Insert the x_steps and y_steps
extended_photocurrent[0, 1:] = np.arange(cols) * x_step_size
extended_photocurrent[1:, 0] = np.arange(rows) * y_step_size
extended_photocurrent[1:, 1:] = photocurrent

# Insert x_steps and y_steps in the first row and first column
extended_photocurrent[0, 0] = x_steps
extended_photocurrent[0, 1:] = np.arange(cols) * x_step_size
extended_photocurrent[1:, 0] = np.arange(rows) * y_step_size

# Step 8: Save the modified matrix to a new text file
print("Choose a folder to save the file in.")
save_directory = select_directory()
if not save_directory:
    exit("Save directory not selected.")

# Define the full path for saving the file, including the filename and extension
photocurrent_filename = save_directory + "/Photocurrent_with_steps.txt"
np.savetxt(photocurrent_filename, extended_photocurrent, delimiter=' ')

print(f"Data modified by subtracting {value_to_subtract} and saved to '{photocurrent_filename}'")