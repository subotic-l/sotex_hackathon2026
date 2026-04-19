import pymssql
import pandas as pd
import folium
from folium.plugins import MarkerCluster


def connect_to_db():
    conn = pymssql.connect(
        server='localhost',
        port='1433',
        user='sa',
        password='SotexSolutions123!',
        database='SotexHackathon'
    )
    return conn

def extract_data(conn, table_name):
    return pd.read_sql(f"""
        SELECT Name, Latitude, Longitude 
        FROM {table_name}
        WHERE Latitude IS NOT NULL AND Longitude IS NOT NULL
    """, conn)

def generate_map(df_substations):
    return folium.Map(
        location=[df_substations['Latitude'].mean(), df_substations['Longitude'].mean()],
        zoom_start=12,
        tiles='CartoDB positron'
    )

def draw_elements(df_substations, v_icon, v_color, v_map):
    for _, row in df_substations.iterrows():
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=row['Name'],
            icon=folium.Icon(icon=v_icon, prefix='fa', color=v_color)
        ).add_to(v_map)

def extract_feeder_lines(conn, voltage_level, high_loss_ids=None):
    if voltage_level == 11:
        query = """
            SELECT 
                f.Id as FeederId,
                f.Name,
                COALESCE(ts.Latitude, ss.Latitude)   as StartLat,
                COALESCE(ts.Longitude, ss.Longitude) as StartLon,
                dt.Latitude  as EndLat,
                dt.Longitude as EndLon
            FROM Feeders11 f
            JOIN DistributionSubstation dt
                ON dt.Feeder11Id = f.Id
            LEFT JOIN TransmissionStations ts
                ON f.TsId = ts.Id
            LEFT JOIN Substations ss
                ON f.SsId = ss.Id
            WHERE dt.Latitude IS NOT NULL
              AND (ts.Latitude IS NOT NULL OR ss.Latitude IS NOT NULL)
        """
    else:
        query = """
            SELECT 
                f.Id as FeederId,
                f.Name,
                ts.Latitude  as StartLat,
                ts.Longitude as StartLon,
                COALESCE(dt.Latitude, ss.Latitude)   as EndLat,
                COALESCE(dt.Longitude, ss.Longitude) as EndLon
            FROM Feeders33 f
            JOIN TransmissionStations ts
                ON f.TsId = ts.Id
            LEFT JOIN DistributionSubstation dt
                ON dt.Feeder33Id = f.Id
            LEFT JOIN Feeder33Substation fs
                ON fs.Feeders33Id = f.Id
            LEFT JOIN Substations ss
                ON ss.Id = fs.SubstationsId
            WHERE ts.Latitude IS NOT NULL
              AND (dt.Latitude IS NOT NULL OR ss.Latitude IS NOT NULL)
        """
    df = pd.read_sql(query, conn)
    if high_loss_ids is not None:
        df['HighLoss'] = df['FeederId'].isin(high_loss_ids)
    else:
        df['HighLoss'] = False
    return df

def add_feeder_lines(df_feeders, color, v_map, weight=2, layer_name="Feeders", loss_color="red"):
    normal_features = []
    loss_features = []

    for _, group in df_feeders.groupby('FeederId'):
        feeder_name = group.iloc[0]['Name']
        start_lat = group.iloc[0]['StartLat']
        start_lon = group.iloc[0]['StartLon']
        is_high_loss = group.iloc[0]['HighLoss']

        points = list(zip(group['EndLat'], group['EndLon']))
        chain = []
        current = (start_lat, start_lon)
        remaining = points.copy()

        while remaining:
            nearest = min(remaining, key=lambda p: (p[0]-current[0])**2 + (p[1]-current[1])**2)
            chain.append(nearest)
            remaining.remove(nearest)
            current = nearest

        coords = (
            [[start_lon, start_lat]] +
            [[p[1], p[0]] for p in chain]
        )

        feature = {
            "type": "Feature",
            "properties": {"name": feeder_name},
            "geometry": {"type": "LineString", "coordinates": coords}
        }

        if is_high_loss:
            loss_features.append(feature)
        else:
            normal_features.append(feature)

    if normal_features:
        folium.GeoJson(
            {"type": "FeatureCollection", "features": normal_features},
            name=layer_name,
            style_function=lambda x: {"color": color, "weight": weight},
            tooltip=folium.GeoJsonTooltip(fields=["name"])
        ).add_to(v_map)

    if loss_features:
        folium.GeoJson(
            {"type": "FeatureCollection", "features": loss_features},
            name=f"{layer_name} - Visoki gubici (>15%)",
            style_function=lambda x, c=loss_color: {"color": c, "weight": weight + 2},
            tooltip=folium.GeoJsonTooltip(fields=["name"])
        ).add_to(v_map)

if __name__ == "__main__":
    conn = connect_to_db()
    try:
        # Ucitaj feedere sa visokim gubicima
        latest_date11 = pd.read_sql("SELECT MAX(GeneratedAt) as d FROM FeederLosses11", conn).iloc[0]['d']
        latest_date33 = pd.read_sql("SELECT MAX(GeneratedAt) as d FROM FeederLosses33", conn).iloc[0]['d']

        high_loss_11 = pd.read_sql(f"""
            SELECT FeederId FROM FeederLosses11
            WHERE LossPercentage > 15 AND GeneratedAt = '{latest_date11}'
        """, conn)['FeederId'].tolist()

        high_loss_33 = pd.read_sql(f"""
            SELECT FeederId FROM FeederLosses33
            WHERE LossPercentage > 15 AND GeneratedAt = '{latest_date33}'
        """, conn)['FeederId'].tolist()

        df_substation = extract_data(conn=conn, table_name="Substations")
        df_transmission = extract_data(conn=conn, table_name="TransmissionStations")
        df_dt = extract_data(conn=conn, table_name="DistributionSubstation")

        v_map = generate_map(df_substations=df_substation)

        draw_elements(df_substations=df_substation, v_icon='home', v_color='blue', v_map=v_map)
        draw_elements(df_substations=df_transmission, v_icon='industry', v_color='red', v_map=v_map)

        dt_clusters = MarkerCluster().add_to(v_map)
        draw_elements(df_substations=df_dt, v_icon='home', v_color='green', v_map=dt_clusters)

        df_feeders11 = extract_feeder_lines(conn, voltage_level=11, high_loss_ids=high_loss_11)
        df_feeders33 = extract_feeder_lines(conn, voltage_level=33, high_loss_ids=high_loss_33)

        df_total11 = pd.read_sql("SELECT COUNT(*) as cnt FROM Feeders11", conn)
        df_total33 = pd.read_sql("SELECT COUNT(*) as cnt FROM Feeders33", conn)

        add_feeder_lines(df_feeders11, color='purple', v_map=v_map, weight=2, layer_name="Feeder 11kV", loss_color="orange")
        add_feeder_lines(df_feeders33, color='black', v_map=v_map, weight=2, layer_name="Feeder 33kV", loss_color="red")

        folium.LayerControl().add_to(v_map)
        v_map.save("map.html")
        print("Done! Open map.html in your browser.")
    finally:
        conn.close()