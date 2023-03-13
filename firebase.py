from ultralytics import YOLO

model = YOLO("C:/Users/kamal/Downloads/best.pt")

model.export(format="tflite")
