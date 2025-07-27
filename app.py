import streamlit as st
from datetime import datetime
from pymongo import MongoClient
import pytz
import time
import requests
import pandas as pd

# === CONFIGURACIÓN GENERAL ===
st.set_page_config("⏱ Tiempo sin consumir", layout="centered")
st.title("💀 Tiempo sin consumir")
tz = pytz.timezone("America/Bogota")

# === CONEXIÓN A MONGODB ===
client = MongoClient(st.secrets["mongo_uri"])
db = client["coca_tracker"]
col_consumos = db["consumos"]
col_ingresos = db["ingresos"]

# === OBTENER IP PÚBLICA ===
def obtener_ip():
    try:
        return requests.get("https://api.ipify.org").text.strip()
    except:
        return "IP_DESCONOCIDA"

# === REGISTRAR INGRESO ===
def registrar_ingreso():
    ip = obtener_ip()
    col_ingresos.insert_one({
        "ip": ip,
        "fecha": datetime.now(tz)
    })
    st.success("Ingreso registrado.")

# === REGISTRAR CONSUMO ===
def registrar_consumo():
    col_consumos.insert_one({
        "fecha": datetime.now(tz)
    })
    st.error("☠️ Consumo registrado.")

# === OBTENER FECHAS BASE ===
def obtener_ultimo_consumo():
    doc = col_consumos.find_one(sort=[("fecha", -1)])
    return doc["fecha"] if doc and "fecha" in doc else None

def obtener_primer_ingreso():
    doc = col_ingresos.find_one(sort=[("fecha", 1)])
    return doc["fecha"] if doc and "fecha" in doc else None

# === BOTÓN DE CONSUMO ===
if st.button("💀 Registrar consumo"):
    registrar_consumo()

# === REGISTRO DE INGRESO UNA SOLA VEZ POR SESIÓN
if "ingreso_registrado" not in st.session_state:
    registrar_ingreso()
    st.session_state["ingreso_registrado"] = True

# === HISTORIAL DE CONSUMOS ===
with st.expander("📜 Historial de consumos"):
    historial = list(col_consumos.find().sort("fecha", -1))
    if historial:
        df = pd.DataFrame(historial)
        df["_id"] = df["_id"].astype(str)
        df["fecha"] = pd.to_datetime(df["fecha"]).dt.tz_localize(None)
        df["fecha"] = df["fecha"].dt.strftime("%Y-%m-%d %H:%M:%S")
        df.index = range(len(df), 0, -1)
        st.dataframe(df[["fecha"]], use_container_width=True)
    else:
        st.info("Sin consumos registrados.")

# === HISTORIAL DE INGRESOS ===
with st.expander("📥 Historial de ingresos"):
    ingresos = list(col_ingresos.find().sort("fecha", -1))
    if ingresos:
        df_ing = pd.DataFrame(ingresos)
        df_ing["_id"] = df_ing["_id"].astype(str)
        df_ing["ip"] = df_ing["ip"]
        df_ing["fecha"] = pd.to_datetime(df_ing["fecha"]).dt.tz_localize(None)
        df_ing["fecha"] = df_ing["fecha"].dt.strftime("%Y-%m-%d %H:%M:%S")
        df_ing.index = range(len(df_ing), 0, -1)
        st.dataframe(df_ing[["fecha", "ip"]], use_container_width=True)
    else:
        st.info("Sin ingresos registrados.")

# === CRONÓMETRO EN TIEMPO REAL AL SEGUNDO ===
fecha_base = obtener_ultimo_consumo() or obtener_primer_ingreso()
if isinstance(fecha_base, datetime):
    placeholder = st.empty()
    while True:
        ahora = datetime.now(tz)
        delta = ahora - fecha_base
        total_segundos = int(delta.total_seconds())
        horas = total_segundos // 3600
        minutos = (total_segundos % 3600) // 60
        segundos = total_segundos % 60
        with placeholder.container():
            st.metric("⏳ Tiempo transcurrido", f"{horas:02d}:{minutos:02d}:{segundos:02d}")
        time.sleep(1)
else:
    st.warning("Aún no hay registros de ingreso ni consumo.")