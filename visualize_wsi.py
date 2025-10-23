import os
from openslide import OpenSlide
import matplotlib.pyplot as plt 
import numpy as np 


wsi_path = "/home/duckhiem/Histopathology-Image-Processing/camelyon17_mil_small/images/patient_000_node_0.tif"


if not os.path.exists(wsi_path):
    raise FileNotFoundError(f"The specified WSI file does not exist: {wsi_path}")

slide = OpenSlide(wsi_path)

# Get dimensions of the WSI
print(f"dimensions of WSI: {slide.dimensions}")
print(f"number of levels: {slide.level_count}")
print(f"level dimensions : {slide.level_dimensions}")
print(f"level downsample factors:  {slide.level_downsamples}")