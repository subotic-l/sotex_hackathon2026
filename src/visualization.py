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
    df_ret_val = pd.read_sql(f"""
        SELECT Name, Latitude, Longitude 
        FROM {table_name}
        WHERE Latitude IS NOT NULL AND Longitude IS NOT NULL
    """, conn)
    return df_ret_val

def generate_map(df_substations):
    v_map = folium.Map(
    location=[df_substations['Latitude'].mean(), df_substations['Longitude'].mean()],
    zoom_start=12,
    tiles='CartoDB positron'
    )
    return v_map


def draw_elements(df_substations, v_icon, v_color, v_map):
    for _, row in df_substations.iterrows():
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=row['Name'],
            icon=folium.Icon(icon=v_icon, prefix='fa', color=v_color)
        ).add_to(v_map)


if __name__ == "__main__":
    conn = connect_to_db()
    try:
        df_substation = extract_data(conn=conn, table_name="Substations")
        df_transmission = extract_data(conn=conn, table_name="TransmissionStations")
        df_dt = extract_data(conn=conn, table_name="DistributionSubstation")
        v_map = generate_map(df_substations=df_substation)
        draw_elements(df_substations=df_substation, v_icon='home', v_color='blue', v_map=v_map)
        draw_elements(df_substations=df_transmission, v_icon='industry', v_color='red', v_map=v_map)
        dt_clusters = MarkerCluster().add_to(v_map)
        draw_elements(df_substations=df_dt, v_icon='home', v_color='green', v_map=dt_clusters)
        v_map.save("map.html")
        print("Done! Open map.html in your browser.")
    finally: 
        conn.close()