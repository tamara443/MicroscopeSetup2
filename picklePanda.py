import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt

x_r = 5
y_r = 5

spectrum_image_map = np.zeros((2068, x_r, y_r), dtype=float)

slice_index = 1000  # You can change this to any valid index within the range (0, 2068)

# Visualize the 2D slice
plt.imshow(spectrum_image_map[slice_index, :, :], cmap='viridis')
plt.title(f'Slice at index {slice_index}')
plt.xlabel('X Range')
plt.ylabel('Y Range')
plt.colorbar(label='Intensity')
plt.show()

