import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
database = firestore.client()
location = firestore.GeoPoint(90, 90)

docs = database.collection('pothole').stream()
print(docs)

location = []

for doc in docs:
    doc = doc.to_dict()
    location.append(([doc.get('location').latitude, doc.get('location').longitude], doc.get('type')))

print(location)
