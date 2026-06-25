# create_data_yaml.py
import os
import kagglehub
import shutil
import glob

# Get dataset path
dataset_path = kagglehub.dataset_download("mugheesahmad/sh17-dataset-for-ppe-detection")
print(f"📂 Dataset location: {dataset_path}")

# Read train/val splits
with open(os.path.join(dataset_path, "train_files.txt"), "r") as f:
    train_files = [line.strip() for line in f.readlines()]

with open(os.path.join(dataset_path, "val_files.txt"), "r") as f:
    val_files = [line.strip() for line in f.readlines()]

print(f"📊 Train files: {len(train_files)}")
print(f"📊 Val files: {len(val_files)}")

# Create YOLO dataset structure
output_dir = "data/ppe_dataset"
os.makedirs(output_dir, exist_ok=True)
os.makedirs(os.path.join(output_dir, "train", "images"), exist_ok=True)
os.makedirs(os.path.join(output_dir, "train", "labels"), exist_ok=True)
os.makedirs(os.path.join(output_dir, "val", "images"), exist_ok=True)
os.makedirs(os.path.join(output_dir, "val", "labels"), exist_ok=True)

# Helper function to find and copy files
def copy_files(file_list, dest_images, dest_labels, source_images, source_labels):
    for short_name in file_list:
        # The actual image file might have different extensions or naming
        # Try to find a file that starts with the short name
        found = False
        for ext in ['.jpg', '.jpeg', '.png', '.JPG']:
            # Check if the file exists with this extension
            src_img = os.path.join(source_images, short_name + ext)
            if os.path.exists(src_img):
                shutil.copy2(src_img, dest_images)
                # Copy corresponding label
                src_label = os.path.join(source_labels, short_name + '.txt')
                if os.path.exists(src_label):
                    shutil.copy2(src_label, dest_labels)
                found = True
                break
        
        if not found:
            # Try to find a file that starts with the short name (in case of extra characters)
            pattern = os.path.join(source_images, short_name + '*')
            matches = glob.glob(pattern)
            if matches:
                src_img = matches[0]  # Take the first match
                shutil.copy2(src_img, dest_images)
                # Copy corresponding label
                src_label = os.path.join(source_labels, os.path.basename(src_img).replace('.jpg', '.txt').replace('.jpeg', '.txt').replace('.png', '.txt'))
                if os.path.exists(src_label):
                    shutil.copy2(src_label, dest_labels)
                found = True
        
        if not found:
            print(f"⚠️ Warning: Could not find file for {short_name}")

# Copy training files
print("📂 Copying training files...")
copy_files(
    train_files,
    os.path.join(output_dir, "train", "images"),
    os.path.join(output_dir, "train", "labels"),
    os.path.join(dataset_path, "images"),
    os.path.join(dataset_path, "labels")
)

# Copy validation files
print("📂 Copying validation files...")
copy_files(
    val_files,
    os.path.join(output_dir, "val", "images"),
    os.path.join(output_dir, "val", "labels"),
    os.path.join(dataset_path, "images"),
    os.path.join(dataset_path, "labels")
)

# Create data.yaml
class_names = [
    'Hard hat', 'Safety vest', 'Gloves', 'Safety glasses', 'Hearing protection',
    'High visibility', 'Safety shoes', 'Full body suit', 'Respirator', 'Face shield',
    'Goggles', 'Welding helmet', 'Earplugs', 'Harness', 'Lanyard', 'Tool lanyard',
    'Knee pads'
]

yaml_content = f"""
# SH17 Dataset for PPE Detection
train: train/images
val: val/images

nc: 17
names: {class_names}
"""

with open(os.path.join(output_dir, "data.yaml"), "w") as f:
    f.write(yaml_content)

print(f"✅ data.yaml created at: {os.path.join(output_dir, 'data.yaml')}")
print("🎉 Dataset is ready for training!")

# Verify the files were copied
train_img_count = len(os.listdir(os.path.join(output_dir, "train", "images")))
val_img_count = len(os.listdir(os.path.join(output_dir, "val", "images")))
print(f"📊 Training images: {train_img_count}")
print(f"📊 Validation images: {val_img_count}")