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


# Feeders33 – Visokonaponski vodovi
# Tabela: Feeders33 (Id, Name, TsId, MeterId, NameplateRating)
# + join: Meters (MSN, MultiplierFactor), MeterReadTfes (Val, Ts), Channels (Name, Unit)
@app.route('/api/fideri')
def api_fideri():
    return jsonify([
        {"id": 1, "naziv": "Feeder33 – North Ring",   "ts_id": 10, "meter_id": 1001, "nameplate_rating_kva": 5000,
         "msn": "MSN-F33-001", "multiplier_factor": 1.0,
         "ocitavanje_val": 4350, "ocitavanje_ts": _ts(0,1),  "kanal_naziv": "Aktivna preuzeta energija", "kanal_jedinica": "kWh"},
        {"id": 2, "naziv": "Feeder33 – South Ring",   "ts_id": 10, "meter_id": 1002, "nameplate_rating_kva": 4500,
         "msn": "MSN-F33-002", "multiplier_factor": 1.0,
         "ocitavanje_val": 2790, "ocitavanje_ts": _ts(0,3),  "kanal_naziv": "Aktivna preuzeta energija", "kanal_jedinica": "kWh"},
        {"id": 3, "naziv": "Feeder33 – East Line",    "ts_id": 11, "meter_id": 1003, "nameplate_rating_kva": 6000,
         "msn": "MSN-F33-003", "multiplier_factor": 1.5,
         "ocitavanje_val": 4440, "ocitavanje_ts": _ts(0,5),  "kanal_naziv": "Aktivna preuzeta energija", "kanal_jedinica": "kWh"},
        {"id": 4, "naziv": "Feeder33 – West Line",    "ts_id": 11, "meter_id": 1004, "nameplate_rating_kva": 3500,
         "msn": "MSN-F33-004", "multiplier_factor": 1.0,
         "ocitavanje_val": 1575, "ocitavanje_ts": _ts(1,0),  "kanal_naziv": "Aktivna preuzeta energija", "kanal_jedinica": "kWh"},
        {"id": 5, "naziv": "Feeder33 – Industrial A", "ts_id": 12, "meter_id": 1005, "nameplate_rating_kva": 8000,
         "msn": "MSN-F33-005", "multiplier_factor": 2.0,
         "ocitavanje_val": 7280, "ocitavanje_ts": _ts(1,4),  "kanal_naziv": "Aktivna preuzeta energija", "kanal_jedinica": "kWh"},
        {"id": 6, "naziv": "Feeder33 – Industrial B", "ts_id": 12, "meter_id": 1006, "nameplate_rating_kva": 7000,
         "msn": "MSN-F33-006", "multiplier_factor": 2.0,
         "ocitavanje_val": 2660, "ocitavanje_ts": _ts(2,0),  "kanal_naziv": "Aktivna preuzeta energija", "kanal_jedinica": "kWh"},
        {"id": 7, "naziv": "Feeder33 – Suburban C",   "ts_id": 13, "meter_id": 1007, "nameplate_rating_kva": 4000,
         "msn": "MSN-F33-007", "multiplier_factor": 1.0,
         "ocitavanje_val": 2200, "ocitavanje_ts": _ts(2,6),  "kanal_naziv": "Aktivna preuzeta energija", "kanal_jedinica": "kWh"},
        {"id": 8, "naziv": "Feeder33 – Suburban D",   "ts_id": 13, "meter_id": 1008, "nameplate_rating_kva": 4500,
         "msn": "MSN-F33-008", "multiplier_factor": 1.0,
         "ocitavanje_val": 3105, "ocitavanje_ts": _ts(3,0),  "kanal_naziv": "Aktivna preuzeta energija", "kanal_jedinica": "kWh"},
    ])


