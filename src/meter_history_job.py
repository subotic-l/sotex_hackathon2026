import argparse
from datetime import date, datetime, time, timedelta

import pymssql

# ---------------------------
# KONFIGURACIJA
# ---------------------------
DB_CONFIG = {
    'server': 'localhost',
    'port': 1433,
    'user': 'sa',
    'password': 'SotexSolutions123!',
    'database': 'SotexHackathon',
}

SOURCE_TABLE = 'MeterReadTfes'
HISTORY_TABLE = 'MeterDailyStatusHistory'

DEFAULT_BACKFILL_START = date(2026, 4, 6)
DEFAULT_BACKFILL_END = date(2026, 4, 16)
DEFAULT_DAILY_TARGET = date.today() - timedelta(days=1)

N_LAST = 24
EXPECTED_INTERVAL = timedelta(hours=2)
TOLERANCE = timedelta(minutes=5)
INTERVAL_MIN = timedelta(minutes=0)
INTERVAL_MAX = timedelta(hours=2, minutes=5)


def connect_to_db():
    return pymssql.connect(**DB_CONFIG)


def resolve_source_meter_column(conn):
    sql = """
    SELECT COLUMN_NAME
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = %s
    """

    cur = conn.cursor()
    try:
        cur.execute(sql, (SOURCE_TABLE,))
        columns = [row[0] for row in cur.fetchall()]
    finally:
        cur.close()

    if not columns:
        raise ValueError(f'No columns found for source table {SOURCE_TABLE}')

    normalized = {col.lower(): col for col in columns}
    candidates = ['idmeter', 'mid', 'meterid', 'id_meter', 'meter_id']
    for candidate in candidates:
        if candidate in normalized:
            resolved = normalized[candidate]
            print(f'[INFO] Using source meter ID column: {resolved}')
            return resolved

    raise ValueError(
        f'Unable to detect meter ID column in {SOURCE_TABLE}. Available columns: {", ".join(columns)}'
    )


def ensure_history_table(conn):
    ddl = f"""
    IF OBJECT_ID('{HISTORY_TABLE}', 'U') IS NULL
    BEGIN
        CREATE TABLE {HISTORY_TABLE} (
            IdMeter INT NOT NULL,
            SnapshotDate DATE NOT NULL,
            ReferenceDateTime DATETIME NOT NULL,
            Status VARCHAR(10) NOT NULL,
            Reason NVARCHAR(200) NOT NULL,
            ReadingCount INT NOT NULL,
            BadIntervals INT NOT NULL,
            DownFrom DATETIME NULL,
            DownTo DATETIME NULL,
            CreatedAt DATETIME NOT NULL CONSTRAINT DF_{HISTORY_TABLE}_CreatedAt DEFAULT GETDATE(),
            UpdatedAt DATETIME NOT NULL CONSTRAINT DF_{HISTORY_TABLE}_UpdatedAt DEFAULT GETDATE(),
            CONSTRAINT PK_{HISTORY_TABLE} PRIMARY KEY (IdMeter, SnapshotDate)
        );

        CREATE INDEX IX_{HISTORY_TABLE}_SnapshotDate_Status ON {HISTORY_TABLE} (SnapshotDate, Status);
        CREATE INDEX IX_{HISTORY_TABLE}_Status ON {HISTORY_TABLE} (Status);
    END
    """
    cur = conn.cursor()
    try:
        cur.execute(ddl)
    finally:
        cur.close()
    conn.commit()


def fetch_meter_groups_as_of(conn, reference_dt: datetime, n_last: int, meter_id_column: str):
    query = f"""
    ;WITH ranked AS (
        SELECT
            {meter_id_column} AS MeterId,
            Ts,
            Val,
            ROW_NUMBER() OVER (PARTITION BY {meter_id_column} ORDER BY Ts DESC) AS rn
        FROM {SOURCE_TABLE}
        WHERE Ts <= %s
    )
    SELECT MeterId, Ts, Val
    FROM ranked
    WHERE rn <= %s
    ORDER BY MeterId, Ts ASC;
    """
    cur = conn.cursor()
    try:
        cur.execute(query, (reference_dt, n_last))
        rows = cur.fetchall()
    finally:
        cur.close()

    meter_groups = {}
    for row in rows:
        meter_id = row[0]
        reading = {'Ts': row[1], 'Val': row[2]}

        if meter_id not in meter_groups:
            meter_groups[meter_id] = []
        meter_groups[meter_id].append(reading)

    return meter_groups


