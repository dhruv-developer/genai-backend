from pymongo import MongoClient

client = MongoClient("mongodb+srv://dhruvdawar11022006_db_user:gSbiZCRvqSl6klu7@cluster0.d933uzd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["grant_risk_db"]  # replace with your DB name

doc = db.features.find_one({"grant_id": "G123"})
print(doc)