# Feeders11 – Srednjenaponski vodovi
# Tabela: Feeders11 (Id, Name, SsId, MeterId, Feeder33Id, NameplateRating, TsId)
# + join: Meters (MSN, MultiplierFactor), MeterReadTfes (Val, Ts), Channels (Name, Unit)
@app.route('/api/provodnici')
def api_provodnici():
    return jsonify([
        {"id": 101, "naziv": "Feeder11 – Segment A1", "ss_id": 201, "meter_id": 2001, "feeder33_id": 3, "ts_id": 11, "nameplate_rating_kva": 1600,
         "msn": "MSN-F11-101", "multiplier_factor": 1.0,
         "ocitavanje_val": 1248, "ocitavanje_ts": _ts(0,2),  "kanal_naziv": "Aktivna preuzeta energija", "kanal_jedinica": "kWh"},
        {"id": 102, "naziv": "Feeder11 – Segment B2", "ss_id": 202, "meter_id": 2002, "feeder33_id": 4, "ts_id": 11, "nameplate_rating_kva": 1000,
         "msn": "MSN-F11-102", "multiplier_factor": 1.0,
         "ocitavanje_val":  420, "ocitavanje_ts": _ts(0,4),  "kanal_naziv": "Aktivna preuzeta energija", "kanal_jedinica": "kWh"},
        {"id": 103, "naziv": "Feeder11 – Segment C3", "ss_id": 203, "meter_id": 2003, "feeder33_id": 5, "ts_id": 12, "nameplate_rating_kva": 2000,
         "msn": "MSN-F11-103", "multiplier_factor": 1.5,
         "ocitavanje_val": 1860, "ocitavanje_ts": _ts(0,8),  "kanal_naziv": "Aktivna preuzeta energija", "kanal_jedinica": "kWh"},
        {"id": 104, "naziv": "Feeder11 – Segment D4", "ss_id": 204, "meter_id": 2004, "feeder33_id": 6, "ts_id": 12, "nameplate_rating_kva":  800,
         "msn": "MSN-F11-104", "multiplier_factor": 1.0,
         "ocitavanje_val":  248, "ocitavanje_ts": _ts(1,2),  "kanal_naziv": "Aktivna preuzeta energija", "kanal_jedinica": "kWh"},
        {"id": 105, "naziv": "Feeder11 – Segment E5", "ss_id": 205, "meter_id": 2005, "feeder33_id": 3, "ts_id": 11, "nameplate_rating_kva": 1600,
         "msn": "MSN-F11-105", "multiplier_factor": 1.0,
         "ocitavanje_val": 1040, "ocitavanje_ts": _ts(1,7),  "kanal_naziv": "Aktivna preuzeta energija", "kanal_jedinica": "kWh"},
        {"id": 106, "naziv": "Feeder11 – Segment F6", "ss_id": 206, "meter_id": 2006, "feeder33_id": 7, "ts_id": 13, "nameplate_rating_kva": 1250,
         "msn": "MSN-F11-106", "multiplier_factor": 1.0,
         "ocitavanje_val":  712, "ocitavanje_ts": _ts(2,3),  "kanal_naziv": "Aktivna preuzeta energija", "kanal_jedinica": "kWh"},
    ])


