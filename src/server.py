# server.py
import os
import glob
import time
import schedule
import subprocess
import threading
from datetime import datetime

import pymssql
from flask import Flask, jsonify, request

app = Flask(__name__)

DB_CONFIG = {
    'server': 'localhost',
    'port': 1433,
    'user': 'sa',
    'password': 'SotexSolutions123!',
    'database': 'SotexHackathon',
}

HISTORY_TABLE = 'MeterDailyStatusHistory'

FALLBACK_DASHBOARD = {
    'NumActiveMeters': 323,
    'NumDownMeters': 199,
    'NetworkEffectivnessPercentage': 0.73,
}


def connect_to_db():
    return pymssql.connect(**DB_CONFIG)


def get_latest_snapshot_date(conn):
    cur = conn.cursor()
    try:
        cur.execute(f'SELECT TOP 1 SnapshotDate FROM {HISTORY_TABLE} ORDER BY SnapshotDate DESC')
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        cur.close()


def get_dashboard_payload(conn):
    latest_snapshot = get_latest_snapshot_date(conn)
    if latest_snapshot is None:
        return FALLBACK_DASHBOARD

    cur = conn.cursor()
    try:
        cur.execute(
            f'''
            SELECT
                SUM(CASE WHEN Status = 'OK' THEN 1 ELSE 0 END) AS NumActiveMeters,
                SUM(CASE WHEN Status = 'DOWN' THEN 1 ELSE 0 END) AS NumDownMeters
            FROM {HISTORY_TABLE}
            WHERE SnapshotDate = %s
            ''',
            (latest_snapshot,)
        )
        row = cur.fetchone()
        if not row:
            return FALLBACK_DASHBOARD

        active = int(row[0] or 0)
        down = int(row[1] or 0)
        total = active + down
        effectiveness = round(active / total, 4) if total else 0.0

        return {
            'NumActiveMeters': active,
            'NumDownMeters': down,
            'NetworkEffectivnessPercentage': effectiveness,
        }
    finally:
        cur.close()


def get_meter_history(conn, status=None, snapshot_date=None, page=1, page_size=50):
    if snapshot_date is None:
        snapshot_date = get_latest_snapshot_date(conn)

    if snapshot_date is None:
        return {
            'snapshotDate': None,
            'page': page,
            'pageSize': page_size,
            'totalItems': 0,
            'totalPages': 0,
            'items': [],
        }

    filters = ['SnapshotDate = %s']
    params = [snapshot_date]

    if status in ('OK', 'DOWN'):
        filters.append('Status = %s')
        params.append(status)

    where_sql = ' AND '.join(filters)
    offset = (page - 1) * page_size

    cur = conn.cursor()
    try:
        cur.execute(
            f'SELECT COUNT(*) FROM {HISTORY_TABLE} WHERE {where_sql}',
            tuple(params)
        )
        total_items = int(cur.fetchone()[0] or 0)

        cur.execute(
            f'''
            SELECT
                IdMeter,
                SnapshotDate,
                Status,
                Reason,
                ReadingCount,
                BadIntervals,
                DownFrom,
                DownTo
            FROM {HISTORY_TABLE}
            WHERE {where_sql}
            ORDER BY IdMeter
            OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
            ''',
            tuple(params + [offset, page_size])
        )
        items = []
        for row in cur.fetchall():
            items.append({
                'IdMeter': row[0],
                'SnapshotDate': row[1].isoformat() if row[1] else None,
                'Status': row[2],
                'Reason': row[3],
                'ReadingCount': row[4],
                'BadIntervals': row[5],
                'DownFrom': row[6].isoformat() if row[6] else None,
                'DownTo': row[7].isoformat() if row[7] else None,
            })
    finally:
        cur.close()

    total_pages = (total_items + page_size - 1) // page_size if page_size else 0
    return {
        'snapshotDate': snapshot_date.isoformat() if snapshot_date else None,
        'page': page,
        'pageSize': page_size,
        'totalItems': total_items,
        'totalPages': total_pages,
        'items': items,
    }

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
    try:
        conn = connect_to_db()
        try:
            return jsonify(get_dashboard_payload(conn))
        finally:
            conn.close()
    except Exception:
        return jsonify(FALLBACK_DASHBOARD)


@app.route('/api/meters')
def meters_history():
    status = request.args.get('status')
    snapshot_date_raw = request.args.get('date')
    page = max(int(request.args.get('page', 1)), 1)
    page_size = min(max(int(request.args.get('pageSize', 50)), 1), 200)

    snapshot_date = None
    if snapshot_date_raw:
        snapshot_date = datetime.strptime(snapshot_date_raw, '%Y-%m-%d').date()

    try:
        conn = connect_to_db()
        try:
            payload = get_meter_history(conn, status=status, snapshot_date=snapshot_date, page=page, page_size=page_size)
            return jsonify(payload)
        finally:
            conn.close()
    except Exception as exc:
        return jsonify({'error': str(exc), 'items': [], 'totalItems': 0, 'totalPages': 0}), 500


@app.route('/api/meters/down')
def down_meters_history():
    snapshot_date_raw = request.args.get('date')
    page = max(int(request.args.get('page', 1)), 1)
    page_size = min(max(int(request.args.get('pageSize', 50)), 1), 200)

    snapshot_date = None
    if snapshot_date_raw:
        snapshot_date = datetime.strptime(snapshot_date_raw, '%Y-%m-%d').date()

    try:
        conn = connect_to_db()
        try:
            payload = get_meter_history(conn, status='DOWN', snapshot_date=snapshot_date, page=page, page_size=page_size)
            return jsonify(payload)
        finally:
            conn.close()
    except Exception as exc:
        return jsonify({'error': str(exc), 'items': [], 'totalItems': 0, 'totalPages': 0}), 500


@app.route('/api/meters/up')
def up_meters_history():
    snapshot_date_raw = request.args.get('date')
    page = max(int(request.args.get('page', 1)), 1)
    page_size = min(max(int(request.args.get('pageSize', 50)), 1), 200)

    snapshot_date = None
    if snapshot_date_raw:
        snapshot_date = datetime.strptime(snapshot_date_raw, '%Y-%m-%d').date()

    try:
        conn = connect_to_db()
        try:
            payload = get_meter_history(conn, status='OK', snapshot_date=snapshot_date, page=page, page_size=page_size)
            return jsonify(payload)
        finally:
            conn.close()
    except Exception as exc:
        return jsonify({'error': str(exc), 'items': [], 'totalItems': 0, 'totalPages': 0}), 500

if __name__ == '__main__':
    app.run(debug=False, port=5000)