def analyze_meter_readings(id_meter, readings_asc, reference_dt, expected_interval, tolerance, n_last):
    lower = INTERVAL_MIN
    upper = INTERVAL_MAX

    max_expected_span = expected_interval * (n_last - 1)
    max_allowed_age = max_expected_span + tolerance

    if len(readings_asc) < 2:
        return {
            'IdMeter': id_meter,
            'SnapshotDate': reference_dt.date(),
            'ReferenceDateTime': reference_dt,
            'Status': 'DOWN',
            'Reason': 'Nedovoljno merenja za proveru intervala',
            'ReadingCount': len(readings_asc),
            'BadIntervals': 0,
            'DownFrom': None,
            'DownTo': None,
        }

    first_reading_ts = readings_asc[0]['Ts']
    age_of_first = reference_dt - first_reading_ts

    if age_of_first > max_allowed_age:
        return {
            'IdMeter': id_meter,
            'SnapshotDate': reference_dt.date(),
            'ReferenceDateTime': reference_dt,
            'Status': 'DOWN',
            'Reason': f'Prvo merenje je previše staro ({age_of_first})',
            'ReadingCount': len(readings_asc),
            'BadIntervals': 0,
            'DownFrom': None,
            'DownTo': None,
        }

    bad_intervals = []
    for index in range(len(readings_asc) - 1):
        ts_older = readings_asc[index]['Ts']
        ts_newer = readings_asc[index + 1]['Ts']
        delta = ts_newer - ts_older

        if not (lower <= delta <= upper):
            bad_intervals.append({
                'from_ts': ts_older,
                'to_ts': ts_newer,
            })

    if bad_intervals:
        return {
            'IdMeter': id_meter,
            'SnapshotDate': reference_dt.date(),
            'ReferenceDateTime': reference_dt,
            'Status': 'DOWN',
            'Reason': 'Nepravilni vremenski razmaci',
            'ReadingCount': len(readings_asc),
            'BadIntervals': len(bad_intervals),
            'DownFrom': bad_intervals[0]['from_ts'],
            'DownTo': bad_intervals[-1]['to_ts'],
        }

    return {
        'IdMeter': id_meter,
        'SnapshotDate': reference_dt.date(),
        'ReferenceDateTime': reference_dt,
        'Status': 'OK',
        'Reason': 'Svi razmaci su validni i merenja su nedavna',
        'ReadingCount': len(readings_asc),
        'BadIntervals': 0,
        'DownFrom': None,
        'DownTo': None,
    }


def get_distinct_source_meter_count(conn, reference_dt: datetime, meter_id_column: str):
    sql = f"""
    SELECT COUNT(DISTINCT {meter_id_column})
    FROM {SOURCE_TABLE}
    WHERE Ts <= %s
    """
    cur = conn.cursor()
    try:
        cur.execute(sql, (reference_dt,))
        row = cur.fetchone()
        return int(row[0] or 0)
    finally:
        cur.close()


def delete_history_range(conn, start_date, end_date):
    sql = f"DELETE FROM {HISTORY_TABLE} WHERE SnapshotDate BETWEEN %s AND %s"
    cur = conn.cursor()
    try:
        cur.execute(sql, (start_date, end_date))
    finally:
        cur.close()
    conn.commit()
    print(f'[INFO] Deleted existing history rows for {start_date.isoformat()} -> {end_date.isoformat()}')


