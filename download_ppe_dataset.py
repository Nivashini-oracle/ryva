# download_ppe_dataset.py
import kagglehub
import os
import shutil

# Download the SH17 dataset
print("📥 Downloading SH17 PPE dataset...")
path = kagglehub.dataset_download("mugheesahmad/sh17-dataset-for-ppe-detection")
print(f"✅ Dataset downloaded to: {path}")

# Optional: Copy to a more convenient location in your project
destination = "data/ppe_dataset"
if not os.path.exists(destination):
    os.makedirs(destination)

print(f"📂 Dataset location: {path}")
print("📋 Files in dataset:")
for root, dirs, files in os.walk(path):
    print(f"  {root}")
    for file in files[:5]:  # Show first 5 files
        print(f"    - {file}")
    break  # Only show top level

print("\n✅ Done! Now find the data.yaml file and update your training script.")