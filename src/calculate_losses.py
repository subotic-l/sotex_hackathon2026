import pymssql
import pandas as pd
from datetime import date, timedelta
import sys

FEEDERS11_CONDITION = "1=1"
FEEDERS33_CONDITION = """
    EXISTS (SELECT 1 FROM DistributionSubstation d WHERE d.Feeder33Id = f.Id)
    OR
    EXISTS (SELECT 1 FROM Feeder33Substation fs WHERE fs.Feeders33Id = f.Id)
"""
DISTRIBUTION_SUBSTATION_CONDITION = "1=1"

# Primeni end_date kao argument ili koristi danas
if len(sys.argv) > 1:
    end_date_arg = date.fromisoformat(sys.argv[1])
else:
    end_date_arg = date.today()

END_DATE = end_date_arg.strftime('%Y-%m-%d')
START_DATE = (end_date_arg - timedelta(days=30)).strftime('%Y-%m-%d')
TOTAL_DAYS = 30

def create_tables(conn):
    cursor = conn.cursor()
    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='FeederLosses11' AND xtype='U')
        CREATE TABLE FeederLosses11 (
            Mid INT,
            Difference FLOAT,
            LossPercentage FLOAT,
            DSCoverage FLOAT,
            FeederId INT,
            GeneratedAt DATE
        )
    """)
    cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='FeederLosses33' AND xtype='U')
        CREATE TABLE FeederLosses33 (
            Mid INT,
            Difference FLOAT,
            LossPercentage FLOAT,
            Coverage FLOAT,
            FeederId INT,
            GeneratedAt DATE
        )
    """)
    conn.commit()

def connect_to_db():
    conn = pymssql.connect(
        server='localhost',
        port='1433',
        user='sa',
        password='SotexSolutions123!',
        database='SotexHackathon'
    )
    return conn

def get_valid_data(conn, name, condition):
    return pd.read_sql(f"""
        SELECT *
        FROM {name} f
        WHERE MeterId IS NOT NULL
        AND (
{condition}
        )
    """, conn)

def get_feeders_with_meter(conn):
    feeders33 = get_valid_data(conn=conn, name="Feeders33", condition=FEEDERS33_CONDITION)
    feeders11 = get_valid_data(conn=conn, name="Feeders11", condition=FEEDERS11_CONDITION)
    return feeders11, feeders33

def get_feeder_energy_diff(conn, feeders, start_date, end_date):
    ids = ','.join(str(i) for i in feeders['MeterId'].tolist())
    return pd.read_sql(f"""
        WITH ranked AS (
            SELECT Mid, Val, Ts,
                   ROW_NUMBER() OVER (PARTITION BY Mid ORDER BY Ts DESC) as rn
            FROM MeterReadTfes
            WHERE Mid IN ({ids})
            AND CAST(Ts AS DATE) BETWEEN '{start_date}' AND '{end_date}'
        )
        SELECT 
            r1.Mid,
            r1.Val - r2.Val AS Diff,
            r1.Ts AS LastTs,
            r2.Ts AS PrevTs
        FROM ranked r1
        JOIN ranked r2 ON r1.Mid = r2.Mid
        WHERE r1.rn = 1 AND r2.rn = (SELECT MAX(rn) FROM ranked WHERE Mid = r1.Mid)
    """, conn)

def get_ds_energy_diff(conn, feeders, start_date, end_date):
    ids = ','.join(str(i) for i in feeders['MeterId'].tolist())
    return pd.read_sql(f"""
        WITH ranked AS (
            SELECT m.Mid, m.Val, m.Ts, ds.Feeder11Id, ds.Feeder33Id,
                   ROW_NUMBER() OVER (PARTITION BY m.Mid ORDER BY m.Ts DESC) as rn
            FROM MeterReadTfes m
            JOIN DistributionSubstation ds ON ds.MeterId = m.Mid
            WHERE m.Mid IN ({ids})
            AND CAST(Ts AS DATE) BETWEEN '{start_date}' AND '{end_date}'
        )
        SELECT 
            r1.Mid,
            r1.Feeder11Id,
            r1.Feeder33Id,
            r1.Val - r2.Val AS Diff,
            r1.Ts AS LastTs,
            r2.Ts AS PrevTs
        FROM ranked r1
        JOIN ranked r2 ON r1.Mid = r2.Mid
        WHERE r1.rn = 1 AND r2.rn = (SELECT MAX(rn) FROM ranked WHERE Mid = r1.Mid)
    """, conn)

