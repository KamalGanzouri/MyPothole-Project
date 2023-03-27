from io import BytesIO

import numpy as np
from PIL import Image
from fastapi import FastAPI, UploadFile, HTTPException
import firebase_admin
from firebase_admin import credentials, firestore
from ultralytics import YOLO

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
database = firestore.client()

model = YOLO('Model.pt')

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/detect")
async def detect(img: bytes, lat: float, long: float):

    location = firestore.GeoPoint(lat, long)
    docs = database.collection('pothole').where("location", "==", location).get()
    if docs:
        return "Already Saved"

    '''if img.filename.split(".")[-1] in ("jpg", "jpeg", "png"):
        pass
    else:
        raise HTTPException(status_code=415, detail="wrong format")'''

    image = Image.open(BytesIO(img))
    image = np.array(image)
    result = model(image)

    pothole_type = ""

    for r in result:
        for c in r.boxes.cls:
            pothole_type = model.names[int(c)]
            if pothole_type == "Dangerous":
                break

    if pothole_type in ("Bad", "Dangerous"):
        database.collection('pothole').add({'user_id': "NotDefinedYet", 'type': pothole_type, 'location': location,
                                            'fixed': False, 'employee_id': "NotDefinedYet"})
        return 'Detected'
    else:
        return 'No Detection'


@app.get("/location")
async def locations():
    docs = database.collection('pothole').where("fixed", "==", False).stream()
    location = []
    for doc in docs:
        doc = doc.to_dict()

        location_and_type = {'latitude': doc.get('location').latitude, 'longitude': doc.get('location').longitude,
                             'type': doc.get('type')}
        location.append(location_and_type)
    return location


@app.get("/location/bad")
async def bad_locations():
    docs = database.collection("pothole").where("fixed", "==", False).where("type", "==", "Bad").stream()
    location = []
    for doc in docs:
        doc = doc.to_dict()
        location_only = {'latitude': doc.get('location').latitude, 'longitude': doc.get('location').longitude}
        location.append(location_only)
    return location


@app.get("/location/dangerous")
async def dangerous_locations():
    docs = database.collection("pothole").where("fixed", "==", False).where("type", "==", "Dangerous").stream()
    location = []
    for doc in docs:
        doc = doc.to_dict()
        location_only = {'latitude': doc.get('location').latitude, 'longitude': doc.get('location').longitude}
        location.append(location_only)
    return location


@app.put("/pothole-fixed")
async def pothole_fix(lat: float, long: float, employee_id: str):
    location = firestore.GeoPoint(lat, long)
    docs = database.collection('pothole').where("location", "==", location).get()
    for doc in docs:
        database.collection('pothole').document(doc.id).update({'fixed': True, 'employee_id': employee_id})
    return "Pothole marked as fixed"