# Dt – Niskonaponske podstanice
# Tabela: Dt (Id, Name, MeterId, Feeder11Id, Feeder33Id, NameplateRating, Latitude, Longitude)
# + join: Meters (MSN, MultiplierFactor), MeterReadTfes (Val, Ts), Channels (Name, Unit)
@app.route('/api/potrosaci')
def api_potrosaci():
    return jsonify([
        {"id": 301, "naziv": "DT – Blok 45",         "meter_id": 3001, "feeder11_id": 103, "feeder33_id": 5, "nameplate_rating_kva": 630,
         "msn": "MSN-DT-301", "multiplier_factor": 1.0,
         "ocitavanje_val": 598, "ocitavanje_ts": _ts(0,0),  "kanal_naziv": "Aktivna preuzeta energija", "kanal_jedinica": "kWh",
         "latitude": 44.8125, "longitude": 20.4612},
        {"id": 302, "naziv": "DT – Blok 23",         "meter_id": 3002, "feeder11_id": 101, "feeder33_id": 3, "nameplate_rating_kva": 400,
         "msn": "MSN-DT-302", "multiplier_factor": 1.0,
         "ocitavanje_val": 328, "ocitavanje_ts": _ts(0,1),  "kanal_naziv": "Aktivna preuzeta energija", "kanal_jedinica": "kWh",
         "latitude": 44.8201, "longitude": 20.4523},
        {"id": 303, "naziv": "DT – Tržni Centar",    "meter_id": 3003, "feeder11_id": 102, "feeder33_id": 4, "nameplate_rating_kva": 800,
         "msn": "MSN-DT-303", "multiplier_factor": 1.5,
         "ocitavanje_val": 568, "ocitavanje_ts": _ts(0,3),  "kanal_naziv": "Aktivna preuzeta energija", "kanal_jedinica": "kWh",
         "latitude": 44.8334, "longitude": 20.4011},
        {"id": 304, "naziv": "DT – Bolnica",         "meter_id": 3004, "feeder11_id": 104, "feeder33_id": 6, "nameplate_rating_kva": 630,
         "msn": "MSN-DT-304", "multiplier_factor": 1.0,
         "ocitavanje_val": 365, "ocitavanje_ts": _ts(0,5),  "kanal_naziv": "Aktivna preuzeta energija", "kanal_jedinica": "kWh",
         "latitude": 44.7988, "longitude": 20.4789},
        {"id": 305, "naziv": "DT – Aerodrom",        "meter_id": 3005, "feeder11_id": 106, "feeder33_id": 7, "nameplate_rating_kva": 1000,
         "msn": "MSN-DT-305", "multiplier_factor": 2.0,
         "ocitavanje_val": 760, "ocitavanje_ts": _ts(0,6),  "kanal_naziv": "Aktivna preuzeta energija", "kanal_jedinica": "kWh",
         "latitude": 44.8184, "longitude": 20.2917},
        {"id": 306, "naziv": "DT – Pivara",          "meter_id": 3006, "feeder11_id": 105, "feeder33_id": 3, "nameplate_rating_kva": 400,
         "msn": "MSN-DT-306", "multiplier_factor": 1.0,
         "ocitavanje_val": 196, "ocitavanje_ts": _ts(1,1),  "kanal_naziv": "Aktivna preuzeta energija", "kanal_jedinica": "kWh",
         "latitude": 44.8267, "longitude": 20.4699},
        {"id": 307, "naziv": "DT – Hotel zona",      "meter_id": 3007, "feeder11_id": 101, "feeder33_id": 3, "nameplate_rating_kva": 250,
         "msn": "MSN-DT-307", "multiplier_factor": 1.0,
         "ocitavanje_val": 107, "ocitavanje_ts": _ts(1,4),  "kanal_naziv": "Aktivna preuzeta energija", "kanal_jedinica": "kWh",
         "latitude": 44.8145, "longitude": 20.4658},
        {"id": 308, "naziv": "DT – Štamparija",      "meter_id": 3008, "feeder11_id": 104, "feeder33_id": 6, "nameplate_rating_kva": 250,
         "msn": "MSN-DT-308", "multiplier_factor": 1.0,
         "ocitavanje_val":  90, "ocitavanje_ts": _ts(2,0),  "kanal_naziv": "Aktivna preuzeta energija", "kanal_jedinica": "kWh",
         "latitude": 44.8089, "longitude": 20.4831},
    ])


@app.route('/notifikacije')
def notifikacije():
    with open(os.path.join(os.path.dirname(__file__), 'notifikacije.html'), encoding='utf-8') as f:
        return f.read()

@app.route('/notifikacije.js')
def notifikacije_js():
    from flask import Response
    with open(os.path.join(os.path.dirname(__file__), 'notifikacije.js'), encoding='utf-8') as f:
        return Response(f.read(), mimetype='application/javascript')


