import streamlit as st
from datetime import datetime, timezone
from pymongo import MongoClient
import pandas as pd
import pytz
import time
import requests

# === CONFIGURACIÓN GENERAL ===
st.set_page_config(page_title="Coca Tracker", layout="centered")
st.title("💀 Tiempo sin consumir")
tz = pytz.timezone("America/Bogota")

# === CONEXIÓN A MONGO ===
client = MongoClient(st.secrets["mongo_uri"])
db = client["coca_tracker"]
col_consumos = db["consumos"]
col_ingresos = db["ingresos"]

# === REGISTRO DE INGRESO CON IP Y CIUDAD (solo una vez por sesión) ===
def obtener_ip_y_ciudad():
    try:
        res = requests.get("https://ipinfo.io/json")
        data = res.json()
        return data.get("ip", "N/A"), data.get("city", "N/A")
    except:
        return "N/A", "N/A"

if "ingreso_registrado" not in st.session_state:
    ip, ciudad = obtener_ip_y_ciudad()
    col_ingresos.insert_one({
        "fecha": datetime.utcnow(),
        "ip": ip,
        "ciudad": ciudad
    })
    st.session_state["ingreso_registrado"] = True

# === PESTAÑAS PRINCIPALES ===
tab1, tab2 = st.tabs(["⏱ Cronómetro", "📜 Historial de ingresos"])

with tab1:
    # Obtener último consumo o primer ingreso
    ultimo_consumo = col_consumos.find_one(sort=[("fecha", -1)])
    if ultimo_consumo:
        inicio = ultimo_consumo["fecha"].replace(tzinfo=timezone.utc).astimezone(tz)
    else:
        primer_ingreso = col_ingresos.find_one(sort=[("fecha", 1)])
        inicio = primer_ingreso["fecha"].replace(tzinfo=timezone.utc).astimezone(tz) if primer_ingreso else datetime.now(tz)

    # Botón registrar consumo
    if st.button("💀 Registrar consumo"):
        col_consumos.insert_one({"fecha": datetime.utcnow()})
        st.success("Registro guardado.")
        st.rerun()

    # Cronómetro en tiempo real
    st.markdown("⏳ **Tiempo transcurrido**")
    segundos_transcurridos = int((datetime.now(tz) - inicio).total_seconds())
    reloj_placeholder = st.empty()

    while True:
        tiempo = time.strftime("%H:%M:%S", time.gmtime(segundos_transcurridos))
        reloj_placeholder.markdown(f"### {tiempo}")
        time.sleep(1)
        segundos_transcurridos += 1

with tab2:
    registros = list(col_ingresos.find().sort("fecha", -1))
    if registros:
        df = pd.DataFrame(registros)
        df["fecha"] = pd.to_datetime(df["fecha"]).dt.tz_localize("UTC").dt.tz_convert("America/Bogota")
        df["fecha"] = df["fecha"].dt.strftime("%Y-%m-%d %H:%M:%S")
        df = df[["fecha", "ip", "ciudad"]]
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Aún no hay ingresos registrados.")