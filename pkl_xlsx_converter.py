import pandas as pd
import pickle
import os

# Load pickle file
with open(r'C:\Users\EEFM\Desktop\BA_Philipp\MicroscopeSetup\data\17050720171705072068_raw_PL_spectra_data.pkl', 'rb') as f:
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

# Save converted file to desktop
desktop_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
df.to_excel(os.path.join(desktop_path, 'stagescan1000ms2avg2.xlsx'), index=False)






