# server.py
import os
import glob
import time
import schedule
import subprocess
import threading
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def generate_map():
    print("Generating new map...")
    
    for old_file in glob.glob('map.*'):
        os.remove(old_file)
        print(f"Deleted {old_file}")
    
    subprocess.run(['python', 'visualization.py'])
    print("New map ready!")

def run_scheduler():
    generate_map()
    schedule.every(30).minutes.do(generate_map)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

worker = threading.Thread(target=run_scheduler, daemon=True)
worker.start()

@app.route('/')
def dashboard():
    with open(os.path.join(os.path.dirname(__file__), 'dashboard.html'), encoding='utf-8') as f:
        return f.read()

@app.route('/dashboard.js')
def dashboard_js():
    with open(os.path.join(os.path.dirname(__file__), 'dashboard.js'), encoding='utf-8') as f:
        return f.read(), 200, {'Content-Type': 'application/javascript'}

@app.route('/map')
def map_view():
    files = glob.glob('map.*')
    if not files:
        return "Map not ready yet, please wait...", 503
    with open(files[0], encoding='utf-8', mode='r') as f:
        return f.read()


@app.route('/api/dashboard-data')
def dashboard_data():
    return jsonify({
        "NumActiveMeters": 323,
        "NumDownMeters": 199,
        "NetworkEffectivnessPercentage": 0.73,
    })

if __name__ == '__main__':
    app.run(debug=False, port=5000)