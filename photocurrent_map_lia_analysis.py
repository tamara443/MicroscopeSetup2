import numpy as np
import os
import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt

# === Select folder ===
root = tk.Tk()
root.withdraw()
folder = filedialog.askdirectory(title="Select folder containing text files")

if not folder:
    raise SystemExit("No folder selected – exiting.")

# === Find data files in folder ===
phase_file = None
amplitude_file = None
settings_file = None

for file in os.listdir(folder):
    if file.endswith("lia_phase_phase_means.txt"):
        phase_file = os.path.join(folder, file)
    elif file.endswith("smu_pc_photocurrent_means.txt"):
        amplitude_file = os.path.join(folder, file)
    elif file.endswith("MeasurementSettings.txt"):
        settings_file = os.path.join(folder, file)

if not phase_file or not amplitude_file or not settings_file:
    raise FileNotFoundError("Could not find phase, amplitude, or settings file in the selected folder.")

print(f"Found files:\n  Amplitude: {os.path.basename(amplitude_file)}\n  Phase: {os.path.basename(phase_file)}\n  Settings: {os.path.basename(settings_file)}")

# === Load data ===
amplitude = np.loadtxt(amplitude_file)
phase_deg = np.loadtxt(phase_file)

# === Convert phase from degrees to radians ===
phase_rad = np.deg2rad(phase_deg)

# === Compute current ===
current = amplitude * np.cos(phase_rad)

# === Read scan settings ===
with open(settings_file, 'r') as f:
    lines = f.readlines()

# Extract values from the relevant lines
x_scan_size = float(lines[4].split(":")[1].strip())
y_scan_size = float(lines[5].split(":")[1].strip())
x_step_size = float(lines[6].split(":")[1].strip())
y_step_size = float(lines[7].split(":")[1].strip())

# === Compute X and Y arrays ===
num_cols = current.shape[1]
num_rows = current.shape[0]

x_values = np.arange(0, num_cols * x_step_size, x_step_size)
y_values = np.arange(0, num_rows * y_step_size, y_step_size)

# Safety check: if rounding errors make arrays too long
x_values = x_values[:num_cols]
y_values = y_values[:num_rows]

# === Create extended matrix with first row and column ===
current_with_axis = np.zeros((num_rows + 1, num_cols + 1))
current_with_axis[0, 1:] = x_values
current_with_axis[1:, 0] = y_values
current_with_axis[1:, 1:] = current

# === Save result with high precision ===
output_file = os.path.join(folder, "current.txt")
np.savetxt(output_file, current_with_axis, fmt="%.18e")
print(f"\n✅ Current matrix with axes saved as '{output_file}'.")

# === Create color heatmap ===
plt.figure(figsize=(6, 5))
im = plt.imshow(current, cmap="viridis", aspect="auto", extent=[x_values[0], x_values[-1], y_values[-1], y_values[0]])
plt.colorbar(im, label="Current (A)")
plt.title("Calculated Current Matrix")
plt.xlabel("X (units)")
plt.ylabel("Y (units)")
plt.tight_layout()

# === Save plot ===
plot_file = os.path.join(folder, "current_heatmap.png")
plt.savefig(plot_file, dpi=300)
plt.close()
print(f"✅ Color heatmap saved as '{plot_file}'.")

