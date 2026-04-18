# server.py
import os
import glob
import time
import schedule
import subprocess
import threading
from datetime import datetime, timedelta
from flask import Flask, jsonify

app = Flask(__name__)

@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

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

@app.route('/top-liste')
def top_liste():
    with open(os.path.join(os.path.dirname(__file__), 'top-liste.html'), encoding='utf-8') as f:
        return f.read()

@app.route('/top-liste.js')
def top_liste_js():
    from flask import Response
    with open(os.path.join(os.path.dirname(__file__), 'top-liste.js'), encoding='utf-8') as f:
        return Response(f.read(), mimetype='application/javascript')


def _ts(days_ago=0, hours_ago=0):
    return (datetime.now() - timedelta(days=days_ago, hours=hours_ago)).strftime('%Y-%m-%dT%H:%M:%S')


@app.route('/api/fideri')
def api_fideri():
    return jsonify([
        {"id": 1, "id_oznaka": "F33-01", "naziv": "Fider 33kV – Novi Beograd",    "telefon": "+381 11 234 5601", "vreme_dolaska": _ts(0,1),  "opterecenje_pct": 87, "snaga_kw": 2800, "struja_a": 490, "napon_v": "33 kV", "status": "Alarm",       "duzina_km": 14.2, "tip_provodnika": "ACSR 240", "zona": "Novi Beograd"},
        {"id": 2, "id_oznaka": "F33-02", "naziv": "Fider 33kV – Zemun",           "telefon": "+381 11 234 5602", "vreme_dolaska": _ts(0,3),  "opterecenje_pct": 62, "snaga_kw": 1950, "struja_a": 340, "napon_v": "33 kV", "status": "Aktivan",     "duzina_km": 10.8, "tip_provodnika": "ACSR 185", "zona": "Zemun"},
        {"id": 3, "id_oznaka": "F33-03", "naziv": "Fider 33kV – Palilula",        "telefon": "+381 11 234 5603", "vreme_dolaska": _ts(0,5),  "opterecenje_pct": 74, "snaga_kw": 2300, "struja_a": 402, "napon_v": "33 kV", "status": "Upozorenje",  "duzina_km": 12.1, "tip_provodnika": "ACSR 240", "zona": "Palilula"},
        {"id": 4, "id_oznaka": "F33-04", "naziv": "Fider 33kV – Voždovac",        "telefon": "+381 11 234 5604", "vreme_dolaska": _ts(1,0),  "opterecenje_pct": 45, "snaga_kw": 1420, "struja_a": 248, "napon_v": "33 kV", "status": "Aktivan",     "duzina_km": 9.5,  "tip_provodnika": "ACSR 150", "zona": "Voždovac"},
        {"id": 5, "id_oznaka": "F33-05", "naziv": "Fider 33kV – Rakovica",        "telefon": "+381 11 234 5605", "vreme_dolaska": _ts(1,4),  "opterecenje_pct": 91, "snaga_kw": 3100, "struja_a": 541, "napon_v": "33 kV", "status": "Alarm",       "duzina_km": 11.3, "tip_provodnika": "ACSR 300", "zona": "Rakovica"},
        {"id": 6, "id_oznaka": "F33-06", "naziv": "Fider 33kV – Čukarica",        "telefon": "+381 11 234 5606", "vreme_dolaska": _ts(2,0),  "opterecenje_pct": 38, "snaga_kw": 1200, "struja_a": 209, "napon_v": "33 kV", "status": "Aktivan",     "duzina_km": 8.7,  "tip_provodnika": "ACSR 120", "zona": "Čukarica"},
        {"id": 7, "id_oznaka": "F33-07", "naziv": "Fider 33kV – Grocka",          "telefon": "+381 11 234 5607", "vreme_dolaska": _ts(2,6),  "opterecenje_pct": 55, "snaga_kw": 1750, "struja_a": 305, "napon_v": "33 kV", "status": "Aktivan",     "duzina_km": 18.4, "tip_provodnika": "ACSR 185", "zona": "Grocka"},
        {"id": 8, "id_oznaka": "F33-08", "naziv": "Fider 33kV – Surčin",          "telefon": "+381 11 234 5608", "vreme_dolaska": _ts(3,0),  "opterecenje_pct": 69, "snaga_kw": 2150, "struja_a": 375, "napon_v": "33 kV", "status": "Upozorenje",  "duzina_km": 15.6, "tip_provodnika": "ACSR 240", "zona": "Surčin"},
    ])


