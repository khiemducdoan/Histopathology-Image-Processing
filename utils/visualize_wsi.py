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


thumbnail = slide.get_thumbnail((1024, 1024))
thumbnail_np = np.array(thumbnail)

plt.figure(figsize = (8,8))
plt.imshow(thumbnail_np)
plt.axis('off')
plt.title("WSI Thumbnail (512x512)")
plt.show()

print("extract a high resolution patch from the WSI")

patch = slide.read_region((600,600), 0, (512, 512))
patch_array = np.array(patch)[:,:,:3] #remove alpha channel
plt.figure(figsize = (8,8))
plt.imshow(patch)
plt.axis("off")
plt.title("High resolution patch (512x512) at (10000, 10000)")
plt.show()

slide.close()
