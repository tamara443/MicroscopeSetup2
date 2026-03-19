import pandas as pd
import numpy as np
import re
import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.signal import find_peaks


def select_directory():
    # Create a Tkinter root window
    root = tk.Tk()
    root.withdraw() # Hide the root window

    # Open a directory slection dialog
    directory_path = filedialog.askdirectory()
    return directory_path

def select_file():
    # Create a Tkinter root window
    root = tk.Tk()
    root.withdraw()  # Hide the root window

    # Open a file selection dialog within the selected directory
    file_path = filedialog.askopenfilename()
    return file_path

def open_file():
    file_path = select_file()
    if file_path:
        print(f"Selected file: {file_path}")
        return file_path
    else:
        print("No file selected.")

def read_txt(file_name):
    txt = pd.DataFrame()
    txt = pd.read_csv(file_name, sep=" ", header=None)
    txt = txt.shift(-1)
    txt = txt.dropna(axis=1, how="all")
    txt = txt.drop(2068)
    txt.columns = ["Wavelength", "Intensity"]
    return txt.Intensity

def extract_xy(title):
    match = re.search(r'X (\d+) - Y (\d+)', title)
    if match:
        x_value = int(match.group(1))
        y_value = int(match.group(2))
        return x_value, y_value
    else:
        return None, None

def modified_z_score(intensity):
    median_int = np.median(intensity)
    mad_int = np.median([np.abs(intensity - median_int)])
    modified_z_scores = 0.6745 * (intensity - median_int) / mad_int
    return modified_z_scores

def calculate_delta(intensity):
    # First we calculated ∇x(i):
    dist = 0
    delta_intensity = []
    for i in np.arange(len(intensity) - 1):
        dist = intensity[i + 1]-intensity[i]
        delta_intensity.append(dist)
        delta_int = np.array(delta_intensity)
    # Alternatively to the for loop one can use:
    # delta_int = np.diff(intensity)
    return delta_int

def fixer(y, m, threshold=3.5, peak_regions=None):
    # peak_regions: a list of tuples (start, end) specifying regions where peaks are expected

    # Detect spikes using modified Z-score
    spikes = abs(np.array(modified_z_score(np.diff(y)))) > threshold
    y_out = y.copy()

    for i in np.arange(len(spikes)):
        # If we have a spike in position i and it's not in a peak region
        in_peak_region = False
        if peak_regions:
            for start, end in peak_regions:
                if start <= i <= end:
                    in_peak_region = True
                    break

        if spikes[i] != 0 and not in_peak_region:
            # Select a window around the spike
            w = np.arange(max(i - m, 0), min(i + 1 + m, len(y)))  # handle boundaries

            # Ensure we only average non-spike values
            w2 = w[spikes[w] == 0]
            if len(w2) > 0:
                y_out[i] = np.mean(y[w2])  # average their values

    return y_out

def parse_settings(file_path):
    settings = {}
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if ": " in line:
                key, value = line.split(": ", 1)
                settings[key] = value
    return settings

def get_scan_parameters(settings):
    x_step_size = float(settings.get("X step size (um)", 0))
    y_step_size = float(settings.get("Y step size (um)", 0))
    return x_step_size, y_step_size

def load_data():
    print("Select a CSV file to analyze.")
    csv_file_name = open_file()
    df = pd.read_csv(csv_file_name)
    # Drop the index column if it exists
    if 'Unnamed: 0' in df.columns:
        df = df.drop('Unnamed: 0', axis=1)

    # Extract wavelengths as a flat array
    wavelengths = df['Wavelengths'].values

    # Remove the 'Wavelengths' column from the DataFrame
    df = df.loc[:, df.columns != 'Wavelengths']

    print("Select a dark count text file to subtract.")
    dark_file = open_file()
    dark_count = read_txt(dark_file)

    # Ensure dark_count is a Series of numeric values
    dark_count = pd.to_numeric(dark_count, errors='coerce')

    # Check if dark_count is the same length as the DataFrame
    if len(dark_count) != len(df):
        raise ValueError("The length of the dark count data does not match the number of rows in the CSV file.")

    # Subtract dark count from each column in the DataFrame
    new_df = df.sub(dark_count, axis=0)
    return wavelengths, new_df

def gaussian_with_baseline(x, a, b, c, d):
    # a: amplitude, b: mean, c: standard deviation, d: baseline offset
    return a * np.exp(-0.5 * ((x - b) / c) ** 2) + d

def fit_gaussian(wavelengths, intensities):
    # Initial guess for the parameters: [amplitude, mean, standard deviation, baseline offset]
    initial_guess = [max(intensities) - min(intensities), wavelengths[np.argmax(intensities)], 10, min(intensities)]
    try:
        popt, _ = curve_fit(gaussian_with_baseline, wavelengths, intensities, p0=initial_guess)
        a, b, c, d = popt
        fwhm = 2 * np.sqrt(2 * np.log(2)) * c
        return a, b, fwhm, d
    except RuntimeError:
        print("Gaussian fit failed")
        return None, None, None, None


def save_data_to_file(save_folder,filename, wavelengths, intensities, fitted_curve=None, a=None, b=None, fwhm=None, d=None):
    filename = save_folder + "/" + filename

    # Create the main DataFrame for the entire spectrum
    df_main = pd.DataFrame({
        'Wavelength [nm]': wavelengths,
        'PL Intensity [counts]': intensities,
    })

    # Add fitted values if available
    if fitted_curve is not None:
        df_main['Fitted Values [counts]'] = fitted_curve

    # Create the header for the file
    header = ""
    if a is not None and b is not None and fwhm is not None and d is not None:
        header = f"Peak Maximum: {a}\nPeak Position: {b}\nFWHM: {fwhm}\nBaseline Offset: {d}\n"

    # Save to a text file
    with open(filename, 'w') as f:
        f.write(header)
        df_main.to_csv(f, index=False, sep='\t', na_rep='NaN')


