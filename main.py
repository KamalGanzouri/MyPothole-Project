from io import BytesIO
import numpy as np
from PIL import Image
from fastapi import FastAPI, File
import firebase_admin
from firebase_admin import credentials, firestore
from ultralytics import YOLO

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
database = firestore.client()

model = YOLO('Model.pt')
model.overrides['conf'] = 0.8

app = FastAPI()


@app.post("/login")
async def login(email: str, password: str):
    docs = database.collection("user").where("email", "==", email).where("password", "==", password)\
                                      .where("type", "==", 'user').get()
    if docs:
        for doc in docs:
            return {'id': doc.id, 'type': 'user'}
    docs = database.collection("user").where("email", "==", email).where("password", "==", password)\
                                      .where("type", "==", 'employee').get()
    if docs:
        for doc in docs:
            return {'id': doc.id, 'type': 'employee'}

    return "Failed"


@app.post("/signup")
async def signup(email: str, password: str, category: str):
    docs = database.collection('user').where("email", "==", email).get()
    if docs:
        return "Already Saved"
    else:
        database.collection('user').add({'email': email, 'password': password, 'type': category})
    return "Success"


@app.post("/detect")
async def detect(lat: float, long: float, user_id: str, img: bytes = File(...)):
    pothole_type = "No Detection"
    location = firestore.GeoPoint(float('%.4f' % lat), float('%.4f' % long))

    docs = database.collection('pothole').where("location", "==", location).get()
    if docs:
        return "Already Saved"
    else:
        image = Image.open(BytesIO(img))
        image = np.array(image)
        result = model(image)

        for r in result:
            for c in r.boxes.cls:
                pothole_type = model.names[int(c)]
                if pothole_type == "Dangerous":
                    break

        if pothole_type in ("Bad", "Dangerous"):
            database.collection('pothole').add({'user_id': user_id, 'type': pothole_type, 'location': location,
                                                'fixed': False, 'employee_id': "NotDefinedYet"})
    return pothole_type


@app.get("/location")
async def locations():
    docs = database.collection('pothole').where("fixed", "==", False).stream()
    location = []
    for doc in docs:
        id = doc.id
        doc = doc.to_dict()

        location_and_type = {'id': id, 'latitude': doc.get('location').latitude,
                             'longitude': doc.get('location').longitude,
                             'type': doc.get('type')}
        location.append(location_and_type)
    return location


@app.get("/location/bad")
async def bad_locations():
    docs = database.collection("pothole").where("fixed", "==", False).where("type", "==", "Bad").stream()
    location = []
    for doc in docs:
        id = doc.id
        doc = doc.to_dict()
        location_only = {'id': id, 'latitude': doc.get('location').latitude,
                         'longitude': doc.get('location').longitude}
        location.append(location_only)
    return location


@app.get("/location/dangerous")
async def dangerous_locations():
    docs = database.collection("pothole").where("fixed", "==", False).where("type", "==", "Dangerous").stream()
    location = []
    for doc in docs:
        id = doc.id
        doc = doc.to_dict()
        location_only = {'id': id, 'latitude': doc.get('location').latitude,
                         'longitude': doc.get('location').longitude}
        location.append(location_only)
    return location


@app.put("/location/fixed")
async def pothole_fix(lat: float, long: float, employee_id: str):
    location = firestore.GeoPoint(lat, long)
    docs = database.collection('pothole').where("location", "==", location).get()
    for doc in docs:
        database.collection('pothole').document(doc.id).update({'fixed': True, 'employee_id': employee_id})
    return "Pothole marked as fixed"
