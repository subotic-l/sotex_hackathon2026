# server.py
import os
import glob
import time
import schedule
import subprocess
import threading
from flask import Flask, render_template_string

app = Flask(__name__)

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
    return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head><title>Dashboard</title></head>
        <body>
            <h1>Sotex Dashboard</h1>
            <p>Coming soon...</p>
        </body>
        </html>
    """)

@app.route('/map')
def map_view():
    files = glob.glob('map.*')
    if not files:
        return "Map not ready yet, please wait...", 503
    with open(files[0], 'r') as f:
        return f.read()

if __name__ == '__main__':
    app.run(debug=False, port=5000)