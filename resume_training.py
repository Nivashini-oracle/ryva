# resume_training_alt.py
from ultralytics import YOLO

# Load the partially trained model
model = YOLO('ppe_model/yolov8n_ppe/weights/last.pt')

# Resume training with fresh settings
model.train(
    data='data_direct.yaml',
    epochs=30,
    imgsz=416,
    batch=8,
    device='cpu',
    workers=2,
    resume=True,
    project='ppe_model',
    name='yolov8n_ppe_resumed',
    exist_ok=True
)