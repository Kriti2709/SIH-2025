from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime

MONGODB_CONN = "mongodb+srv://testuser:testpass@your-cluster.mongodb.net/iotdata?retryWrites=true&w=majority"

client = MongoClient(MONGODB_CONN)
db = client["iotdata"]
coll = db["readings"]

app = Flask(__name__)
CORS(app)

# Endpoint for devices (or test script) to POST data


@app.route('/api/sensor', methods=['POST'])
def post_sensor():
    data = request.json
    data['timestamp'] = datetime.utcnow().isoformat()
    # Basic fault detection! (move to server-side processing)
    prob = 0
    if data['voltage'] < 210:
        prob += 0.4
    if data['current'] < 7:
        prob += 0.3
    if data['accel'] > 1.0:
        prob += 0.3
    if prob > 1:
        prob = 1
    data['fault_probability'] = round(prob, 2)
    data['status'] = "FAULT_DETECTED" if prob > 0.5 else "NORMAL"
    coll.insert_one(data)
    return {"ok": True}, 201

# Endpoint for dashboard frontend


@app.route('/api/data')
def get_data():
    readings = list(coll.find().sort("timestamp", -1).limit(20))
    # .find() returns ObjectId, convert to string or remove
    for r in readings:
        r.pop('_id', None)
    return jsonify(readings[::-1])


if __name__ == "__main__":
    app.run(host="0.0.0.0")
