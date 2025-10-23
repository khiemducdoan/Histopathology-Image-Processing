#!/bin/bash

set -e

BUCKET="s3://camelyon-dataset"
DATA_DIR="camelyon17_mil_small"
mkdir -p "$DATA_DIR/images"

# 1. Download labels
echo "📥 Downloading stages.csv..."
aws s3 cp --no-sign-request "$BUCKET/CAMELYON17/stages.csv" "$DATA_DIR/"

# 2. Select 6 patients (3 neg, 3 pos) from center_0
# Verified from stages.csv:
# - patient_000, 002, 004 → label=0 (negative)
# - patient_001, 003, 005 → label=1 (positive)

PATIENTS=("000" "001" "002" "003" "004" "005")

echo "📥 Downloading 6 patients (30 slides)..."

for p in "${PATIENTS[@]}"; do
    for n in {0..4}; do
        filename="patient_${p}_node_${n}.tif"
        s3_path="$BUCKET/CAMELYON17/images/$filename"
        local_path="$DATA_DIR/images/$filename"
        echo "  → $filename"
        aws s3 cp --no-sign-request "$s3_path" "$local_path"
    done
done

echo "✅ Done! Total data: ~18 GB"