@app.route('/api/provodnici')
def api_provodnici():
    return jsonify([
        {"id": 101, "id_oznaka": "PRV-001", "naziv": "Provodnik ACSR 240 – Segment A1",  "telefon": "+381 11 345 1001", "vreme_dolaska": _ts(0,2),  "opterecenje_pct": 78, "snaga_kw": 2450, "struja_a": 428, "napon_v": "10 kV", "status": "Upozorenje",  "duzina_km": 6.2, "tip_provodnika": "ACSR 240", "zona": "Sektor Sever"},
        {"id": 102, "id_oznaka": "PRV-002", "naziv": "Provodnik ACSR 185 – Segment B2",  "telefon": "+381 11 345 1002", "vreme_dolaska": _ts(0,4),  "opterecenje_pct": 42, "snaga_kw": 1320, "struja_a": 230, "napon_v": "10 kV", "status": "Aktivan",     "duzina_km": 4.8, "tip_provodnika": "ACSR 185", "zona": "Sektor Jug"},
        {"id": 103, "id_oznaka": "PRV-003", "naziv": "Provodnik ACSR 300 – Segment C3",  "telefon": "+381 11 345 1003", "vreme_dolaska": _ts(0,8),  "opterecenje_pct": 93, "snaga_kw": 3200, "struja_a": 558, "napon_v": "10 kV", "status": "Alarm",       "duzina_km": 7.5, "tip_provodnika": "ACSR 300", "zona": "Industrijska zona"},
        {"id": 104, "id_oznaka": "PRV-004", "naziv": "Provodnik ACSR 120 – Segment D4",  "telefon": "+381 11 345 1004", "vreme_dolaska": _ts(1,2),  "opterecenje_pct": 31, "snaga_kw":  980, "struja_a": 171, "napon_v": "10 kV", "status": "Aktivan",     "duzina_km": 3.9, "tip_provodnika": "ACSR 120", "zona": "Stambena zona"},
        {"id": 105, "id_oznaka": "PRV-005", "naziv": "Provodnik ACSR 240 – Segment E5",  "telefon": "+381 11 345 1005", "vreme_dolaska": _ts(1,7),  "opterecenje_pct": 65, "snaga_kw": 2050, "struja_a": 358, "napon_v": "10 kV", "status": "Aktivan",     "duzina_km": 5.6, "tip_provodnika": "ACSR 240", "zona": "Sektor Istok"},
        {"id": 106, "id_oznaka": "PRV-006", "naziv": "Provodnik ACSR 150 – Segment F6",  "telefon": "+381 11 345 1006", "vreme_dolaska": _ts(2,3),  "opterecenje_pct": 57, "snaga_kw": 1800, "struja_a": 314, "napon_v": "10 kV", "status": "Aktivan",     "duzina_km": 4.3, "tip_provodnika": "ACSR 150", "zona": "Sektor Zapad"},
    ])


@app.route('/api/potrosaci')
def api_potrosaci():
    return jsonify([
        {"id": 201, "id_oznaka": "POT-001", "naziv": "Fabrika Metalac d.o.o.",        "telefon": "+381 11 456 2001", "vreme_dolaska": _ts(0,0),  "opterecenje_pct": 95, "snaga_kw": 3800, "struja_a": 663, "napon_v": "10 kV", "status": "Alarm",    "br_brojila": "1234567", "fider": "F33-05", "adresa": "Industrijska 12, Rakovica"},
        {"id": 202, "id_oznaka": "POT-002", "naziv": "Hladnjača Frigo-Beograd",       "telefon": "+381 11 456 2002", "vreme_dolaska": _ts(0,1),  "opterecenje_pct": 82, "snaga_kw": 2600, "struja_a": 454, "napon_v": "10 kV", "status": "Alarm",    "br_brojila": "2345678", "fider": "F33-01", "adresa": "Bulevar Mihajla Pupina 6, NB"},
        {"id": 203, "id_oznaka": "POT-003", "naziv": "Tržni centar Arena",            "telefon": "+381 11 456 2003", "vreme_dolaska": _ts(0,3),  "opterecenje_pct": 71, "snaga_kw": 2250, "struja_a": 393, "napon_v": "10 kV", "status": "Upozorenje","br_brojila": "3456789", "fider": "F33-02", "adresa": "Palmira Toljatija 1, Zemun"},
        {"id": 204, "id_oznaka": "POT-004", "naziv": "Bolnica Dragisa Misovic",       "telefon": "+381 11 456 2004", "vreme_dolaska": _ts(0,5),  "opterecenje_pct": 58, "snaga_kw": 1840, "struja_a": 321, "napon_v": "10 kV", "status": "Aktivan",  "br_brojila": "4567890", "fider": "F33-04", "adresa": "Heroja Milana Tepića 1, Voždovac"},
        {"id": 205, "id_oznaka": "POT-005", "naziv": "Aerodrom Nikola Tesla",         "telefon": "+381 11 456 2005", "vreme_dolaska": _ts(0,6),  "opterecenje_pct": 76, "snaga_kw": 2420, "struja_a": 422, "napon_v": "10 kV", "status": "Upozorenje","br_brojila": "5678901", "fider": "F33-08", "adresa": "11070 Surčin"},
        {"id": 206, "id_oznaka": "POT-006", "naziv": "Pivara Beograd",                "telefon": "+381 11 456 2006", "vreme_dolaska": _ts(1,1),  "opterecenje_pct": 49, "snaga_kw": 1560, "struja_a": 272, "napon_v": "10 kV", "status": "Aktivan",  "br_brojila": "6789012", "fider": "F33-03", "adresa": "Carine 2, Palilula"},
        {"id": 207, "id_oznaka": "POT-007", "naziv": "Hotel Metropol Palace",         "telefon": "+381 11 456 2007", "vreme_dolaska": _ts(1,4),  "opterecenje_pct": 43, "snaga_kw": 1370, "struja_a": 239, "napon_v": "10 kV", "status": "Aktivan",  "br_boyfriila": "7890123", "fider": "F33-01", "adresa": "Bulevar kralja Aleksandra 69"},
        {"id": 208, "id_oznaka": "POT-008", "naziv": "Štamparija Politika",           "telefon": "+381 11 456 2008", "vreme_dolaska": _ts(2,0),  "opterecenje_pct": 36, "snaga_kw": 1140, "struja_a": 199, "napon_v": "10 kV", "status": "Aktivan",  "br_brojila": "8901234", "fider": "F33-06", "adresa": "Makedonska 29, Centar"},
    ])


if __name__ == '__main__':
    app.run(debug=False, port=5000)