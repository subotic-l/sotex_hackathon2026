import pymssql
import csv
from datetime import datetime, timedelta
from collections import defaultdict

# ---------------------------
# KONFIGURACIJA
# ---------------------------
DB_CONFIG = {
    'server': 'localhost',
    'port': 1433,
    'user': 'sa',
    'password': 'SotexSolutions123!',
    'database': 'SotexHackathon'
}

TABLE_NAME = "MeterReadTfes"

# Referentni datum (do kog gledamo podatke)
REFERENCE_DT = datetime(2026, 4, 16, 0, 0, 0)

# Koliko poslednjih merenja po brojilu analiziramo
N_LAST = 24

# Ocekivani interval
EXPECTED_INTERVAL = timedelta(hours=2)

# Tolerancija (npr +/- 5 minuta)
TOLERANCE = timedelta(minutes=5)

# Minimalni i maksimalni dozvoljeni interval
INTERVAL_MIN = timedelta(minutes=0)
INTERVAL_MAX = timedelta(hours=2, minutes=5)


def fetch_last_n_per_meter(conn, reference_dt: datetime, n_last: int):
    """
    Vraca poslednjih n_last merenja po svakom Mid, zakljucno sa reference_dt.
    """
    query = f"""
    ;WITH ranked AS (
        SELECT
            Mid,
            Ts,
            Val,
            ROW_NUMBER() OVER (PARTITION BY Mid ORDER BY Ts DESC) AS rn
        FROM {TABLE_NAME}
        WHERE Ts <= %s
    )
    SELECT Mid, Ts, Val
    FROM ranked
    WHERE rn <= %s
    ORDER BY Mid, Ts ASC;
    """
    cur = conn.cursor()
    cur.execute(query, (reference_dt, n_last))
    
    # Koristi generator sa batch fetchanjem umesto učitavanja svega odjednom
    batch_size = 1000
    while True:
        rows = cur.fetchmany(batch_size)
        if not rows:
            break
        
        per_meter = defaultdict(list)
        for r in rows:
            # pymssql vraća tuples: (Mid, Ts, Val)
            per_meter[r[0]].append({"Ts": r[1], "Val": r[2]})
        
        yield per_meter


def analyze_meter_readings(per_meter_data, reference_dt, expected_interval, tolerance, n_last):
    """
    Za svako brojilo proverava intervale izmedju uzastopnih merenja.
    Status:
      - DOWN: bar jedan interval odstupa od dozvoljenog opsega (INTERVAL_MIN do INTERVAL_MAX)
      - DOWN: nema dovoljno merenja (manje od 2)
      - DOWN: prvo (najstarije) merenje je previše staro - merilo nije merilo nedavno
      - OK: svi intervali u dozvoljenom opsegu i prva merenja je nedavna
    
    Vraca generator sa rezultatima.
    """
    # Koristimo globalne MIN i MAX intervale
    lower = INTERVAL_MIN
    upper = INTERVAL_MAX
    
    # Maksimalna dozvoljava starost prvog merenja
    # Ako imamo 24 merenja sa 1h razmakom, trebalo bi da pokrivaju ~24h pre reference_dt
    max_expected_span = expected_interval * (n_last - 1)
    max_allowed_age = max_expected_span + tolerance

    for mid, readings_asc in per_meter_data.items():
        # readings su sada ASC (od najstarijeg ka novom)
        if len(readings_asc) < 2:
            yield {
                "Mid": mid,
                "status": "DOWN",
                "reason": "Nedovoljno merenja za proveru intervala",
                "count": len(readings_asc),
                "bad_intervals": 0,
                "down_from": "",
                "down_to": ""
            }
            continue
        
        # Provera: da li je prvo (najstarije) merenje previše staro?
        first_reading_ts = readings_asc[0]["Ts"]
        age_of_first = reference_dt - first_reading_ts
        
        if age_of_first > max_allowed_age:
            yield {
                "Mid": mid,
                "status": "DOWN",
                "reason": f"Prvo merenje je previše staro ({age_of_first})",
                "count": len(readings_asc),
                "bad_intervals": 0,
                "down_from": "",
                "down_to": ""
            }
            continue

        bad_intervals = []
        for i in range(len(readings_asc) - 1):
            ts_older = readings_asc[i]["Ts"]
            ts_newer = readings_asc[i + 1]["Ts"]
            delta = ts_newer - ts_older

            if not (lower <= delta <= upper):
                bad_intervals.append({
                    "from_ts": ts_older,
                    "to_ts": ts_newer,
                    "delta_minutes": delta.total_seconds() / 60.0
                })

        if bad_intervals:
            yield {
                "Mid": mid,
                "status": "DOWN",
                "reason": "Nepravilni vremenski razmaci",
                "count": len(readings_asc),
                "bad_intervals": len(bad_intervals),
                "down_from": bad_intervals[0]["from_ts"],
                "down_to": bad_intervals[-1]["to_ts"]
            }
        else:
            yield {
                "Mid": mid,
                "status": "OK",
                "reason": "Svi razmaci su validni i merenja su nedavna",
                "count": len(readings_asc),
                "bad_intervals": 0,
                "down_from": "",
                "down_to": ""
            }


def main():
    output_file = "meter_check_results.csv"
    
    print(f"[INFO] Reference datetime: {REFERENCE_DT}")
    print(f"[INFO] Last N readings per meter: {N_LAST}")
    print(f"[INFO] Allowed interval range: {INTERVAL_MIN} to {INTERVAL_MAX}")
    print(f"[INFO] Output file: {output_file}\n")

    conn = pymssql.connect(**DB_CONFIG)

    try:
        # Otvori CSV fajl za pisanje
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Mid', 'Status', 'Reason', 'Reading_Count', 'Bad_Intervals', 'Down_From', 'Down_To']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            down_count = 0
            ok_count = 0
            batch_num = 0
            
            # Procesira batche brojila
            for per_meter_batch in fetch_last_n_per_meter(conn, REFERENCE_DT, N_LAST):
                batch_num += 1
                
                # Analiza i pisanje u CSV
                for result in analyze_meter_readings(per_meter_batch, REFERENCE_DT, EXPECTED_INTERVAL, TOLERANCE, N_LAST):
                    writer.writerow({
                        'Mid': result['Mid'],
                        'Status': result['status'],
                        'Reason': result['reason'],
                        'Reading_Count': result['count'],
                        'Bad_Intervals': result['bad_intervals'],
                        'Down_From': result['down_from'],
                        'Down_To': result['down_to']
                    })
                    
                    if result['status'] == 'DOWN':
                        down_count += 1
                    else:
                        ok_count += 1
                
                print(f"[INFO] Batch {batch_num} procesiran: {len(per_meter_batch)} brojila")

        total = down_count + ok_count
        print(f"\n[REZIME] Total: {total} | OK: {ok_count} | DOWN: {down_count}")
        print(f"[INFO] Rezultati zapisani u: {output_file}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()