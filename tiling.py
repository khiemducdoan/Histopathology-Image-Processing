from utils.supfunc import tiling
patches = tiling(
    wsi_path="camelyon17_mil_small/images/patient_000_node_0.tif",
    output_dir="test_patches",
    patch_size=256,
    verbose=True
)
print("Result:", patches)