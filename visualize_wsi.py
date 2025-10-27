import os
from openslide import OpenSlide
import matplotlib.pyplot as plt 
import numpy as np 

import cv2 as cv
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
assert thumbnail_np is not None, "file could not be read, check with os.path.exists()"
 
thumbnail_gray = cv.cvtColor(thumbnail_np, cv.COLOR_RGB2GRAY)

# Global thresholding
ret1, th1 = cv.threshold(thumbnail_gray, 127, 255, cv.THRESH_BINARY)

# Otsu's thresholding
ret2, th2 = cv.threshold(thumbnail_gray, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)

# Otsu's after Gaussian blur
blur = cv.GaussianBlur(thumbnail_gray, (5, 5), 0)
ret3, th3 = cv.threshold(blur, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)
 
# plot all the images and their histograms
images = [thumbnail_np, thumbnail_gray, th1,
          thumbnail_np, thumbnail_gray, th2,
          thumbnail_np, blur, th3]

titles = ['Original Image', 'Grayscale', 'Global Thresholding (v=127)',
          'Original Image', 'Grayscale', "Otsu's Thresholding",
          'Original Image', 'Gaussian Blurred', "Otsu's Thresholding"]
 
for i in range(3):
    plt.subplot(3,3,i*3+1),plt.imshow(images[i*3],'gray')
    plt.title(titles[i*3]), plt.xticks([]), plt.yticks([])
    plt.subplot(3,3,i*3+2),plt.hist(images[i*3].ravel(),256)
    plt.title(titles[i*3+1]), plt.xticks([]), plt.yticks([])
    plt.subplot(3,3,i*3+3),plt.imshow(images[i*3+2],'gray')
    plt.title(titles[i*3+2]), plt.xticks([]), plt.yticks([])
plt.show()
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