def upsert_history_row(conn, result):
    merge_sql = f"""
    MERGE {HISTORY_TABLE} AS target
    USING (
        SELECT
            %s AS IdMeter,
            %s AS SnapshotDate
    ) AS source
    ON target.IdMeter = source.IdMeter AND target.SnapshotDate = source.SnapshotDate
    WHEN MATCHED THEN
        UPDATE SET
            ReferenceDateTime = %s,
            Status = %s,
            Reason = %s,
            ReadingCount = %s,
            BadIntervals = %s,
            DownFrom = %s,
            DownTo = %s,
            UpdatedAt = GETDATE()
    WHEN NOT MATCHED THEN
        INSERT (
            IdMeter,
            SnapshotDate,
            ReferenceDateTime,
            Status,
            Reason,
            ReadingCount,
            BadIntervals,
            DownFrom,
            DownTo
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s
        );
    """

    params = (
        result['IdMeter'],
        result['SnapshotDate'],
        result['ReferenceDateTime'],
        result['Status'],
        result['Reason'],
        result['ReadingCount'],
        result['BadIntervals'],
        result['DownFrom'],
        result['DownTo'],
        result['IdMeter'],
        result['SnapshotDate'],
        result['ReferenceDateTime'],
        result['Status'],
        result['Reason'],
        result['ReadingCount'],
        result['BadIntervals'],
        result['DownFrom'],
        result['DownTo'],
    )

    cur = conn.cursor()
    try:
        cur.execute(merge_sql, params)
    finally:
        cur.close()


def process_snapshot_date(conn, snapshot_date, meter_id_column):
    reference_dt = datetime.combine(snapshot_date + timedelta(days=1), time.min)
    processed = 0
    down_count = 0
    ok_count = 0
    distinct_source_meters = get_distinct_source_meter_count(conn, reference_dt, meter_id_column)
    meter_groups = fetch_meter_groups_as_of(conn, reference_dt, N_LAST, meter_id_column)

    print(f'[INFO] Processing snapshot for {snapshot_date.isoformat()} using reference {reference_dt}')
    print(f'[INFO] Distinct meters in source up to reference: {distinct_source_meters}')
    print(f'[INFO] Meter groups loaded for analysis: {len(meter_groups)}')

    for id_meter, readings in meter_groups.items():
        result = analyze_meter_readings(id_meter, readings, reference_dt, EXPECTED_INTERVAL, TOLERANCE, N_LAST)
        upsert_history_row(conn, result)
        processed += 1

        if result['Status'] == 'DOWN':
            down_count += 1
        else:
            ok_count += 1

        if processed % 500 == 0:
            conn.commit()
            print(f'[INFO]   committed {processed} meters so far')

    conn.commit()
    print(f'[INFO] Completed {snapshot_date.isoformat()} -> total={processed} ok={ok_count} down={down_count}')
    return processed, ok_count, down_count


def backfill_range(conn, start_date, end_date, meter_id_column):
    current = start_date
    total_processed = 0
    while current <= end_date:
        processed, _, _ = process_snapshot_date(conn, current, meter_id_column)
        total_processed += processed
        current += timedelta(days=1)
    return total_processed


def parse_args():
    parser = argparse.ArgumentParser(description='Build daily meter status history from existing readings.')
    parser.add_argument('--start', type=lambda value: datetime.strptime(value, '%Y-%m-%d').date(), help='Backfill start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=lambda value: datetime.strptime(value, '%Y-%m-%d').date(), help='Backfill end date (YYYY-MM-DD)')
    parser.add_argument('--date', type=lambda value: datetime.strptime(value, '%Y-%m-%d').date(), help='Process a single snapshot date (YYYY-MM-DD)')
    parser.add_argument('--reset', action='store_true', help='Delete existing history rows in target date range before processing')
    return parser.parse_args()


def main():
    args = parse_args()

    if args.date is not None:
        target_dates = (args.date, args.date)
        mode_label = f'single-day {args.date.isoformat()}'
    elif args.start is not None or args.end is not None:
        start_date = args.start or DEFAULT_BACKFILL_START
        end_date = args.end or start_date
        target_dates = (start_date, end_date)
        mode_label = f'backfill {start_date.isoformat()} -> {end_date.isoformat()}'
    else:
        target_dates = (DEFAULT_DAILY_TARGET, DEFAULT_DAILY_TARGET)
        mode_label = f'daily {DEFAULT_DAILY_TARGET.isoformat()}'

    start_date, end_date = target_dates
    if end_date < start_date:
        raise ValueError('End date cannot be earlier than start date')

    print(f'[INFO] Mode: {mode_label}')
    print(f'[INFO] Reading history from {SOURCE_TABLE} into {HISTORY_TABLE}')

    conn = connect_to_db()
    try:
        ensure_history_table(conn)
        meter_id_column = resolve_source_meter_column(conn)
        if args.reset:
            delete_history_range(conn, start_date, end_date)
        backfill_range(conn, start_date, end_date, meter_id_column)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
