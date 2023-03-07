from io import BytesIO

import numpy as np
from PIL import Image
from fastapi import FastAPI, UploadFile, HTTPException

from ultralytics import YOLO

model = YOLO("Model.pt")

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/detect")
async def detect(img: UploadFile):
    massage = ""
    if img.filename.split(".")[-1] in ("jpg", "jpeg", "png"):
        pass
    else:
        raise HTTPException(status_code=415, detail="wrong format")
    image = Image.open(BytesIO(img.file.read()))
    image = np.array(image)
    result = model(image)
    for r in result:
        for c in r.boxes.cls:
            massage = model.names[int(c)]
    return {"message": massage}
