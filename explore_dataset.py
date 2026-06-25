# explore_dataset.py
import os
import kagglehub

# Get the dataset path
dataset_path = kagglehub.dataset_download("mugheesahmad/sh17-dataset-for-ppe-detection")
print(f"📂 Dataset location: {dataset_path}")

# Walk through all files
print("\n📋 Full directory structure:")
for root, dirs, files in os.walk(dataset_path):
    depth = root.replace(dataset_path, "").count(os.sep)
    indent = "  " * depth
    folder_name = os.path.basename(root)
    print(f"{indent}📁 {folder_name}/")
    
    # Show files
    sub_indent = "  " * (depth + 1)
    for file in files[:10]:  # Show first 10 files per folder
        print(f"{sub_indent}📄 {file}")
    
    # If there are more files, indicate
    if len(files) > 10:
        print(f"{sub_indent}... and {len(files) - 10} more files")
    
    print()