def get_active_days(conn, ids_list, start_date, end_date):
    ids = ','.join(str(i) for i in ids_list)
    return pd.read_sql(f"""
        SELECT Mid, COUNT(DISTINCT CAST(Ts AS DATE)) AS ActiveDays
        FROM MeterReadTfes
        WHERE Mid IN ({ids})
        AND CAST(Ts AS DATE) BETWEEN '{start_date}' AND '{end_date}'
        GROUP BY Mid
    """, conn)

if __name__ == "__main__":
    conn = connect_to_db()
    try:
        create_tables(conn=conn)
        feeders11, feeders33 = get_feeders_with_meter(conn)
        distribution_substations = get_valid_data(conn, "DistributionSubstation", DISTRIBUTION_SUBSTATION_CONDITION)

        diff11 = get_feeder_energy_diff(conn, feeders11, START_DATE, END_DATE)
        diff33 = get_feeder_energy_diff(conn, feeders33, START_DATE, END_DATE)
        diff_ds = get_ds_energy_diff(conn, distribution_substations, START_DATE, END_DATE)

        # Skaliranje DS
        ds_active = get_active_days(conn, distribution_substations['MeterId'].tolist(), START_DATE, END_DATE)
        diff_ds = diff_ds.merge(ds_active, on='Mid', how='left')
        diff_ds['DiffScaled'] = diff_ds['Diff'] / diff_ds['ActiveDays'] * TOTAL_DAYS

        # Skaliranje feeder11
        f11_active = get_active_days(conn, feeders11['MeterId'].tolist(), START_DATE, END_DATE)
        diff11 = diff11.merge(f11_active, on='Mid', how='left')
        diff11['DiffScaled'] = diff11['Diff'] / diff11['ActiveDays'] * TOTAL_DAYS

        # ── Feeder11 analiza ──────────────────────────────────────────
        ds_grouped_by_feeder11 = diff_ds.groupby('Feeder11Id')['DiffScaled'].sum().reset_index()
        ds_grouped_by_feeder11['Feeder11Id'] = ds_grouped_by_feeder11['Feeder11Id'].astype(int)

        ds_count_with_readings = diff_ds.groupby('Feeder11Id')['Mid'].count().reset_index()
        ds_count_with_readings.columns = ['Feeder11Id', 'DSWithReadings']
        ds_count_with_readings['Feeder11Id'] = ds_count_with_readings['Feeder11Id'].astype(int)

        ds_total_count = distribution_substations.groupby('Feeder11Id')['MeterId'].count().reset_index()
        ds_total_count.columns = ['Feeder11Id', 'DSTotal']
        ds_total_count['Feeder11Id'] = ds_total_count['Feeder11Id'].astype(int)

        diff11['Mid'] = diff11['Mid'].astype(int)

        result11 = diff11.merge(ds_grouped_by_feeder11, left_on='Mid', right_on='Feeder11Id', how='left')
        result11 = result11.merge(ds_count_with_readings, on='Feeder11Id', how='left')
        result11 = result11.merge(ds_total_count, on='Feeder11Id', how='left')

        result11['DSCoverage'] = result11['DSWithReadings'] / result11['DSTotal']
        result11['Difference'] = result11['DiffScaled_x'] - result11['DiffScaled_y']
        result11['LossPercentage'] = (result11['Difference'] / result11['DiffScaled_x']) * 100

        result11 = result11[result11['LossPercentage'] >= 0].dropna(subset=['LossPercentage', 'DSCoverage'])

        feeders11_meta = feeders11[['MeterId', 'Id']].copy()
        feeders11_meta['MeterId'] = feeders11_meta['MeterId'].astype(int)
        result11 = result11.merge(feeders11_meta, left_on='Mid', right_on='MeterId', how='left')

        # ── Feeder33 analiza ──────────────────────────────────────────
        feeder11_to_feeder33 = feeders11[['MeterId', 'Feeder33Id']].dropna().drop_duplicates()
        feeder11_to_feeder33['MeterId'] = feeder11_to_feeder33['MeterId'].astype(int)
        diff11_with_feeder33 = diff11.merge(feeder11_to_feeder33, left_on='Mid', right_on='MeterId', how='inner')
        feeder11_grouped_by_feeder33 = diff11_with_feeder33.groupby('Feeder33Id')['DiffScaled'].sum().reset_index()

        ds_grouped_by_feeder33 = diff_ds.groupby('Feeder33Id')['DiffScaled'].sum().reset_index()

        feeder33_children = feeder11_grouped_by_feeder33.merge(ds_grouped_by_feeder33, on='Feeder33Id', how='outer').fillna(0)
        feeder33_children['TotalChildDiff'] = feeder33_children['DiffScaled_x'] + feeder33_children['DiffScaled_y']

        f11_count_with_readings = diff11_with_feeder33.groupby('Feeder33Id')['Mid'].count().reset_index()
        f11_count_with_readings.columns = ['Feeder33Id', 'F11WithReadings']
        f11_count_with_readings['Feeder33Id'] = f11_count_with_readings['Feeder33Id'].astype(int)

        f11_total_count = feeders11.groupby('Feeder33Id')['Id'].count().reset_index()
        f11_total_count.columns = ['Feeder33Id', 'F11Total']
        f11_total_count['Feeder33Id'] = f11_total_count['Feeder33Id'].astype(int)

        direct_ds_total = distribution_substations[distribution_substations['Feeder33Id'].notna()].groupby('Feeder33Id')['MeterId'].count().reset_index()
        direct_ds_total.columns = ['Feeder33Id', 'DirectDSTotal']
        direct_ds_total['Feeder33Id'] = direct_ds_total['Feeder33Id'].astype(int)

        direct_ds_with_readings = diff_ds[diff_ds['Feeder33Id'].notna()].groupby('Feeder33Id')['Mid'].count().reset_index()
        direct_ds_with_readings.columns = ['Feeder33Id', 'DirectDSWithReadings']
        direct_ds_with_readings['Feeder33Id'] = direct_ds_with_readings['Feeder33Id'].astype(int)

        diff33['Mid'] = diff33['Mid'].astype(int)
        feeder33_children['Feeder33Id'] = feeder33_children['Feeder33Id'].astype(int)

        feeders33_id_to_meterid = feeders33[['Id', 'MeterId']].copy()
        feeders33_id_to_meterid['Id'] = feeders33_id_to_meterid['Id'].astype(int)
        feeders33_id_to_meterid['MeterId'] = feeders33_id_to_meterid['MeterId'].astype(int)

        feeder33_children = feeder33_children.merge(feeders33_id_to_meterid, left_on='Feeder33Id', right_on='Id', how='left')
        feeder33_children = feeder33_children.merge(f11_count_with_readings, on='Feeder33Id', how='left')
        feeder33_children = feeder33_children.merge(f11_total_count, on='Feeder33Id', how='left')
        feeder33_children = feeder33_children.merge(direct_ds_total, on='Feeder33Id', how='left')
        feeder33_children = feeder33_children.merge(direct_ds_with_readings, on='Feeder33Id', how='left')
        feeder33_children = feeder33_children.fillna(0)

        feeder33_children['TotalChildren'] = feeder33_children['F11Total'] + feeder33_children['DirectDSTotal']
        feeder33_children['TotalWithReadings'] = feeder33_children['F11WithReadings'] + feeder33_children['DirectDSWithReadings']
        feeder33_children['Coverage'] = feeder33_children['TotalWithReadings'] / feeder33_children['TotalChildren']

        result33 = diff33.merge(feeder33_children[['MeterId', 'TotalChildDiff', 'Coverage', 'Feeder33Id']], left_on='Mid', right_on='MeterId', how='left')
        result33['Difference'] = result33['Diff'] - result33['TotalChildDiff']
        result33['LossPercentage'] = (result33['Difference'] / result33['Diff']) * 100

        result33 = result33[result33['LossPercentage'] >= 0].dropna(subset=['LossPercentage', 'Coverage'])
        result33['Feeder33Id'] = result33['Feeder33Id'].astype(int)


        cursor = conn.cursor()
        generated_at = END_DATE

        cursor.execute("DELETE FROM FeederLosses11 WHERE GeneratedAt = %s", (generated_at,))
        cursor.execute("DELETE FROM FeederLosses33 WHERE GeneratedAt = %s", (generated_at,))
        conn.commit()

        for _, row in result11[['Mid', 'Difference', 'LossPercentage', 'DSCoverage', 'Id']].dropna().iterrows():
            cursor.execute("""
                INSERT INTO FeederLosses11 (Mid, Difference, LossPercentage, DSCoverage, FeederId, GeneratedAt)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (int(row['Mid']), float(row['Difference']), float(row['LossPercentage']), float(row['DSCoverage']), int(row['Id']), generated_at))

        for _, row in result33[['Mid', 'Difference', 'LossPercentage', 'Coverage', 'Feeder33Id']].dropna().iterrows():
            cursor.execute("""
                INSERT INTO FeederLosses33 (Mid, Difference, LossPercentage, Coverage, FeederId, GeneratedAt)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (int(row['Mid']), float(row['Difference']), float(row['LossPercentage']), float(row['Coverage']), int(row['Feeder33Id']), generated_at))

        conn.commit()
    finally:
        conn.close()