def find_peak_within_range(wavelengths, intensities, wavelength_min, wavelength_max, prominence=0.1, width=5):
    # Filter wavelengths and intensities within the specified range
    mask = (wavelengths >= wavelength_min) & (wavelengths <= wavelength_max)
    filtered_wavelengths = wavelengths[mask]
    filtered_intensities = intensities[mask]

    # Check if there is any data in the filtered range
    if len(filtered_wavelengths) == 0 or len(filtered_intensities) == 0:
        return None, None

    # Find peaks within the specified range
    peaks, properties = find_peaks(filtered_intensities, prominence=prominence, width=width)

    # If no peaks are found, return None
    if len(peaks) == 0:
        return None, None

    # Get the peak with the highest prominence
    peak_index = peaks[np.argmax(properties['prominences'])]
    peak_wavelength = filtered_wavelengths[peak_index]
    peak_intensity = filtered_intensities[peak_index]

    return peak_wavelength, peak_intensity

def PL_analysis(save_folder, df, wavelengths, x_step_size, y_step_size, x_check, y_check, wavelength_min, wavelength_max, prominence, width):
    # Find the column that matches the target X and Y values
    target_x = int(x_check / x_step_size)
    target_y = int(y_check / y_step_size)
    target_column = None
    for column in df:
        x, y = extract_xy(column)
        if x == target_x and y == target_y:
            target_column = df[column]
            intensity_without_spikes = fixer(target_column.values, m=3, threshold=3.5, peak_regions=[(wavelength_min, wavelength_max)])

            # Shift spectrum to non-negative values
            # min_intensity = min(intensity_without_spikes)
            # if min_intensity < 0:
                # intensity_without_spikes += abs(min_intensity)

            # Plot the intensity spectrum
            plt.plot(wavelengths, intensity_without_spikes, label='Data')
            # plt.plot(wavelengths, intensity_without_spikes, label='Data')
            plt.title('PL Intensity Spectrum at  X = '+str(x_check)+' µm and Y = '+str(y_check)+' µm', fontsize=20)
            plt.xticks(fontsize=15)
            plt.yticks(fontsize=15)
            plt.xlabel('Wavelength (nm)', fontsize=20)
            plt.ylabel('Intensity (a.u.)', fontsize=20)

            # Find peak within the specified range
            peak_wavelength, peak_intensity = find_peak_within_range(wavelengths, intensity_without_spikes,
                                                                     wavelength_min, wavelength_max, prominence, width)

            if peak_wavelength is not None:
                # Fit Gaussian over the entire wavelength range
                a, b, fwhm, d = fit_gaussian(wavelengths, intensity_without_spikes)
                if a is not None and (wavelength_min <= b <= wavelength_max):
                    fitted_curve = gaussian_with_baseline(wavelengths, a, b, fwhm / (2 * np.sqrt(2 * np.log(2))), d)
                    plt.plot(wavelengths, fitted_curve, label='Gaussian Fit with Baseline')
                    plt.legend()

                    print(f"Peak Maximum: {a}")
                    print(f"Peak Position: {b}")
                    print(f"FWHM: {fwhm}")
                    print(f"Baseline Offset: {d}")

                    # Save the data to a file with fit
                    filename = f"PL_Spectrum_X_{x_check}_Y_{y_check}.txt"
                    save_data_to_file(save_folder, filename, wavelengths, intensity_without_spikes, fitted_curve, a, b,
                                      fwhm, d)
                else:
                    # Save the data to a file without fit
                    filename = f"PL_Spectrum_X_{x_check}_Y_{y_check}_no_fit.txt"
                    save_data_to_file(save_folder, filename, wavelengths, intensity_without_spikes)
            else:
                # Save the data to a file without fit
                filename = f"PL_Spectrum_X_{x_check}_Y_{y_check}_no_fit.txt"
                save_data_to_file(save_folder, filename, wavelengths, intensity_without_spikes)

            plt.show()
            break

def get_user_inputs():
    while True:
        try:
            print("At which X and Y value do you want to see the PL Intensity plot?")
            x_check = float(input("X Value (in µm): "))
            y_check = float(input("Y Value (in µm): "))
            return x_check, y_check
        except ValueError:
            print("Invalid input. Please enter numeric values for X and Y.")

def get_wavelength_range():
    while True:
        try:
            print("Enter the wavelength range for the PL Intensity plot.")
            wavelength_min = float(input("Minimum Wavelength (in nm): "))
            wavelength_max = float(input("Maximum Wavelength (in nm): "))
            if wavelength_min < wavelength_max:
                return wavelength_min, wavelength_max
            else:
                print("Minimum wavelength must be less than maximum wavelength.")
        except ValueError:
            print("Invalid input. Please enter numeric values for the wavelength range.")

def main():
    print("Choose a measurement settings file.")
    settings_file_path = select_file()
    settings = parse_settings(settings_file_path)
    x_step_size, y_step_size = get_scan_parameters(settings)
    wavelengths, df = load_data()
    print("Select a folder to save the results.")
    save_folder = select_directory()
    wavelength_min, wavelength_max = get_wavelength_range()

    # Define default prominence and width for peak detection
    prominence = 100
    width = 10

    while True:
        x_check, y_check = get_user_inputs()
        PL_analysis(save_folder, df, wavelengths, x_step_size, y_step_size, x_check, y_check, wavelength_min, wavelength_max,
                    prominence, width)

        continue_plotting = input("Do you want to plot another column? (yes/no): ").strip().lower()
        if continue_plotting != 'yes':
            break

if __name__ == "__main__":
    main()