# Notifikacije – nagla promena potrošnje i gubici
# Podatke ce posle da vuče iz: MeterReadTfes (Val, Ts), Meters (MSN), Feeders11/Feeders33 (Name), Dt (Name)
@app.route('/api/notifikacije')
def api_notifikacije():
    return jsonify([
        # ── ALARMI ──────────────────────────────────────────────────────────────
        {
            "id": 1, "tip": "alarm",
            "naziv": "Nagla promena potrošnje – Feeder33 Industrial A",
            "poruka": "Vrednost očitavanja skočila za 91% u roku od 15 minuta. Verovatno kratko spajanje ili kvar na vodu. Potrebna provera.",
            "vreme": _ts(0, 0),
            "vrednost_pre": 3800, "vrednost_posle": 7280, "promena_pct": 91, "jedinica": "kWh",
            "meter_id": 1005, "msn": "MSN-F33-005", "kanal_naziv": "Aktivna preuzeta energija",
            "feeder_naziv": "Feeder33 – Industrial A", "feeder33_id": 5, "feeder11_id": None, "nameplate_rating_kva": 8000
        },
        {
            "id": 2, "tip": "alarm",
            "naziv": "Prekoračenje nominalne snage – DT Blok 45",
            "poruka": "Podstanica radi na 95% nominalne snage duže od 30 minuta. Rizik od preopterećenja transformatora.",
            "vreme": _ts(0, 1),
            "vrednost_pre": 550, "vrednost_posle": 598, "promena_pct": 8, "jedinica": "kVA",
            "meter_id": 3001, "msn": "MSN-DT-301", "kanal_naziv": "Aktivna preuzeta energija",
            "feeder_naziv": "DT – Blok 45", "feeder33_id": 5, "feeder11_id": 103, "nameplate_rating_kva": 630
        },
        {
            "id": 3, "tip": "alarm",
            "naziv": "Nagli pad potrošnje – Feeder11 Segment C3",
            "poruka": "Potrošnja pala sa 1860 na 420 kWh za 10 minuta. Moguć prekid napajanja ili isklop dela mreže.",
            "vreme": _ts(0, 2),
            "vrednost_pre": 1860, "vrednost_posle": 420, "promena_pct": -77, "jedinica": "kWh",
            "meter_id": 2003, "msn": "MSN-F11-103", "kanal_naziv": "Aktivna preuzeta energija",
            "feeder_naziv": "Feeder11 – Segment C3", "feeder33_id": 5, "feeder11_id": 103, "nameplate_rating_kva": 2000
        },

        # ── UPOZORENJA (nagla promena) ───────────────────────────────────────────
        {
            "id": 4, "tip": "upozorenje",
            "naziv": "Povećana potrošnja – DT Tržni Centar",
            "poruka": "Potrošnja porasla za 34% u poslepodnevnim satima. Vrednost blizu gornje granice alarma.",
            "vreme": _ts(0, 3),
            "vrednost_pre": 423, "vrednost_posle": 568, "promena_pct": 34, "jedinica": "kVA",
            "meter_id": 3003, "msn": "MSN-DT-303", "kanal_naziv": "Aktivna preuzeta energija",
            "feeder_naziv": "DT – Tržni Centar", "feeder33_id": 4, "feeder11_id": 102, "nameplate_rating_kva": 800
        },
        {
            "id": 5, "tip": "upozorenje",
            "naziv": "Oscilacija vrednosti – Feeder33 North Ring",
            "poruka": "Detektovane oscilacije očitavanja ±18% u poslednjih sat vremena. Moguć nestabilan kontakt na brojilu.",
            "vreme": _ts(0, 4),
            "vrednost_pre": 3690, "vrednost_posle": 4350, "promena_pct": 18, "jedinica": "kWh",
            "meter_id": 1001, "msn": "MSN-F33-001", "kanal_naziv": "Aktivna preuzeta energija",
            "feeder_naziv": "Feeder33 – North Ring", "feeder33_id": 1, "feeder11_id": None, "nameplate_rating_kva": 5000
        },
        {
            "id": 6, "tip": "upozorenje",
            "naziv": "Neobičan porast u noćnim satima – DT Aerodrom",
            "poruka": "Potrošnja u periodu 02:00–04:00 porasla za 28% u odnosu na prosek. Moguć neplanirani rad opreme.",
            "vreme": _ts(1, 0),
            "vrednost_pre": 593, "vrednost_posle": 760, "promena_pct": 28, "jedinica": "kVA",
            "meter_id": 3005, "msn": "MSN-DT-305", "kanal_naziv": "Aktivna preuzeta energija",
            "feeder_naziv": "DT – Aerodrom", "feeder33_id": 7, "feeder11_id": 106, "nameplate_rating_kva": 1000
        },

        # ── GUBICI ──────────────────────────────────────────────────────────────
        {
            "id": 7, "tip": "gubitak",
            "naziv": "Tehnički gubitak – Feeder33 South Ring",
            "poruka": "Razlika između isporučene energije (Feeder33) i zbirnog očitavanja podstanica iznosi 12.4%. Iznad dozvoljenog praga od 8%.",
            "vreme": _ts(0, 5),
            "vrednost_pre": 2790, "vrednost_posle": 2443, "promena_pct": -12, "jedinica": "kWh",
            "meter_id": 1002, "msn": "MSN-F33-002", "kanal_naziv": "Aktivna preuzeta energija",
            "feeder_naziv": "Feeder33 – South Ring", "feeder33_id": 2, "feeder11_id": None, "nameplate_rating_kva": 4500
        },
        {
            "id": 8, "tip": "gubitak",
            "naziv": "Netehničke gubitke – Feeder11 Segment D4",
            "poruka": "Sumnja na neovlašćeno priključenje. Izmerena energija na vodu (248 kWh) nije pokrivena registrovanim potrošačima (196 kWh). Razlika: 52 kWh.",
            "vreme": _ts(1, 2),
            "vrednost_pre": 248, "vrednost_posle": 196, "promena_pct": -21, "jedinica": "kWh",
            "meter_id": 2004, "msn": "MSN-F11-104", "kanal_naziv": "Aktivna preuzeta energija",
            "feeder_naziv": "Feeder11 – Segment D4", "feeder33_id": 6, "feeder11_id": 104, "nameplate_rating_kva": 800
        },
        {
            "id": 9, "tip": "gubitak",
            "naziv": "Visoki gubici – Feeder33 East Line",
            "poruka": "Kumulativni gubici za poslednjih 24h iznose 16.2% ukupne isporučene energije. Preporučena terenska inspekcija kablovske trase.",
            "vreme": _ts(1, 6),
            "vrednost_pre": 4440, "vrednost_posle": 3721, "promena_pct": -16, "jedinica": "kWh",
            "meter_id": 1003, "msn": "MSN-F33-003", "kanal_naziv": "Aktivna preuzeta energija",
            "feeder_naziv": "Feeder33 – East Line", "feeder33_id": 3, "feeder11_id": None, "nameplate_rating_kva": 6000
        },

        # ── INFO ────────────────────────────────────────────────────────────────
        {
            "id": 10, "tip": "info",
            "naziv": "Redovno očitavanje – Feeder33 West Line",
            "poruka": "Vrednost redovnog mesečnog očitavanja snimljena. Sve u granicama normalnog rada.",
            "vreme": _ts(2, 0),
            "vrednost_pre": 1520, "vrednost_posle": 1575, "promena_pct": 4, "jedinica": "kWh",
            "meter_id": 1004, "msn": "MSN-F33-004", "kanal_naziv": "Aktivna preuzeta energija",
            "feeder_naziv": "Feeder33 – West Line", "feeder33_id": 4, "feeder11_id": None, "nameplate_rating_kva": 3500
        },
        {
            "id": 11, "tip": "info",
            "naziv": "Vraćanje u normalu – DT Bolnica",
            "poruka": "Potrošnja se stabilizovala nakon jutarnjeg skoka. Trenutna vrednost u okviru uobičajenog opsega.",
            "vreme": _ts(2, 4),
            "vrednost_pre": 598, "vrednost_posle": 365, "promena_pct": -39, "jedinica": "kVA",
            "meter_id": 3004, "msn": "MSN-DT-304", "kanal_naziv": "Aktivna preuzeta energija",
            "feeder_naziv": "DT – Bolnica", "feeder33_id": 6, "feeder11_id": 104, "nameplate_rating_kva": 630
        },
        {
            "id": 12, "tip": "info",
            "naziv": "Planirana promena potrošnje – DT Pivara",
            "poruka": "Potrošnja u okviru najavljenog režima rada. Proizvodni pogon radi prema rasporedu.",
            "vreme": _ts(3, 0),
            "vrednost_pre": 180, "vrednost_posle": 196, "promena_pct": 9, "jedinica": "kVA",
            "meter_id": 3006, "msn": "MSN-DT-306", "kanal_naziv": "Aktivna preuzeta energija",
            "feeder_naziv": "DT – Pivara", "feeder33_id": 3, "feeder11_id": 105, "nameplate_rating_kva": 400
        },
    ])


if __name__ == '__main__':
    app.run(debug=False, port=5000)