from utils.supfunc import tiling
patches = tiling(
    wsi_path="camelyon17_mil_small/images/patient_000_node_0.tif",
    output_dir="test_patches",
    patch_size=224,
    stride=224,
    level=0,
    tissue_method="otsu",
    tissue_threshold=0.3,
    save_format="npy",
    verbose=True
)
print("Result:", patches)