#!/usr/bin/env python3
import os
import json  # ← ĐÃ THÊM
import pandas as pd
from utils.supfunc import tiling as fast_tiling

DATA_ROOT = "/home/duckhiem/Histopathology-Image-Processing/camelyon17_mil_small"
IMAGES_DIR = os.path.join(DATA_ROOT, "images")
PATCHES_DIR = os.path.join(DATA_ROOT, "patches")
os.makedirs(PATCHES_DIR, exist_ok=True)

stages_path = os.path.join(DATA_ROOT, "stages.csv")
if os.path.exists(stages_path):
    df = pd.read_csv(stages_path)
    print(f"✅ Loaded {len(df)} rows from stages.csv")
    
    
    slide_label_map = {}
    for _, row in df.iterrows():
        filename = row["patient"]
        stage = row["stage"]
        if filename.endswith(".tif"):
            label = 0 if stage == "negative" else 1
            slide_label_map[filename] = label
    print(f"   Mapped {len(slide_label_map)} slides to labels")
else:
    slide_label_map = None

tif_files = [f for f in os.listdir(IMAGES_DIR) if f.endswith(".tif")]
print(f"found {len(tif_files)} .tif files in {IMAGES_DIR}")


all_patch_paths = []
for filename in tif_files:
    print(f"Processing {filename}...")
    wsi_path = os.path.join(IMAGES_DIR, filename)
    slide_name = filename.replace(".tif", "")
    output_dir = os.path.join(PATCHES_DIR, slide_name)
    
    try:
        patch_paths = fast_tiling(
            wsi_path=wsi_path,
            output_dir=output_dir,
            patch_size=256,
            stride=256,
            level=0,
            tissue_method="otsu",
            tissue_threshold=0.01,
            save_format="npy",
            verbose=False
        )
        if patch_paths is None:
            print(f"  ⚠️  No patches extracted for {filename}")
            continue
        print(f"  ✅ Extracted {len(patch_paths)} patches for {filename}")
        all_patch_paths.extend(patch_paths)
    except Exception as e:
        print(f"  ❌ Error processing {filename}: {e}")
        continue


slide_to_patches = {}
for patch_path in all_patch_paths:
    rel_path = os.path.relpath(patch_path, PATCHES_DIR)
    slide_name = rel_path.split("/")[0]
    if slide_name not in slide_to_patches:
        slide_to_patches[slide_name] = []
    slide_to_patches[slide_name].append(patch_path)

dataset_info = []
for slide_name, patch_list in slide_to_patches.items():
    filename = f"{slide_name}.tif"
    label = slide_label_map.get(filename, -1) if slide_label_map else -1
    
    dataset_info.append({
        "slide_name": slide_name,
        "filename": filename,
        "label": label,
        "num_patches": len(patch_list),
        "patch_paths": patch_list
    })

metadata_path = os.path.join(DATA_ROOT, "mil_dataset.json")
with open(metadata_path, "w") as f:
    json.dump(dataset_info, f, indent=2)

print(f"\n🎉 Done! Metadata saved to {metadata_path}")