import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
from datetime import datetime

# Supabase configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)
CORS(app)

def detect_fault(voltage, current, accel):
    prob = 0
    if voltage < 210:
        prob += 0.4
    if current < 7:
        prob += 0.3
    if accel > 1.0:
        prob += 0.3
    if prob > 1:
        prob = 1
    return prob > 0.5, round(prob, 2)

@app.route('/api/sensor', methods=['POST'])
def post_sensor():
    data = request.json
    voltage = float(data['voltage'])
    current = float(data['current'])
    accel = float(data['accel'])
    
    fault, fault_prob = detect_fault(voltage, current, accel)
    status = "FAULT_DETECTED" if fault else "NORMAL"
    
    # Insert into Supabase
    result = supabase.table('sensor_readings').insert({
        'voltage': voltage,
        'current': current,
        'accel': accel,
        'fault': fault,
        'fault_prob': fault_prob,
        'status': status
    }).execute()
    
    return {"ok": True, "fault": fault}, 201

@app.route('/api/data')
def get_data():
    result = supabase.table('sensor_readings').select("*").order('id', desc=True).limit(20).execute()
    data = result.data[::-1]  # Reverse to show oldest first
    return jsonify(data)

@app.route('/api/status')
def get_status():
    result = supabase.table('sensor_readings').select("fault,fault_prob").order('id', desc=True).limit(1).execute()
    if result.data:
        return jsonify({'fault': result.data[0]['fault'], 'fault_prob': result.data[0]['fault_prob']})
    return jsonify({'fault': False, 'fault_prob': 0.0})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
