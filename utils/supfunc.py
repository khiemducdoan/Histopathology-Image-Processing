import os
import sys
import logging 
import time 
import numpy as np
import matplotlib.pyplot as plt 
from PIL import Image 
import tifffile as tiff 
import pandas as pd 
import gc 
import math 
import cv2
import seaborn as sns

from tqdm import tqdm
import openslide
from openslide import open_slide 
from openslide.deepzoom import DeepZoomGenerator


def rescale_wsi(slide, scale_factor):
    dims = slide.level_dimensions[0]
    large_w, large_h = slide.dimensions
    new_w = math.floor(large_w/scale_factor)
    new_h = math.floor(large_h/scale_factor)
    wsi = slide.read_region((0,0),0, dims) 
    wsi = wsi.convert("RGB")
    rescale_img = wsi.resize((new_w, new_h), Image.Resampling.BILINEAR)
    return rescale_img 
def create_property_df(slide):
    slide_properties = slide.properties 
    descriptions =  ['The number of levels in the slide. Levels are numbered from 0 (highest resolution) to level_count - 1 (lowest resolution)',
                    'A list of downsample factors for each level of the slide. level_downsamples[k] is the downsample factor of level k',
                    'Height at level k',
                    'Tile height at level k',
                    'Tile width at level k',
                    'Width at level k',
                    'The name of the property containing an identification of the vendor',
                    'Resolution Unit of the slide',
                    'X Resolution',
                    'Y Resolution',
                    'A (width, height) tuple for level 0 of the slide',
                    'Image mode/attribute'
                   ]
    properties = {}
    smaller_region = slide.read_region((slide.dimensions[0]//2,slide.dimensions[1]//2), 0, (1024,1024))
    for key, value in slide_properties.items():
        properties[key] = value
    properties["slide-dimension"] = slide.dimensions # widthxheight
    properties['image-mode'] = smaller_region.mode
    df_properties = pd.DataFrame.from_dict(properties, orient='index').reset_index() #orient index is to create the df using dict keys as rows
    df_properties.columns = ['Slide Property', 'Value']
    df_properties['Description'] = descriptions
    df_properties = df_properties[['Slide Property','Description','Value']]
    return df_properties

def visualize_slide(df, loc, img):
    plt.figure(figsize=(30,10))
    plt.imshow(img)
    plt.title(f'Label: {df.loc[loc].label}\nImage ID: {df.loc[loc].image_id}\nCenter ID: {df.loc[loc].center_id}\nImage shape: {img.size}')
    plt.show()
    
def highlight(row):
    df = lambda x: ['background: #8DE7E3' if x.name in row
                    else '' for i in x]
    return df

def thresholding(img, method='otsu'):
    # convert to grayscale complement image
    grayscale_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_c = 255 - grayscale_img
    thres, thres_img = 0, img_c.copy()
    if method == 'otsu':
        thres, thres_img = cv2.threshold(img_c, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    elif method == 'triangle':
        thres, thres_img = cv2.threshold(img_c, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_TRIANGLE)
    return thres, thres_img, img_c

def histogram(img, thres_img, img_c, thres):
    """
    style: ['color', 'grayscale']
    """ 
    plt.figure(figsize=(15,15))
    
    plt.subplot(3,2,1)
    plt.imshow(img)
    plt.title('Scaled-down image')
    
    plt.subplot(3,2,2)
    sns.histplot(img.ravel(), bins=np.arange(0,256), color='orange', alpha=0.5)
    sns.histplot(img[:,:,0].ravel(), bins=np.arange(0,256), color='red', alpha=0.5)
    sns.histplot(img[:,:,1].ravel(), bins=np.arange(0,256), color='Green', alpha=0.5)
    sns.histplot(img[:,:,2].ravel(), bins=np.arange(0,256), color='Blue', alpha=0.5)
    plt.legend(['Total', 'Red_Channel', 'Green_Channel', 'Blue_Channel'])
    plt.ylim(0,0.05e6)
    plt.xlabel('Intensity value')
    plt.title('Color histogram')
    
    plt.subplot(3,2,3)
    plt.imshow(img_c, cmap='gist_gray')
    plt.title('Complement grayscale image')
    
    plt.subplot(3,2,4)
    sns.histplot(img_c.ravel(), bins=np.arange(0,256))
    plt.axvline(thres, c='red', linestyle="--")
    plt.ylim(0,0.05e6)
    plt.xlabel('Intensity value')
    plt.title('Grayscale complement histogram')
    
    plt.subplot(3,2,5)
    plt.imshow(thres_img, cmap='gist_gray')
    plt.title('Thresholded image')
    
    plt.subplot(3,2,6)
    sns.histplot(thres_img.ravel(), bins=np.arange(0,256))
    plt.axvline(thres, c='red', linestyle="--")
    plt.ylim(0,0.05e6)
    plt.xlabel('Intensity value')
    plt.title('Thresholded histogram')
    
    plt.tight_layout()
    plt.show()
def is_tissue(patch, tissue_method="otsu", tissue_threshold=0.1):
    gray = cv2.cvtColor(patch, cv2.COLOR_RGB2GRAY)
    
    # Invert: tissue becomes bright, background dark
    gray_inv = 255 - gray
    
    if tissue_method == "otsu":
        _, thres_img = cv2.threshold(gray_inv, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    elif tissue_method == "triangle":
        _, thres_img = cv2.threshold(gray_inv, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_TRIANGLE)
    else:
        raise ValueError(f"Method {tissue_method} not recognized")
    
    tissue_ratio = np.mean(gray == 255)  # Now this is ACTUAL tissue
    return tissue_ratio >= tissue_threshold
def tiling(
        wsi_path,
        output_dir,
        patch_size = 512,
        stride = None,
        level = 0,
        tissue_method = "otsu",
        tissue_threshold = 0.5,
        save_format = "npy",
        verbose = True
):
    if stride is None:
        stride = patch_size
    os.makedirs(output_dir, exist_ok=True)
    slide = openslide.OpenSlide(wsi_path)
    w, h = slide.dimensions 

    if verbose:
        print(f"WSI dimensions: {slide.dimensions}, level dimensions: {slide.level_dimensions}, level downsample factors: {slide.level_downsamples}")
        print(f"Tiling WSI into patches of size {patch_size}x{patch_size} at level {level} with stride {stride}")   
    saved_patches = []
    patch_count = 0
    total_patches = ((h - patch_size) // stride + 1) * ((w - patch_size) // stride + 1)

    pbar = tqdm(total = total_patches, desc = "Extracting patches", disable = not verbose)
    for y in range(0, h-patch_size, stride):
        for x in range(0, w-patch_size, stride):
            patch = np.array(slide.read_region((x,y), level, (patch_size, patch_size)))[:,:,:3]

            if not is_tissue(patch, tissue_method= tissue_method, tissue_threshold = tissue_threshold):
                pbar.update(1)
                continue

            patch_name = f"{os.path.basename(wsi_path).replace('.tif', '')}_x{x}_y{y}.{save_format}"
            patch_path = os.path.join(output_dir, patch_name)

            if save_format == "npy":
                np.save(patch_path, patch)
            elif save_format == "png":
                Image.fromarray(patch).save(patch_path)
            else:
                raise ValueError(f"Save format {save_format} not recognized. Use 'npy' or 'png'.")
            
            saved_patches.append(patch_path)
            patch_count += 1
            pbar.update(1)
    pbar.close()
    slide.close()
    if verbose:
        print(f"Saved {patch_count} patches to {output_dir}")
    return saved_patches