#!/bin/bash

set -e

# === Cấu hình ===
DATA_DIR="camelyon17_mil_small"
PATIENTS=("000" "001" "002" "003" "004" "005")

# Tạo thư mục
mkdir -p "$DATA_DIR/images"
mkdir -p "$DATA_DIR/annotations"
mkdir -p "$DATA_DIR/masks"
mkdir -p "$DATA_DIR/evaluation"

# === Phần 1: Tải từ S3 (images + stages.csv) ===
BUCKET="s3://camelyon-dataset"
echo "📥 Downloading stages.csv from S3..."
aws s3 cp --no-sign-request "$BUCKET/CAMELYON17/stages.csv" "$DATA_DIR/"

echo "📥 Downloading 6 patients (30 slides) from S3..."
for p in "${PATIENTS[@]}"; do
    for n in {0..4}; do
        filename="patient_${p}_node_${n}.tif"
        s3_path="$BUCKET/CAMELYON17/images/$filename"
        local_path="$DATA_DIR/images/$filename"
        if [ ! -f "$local_path" ]; then
            echo "  → $filename"
            aws s3 cp --no-sign-request "$s3_path" "$local_path"
        else
            echo "  → $filename (already exists)"
        fi
    done
done

# === Phần 2: Tải từ Zenodo (annotations + masks) ===
ZENODO_BASE="https://zenodo.org/record/5649987/files"

echo -e "\n📥 Downloading annotations from Zenodo..."
for p in "${PATIENTS[@]}"; do
    for n in {0..4}; do
        filename="patient_${p}_node_${n}.xml"
        url="$ZENODO_BASE/annotations/$filename?download=1"
        local_path="$DATA_DIR/annotations/$filename"
        if [ ! -f "$local_path" ]; then
            echo "  → $filename"
            wget -q --show-progress -O "$local_path" "$url" || echo "    ⚠️ Failed (may not exist for negative cases)"
        else
            echo "  → $filename (already exists)"
        fi
    done
done

echo -e "\n📥 Downloading masks from Zenodo..."
for p in "${PATIENTS[@]}"; do
    for n in {0..4}; do
        filename="patient_${p}_node_${n}_mask.tif"
        url="$ZENODO_BASE/masks/$filename?download=1"
        local_path="$DATA_DIR/masks/$filename"
        if [ ! -f "$local_path" ]; then
            echo "  → $filename"
            wget -q --show-progress -O "$local_path" "$url" || echo "    ⚠️ Failed (may not exist for negative cases)"
        else
            echo "  → $filename (already exists)"
        fi
    done
done

# === Phần 3: Tải evaluation folder (optional) ===
echo -e "\n📥 Downloading evaluation folder (if needed)..."
# Danh sách file trong evaluation (theo dataset chính)
EVAL_FILES=("center_submission.csv" "example_submission.csv" "README.txt")

for file in "${EVAL_FILES[@]}"; do
    url="$ZENODO_BASE/evaluation/$file?download=1"
    local_path="$DATA_DIR/evaluation/$file"
    if [ ! -f "$local_path" ]; then
        echo "  → $file"
        wget -q --show-progress -O "$local_path" "$url" || echo "    ⚠️ Failed"
    else
        echo "  → $file (already exists)"
    fi
done

# === Hoàn tất ===
echo -e "\n✅ Done!"
echo "📁 Data structure:"
echo "   $DATA_DIR/"
echo "   ├── images/          # 30 WSI (.tif)"
echo "   ├── annotations/     # 30 XML (có thể thiếu ở bệnh nhân âm tính)"
echo "   ├── masks/           # 30 mask (.tif) (có thể thiếu ở bệnh nhân âm tính)"
echo "   ├── evaluation/      # file đánh giá"
echo "   └── stages.csv       # slide-level labels"
echo ""
echo "💡 Lưu ý: Bệnh nhân âm tính (000,002,004) thường KHÔNG có XML/mask!"