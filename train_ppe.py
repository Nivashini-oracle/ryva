# train_ppe.py
from ultralytics import YOLO
import os

# Use the direct path file
data_yaml = "data_direct.yaml"

if not os.path.exists(data_yaml):
    print(f"❌ Error: {data_yaml} not found!")
    exit(1)

print(f"✅ Using dataset config: {data_yaml}")

# Load pretrained model
model = YOLO('yolov8n.pt')

# Train
print("🚀 Starting training... (this will take 1-2 hours)")
model.train(
    data=data_yaml,
    epochs=30,
    imgsz=416,
    batch=8,
    device='cpu',
    workers=2,
    patience=10,
    cache=False,
    project='ppe_model',
    name='yolov8n_ppe',
    exist_ok=True
)

# Validate
print("📊 Validating...")
results = model.val()
print(f"✅ mAP@50: {results.box.map50:.4f}")

# Export
print("📦 Exporting to ONNX...")
model.export(format='onnx', imgsz=416)
print("✅ Done! Model saved to: ppe_model/yolov8n_ppe/weights/")