import streamlit as st
from datetime import datetime
from pymongo import MongoClient
import pytz
import time
import requests
import pandas as pd

# === CONFIG ===
st.set_page_config("⏱ Tiempo sin consumir", layout="centered")
st.title("💀 Tiempo sin consumir")
tz = pytz.timezone("America/Bogota")

# === MONGO ===
client = MongoClient(st.secrets["mongo_uri"])
db = client["coca_tracker"]
col_consumos = db["consumos"]
col_ingresos = db["ingresos"]

# === IP ===
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

# === OBTENER FECHAS ===
def obtener_ultimo_consumo():
    doc = col_consumos.find_one(sort=[("fecha", -1)])
    return doc["fecha"] if doc and "fecha" in doc else None

def obtener_primer_ingreso():
    doc = col_ingresos.find_one(sort=[("fecha", 1)])
    return doc["fecha"] if doc and "fecha" in doc else None

# === CRONÓMETRO ===
def cronometro(base):
    ahora = datetime.now(tz)
    delta = ahora - base
    duracion_segundos = int(delta.total_seconds())
    horas = duracion_segundos // 3600
    minutos = (duracion_segundos % 3600) // 60
    segundos = duracion_segundos % 60
    st.metric("⏳ Tiempo transcurrido", f"{horas:02d}:{minutos:02d}:{segundos:02d}")
    time.sleep(1)
    st.rerun()

# === BOTÓN DE CONSUMO ===
if st.button("💀 Registrar consumo"):
    registrar_consumo()

# === FECHA BASE PARA CRONÓMETRO
fecha_consumo = obtener_ultimo_consumo()
fecha_ingreso = obtener_primer_ingreso()
fecha_base = fecha_consumo or fecha_ingreso

if fecha_base:
    cronometro(fecha_base)
else:
    st.warning("Aún no hay registros de ingreso ni consumo.")

# === REGISTRO DE INGRESO (una vez por sesión)
if "ingreso_registrado" not in st.session_state:
    registrar_ingreso()
    st.session_state["ingreso_registrado"] = True

# === HISTORIAL COMPLETO
with st.expander("📜 Historial de consumos"):
    historial = list(col_consumos.find().sort("fecha", -1))
    if historial:
        df = pd.DataFrame(historial)
        df["_id"] = df["_id"].astype(str)
        df["fecha"] = pd.to_datetime(df["fecha"]).dt.tz_convert(tz).dt.strftime("%Y-%m-%d %H:%M:%S")
        df.index = range(len(df), 0, -1)
        st.dataframe(df[["fecha"]], use_container_width=True)
    else:
        st.info("Sin consumos registrados.")

with st.expander("📥 Historial de ingresos"):
    ingresos = list(col_ingresos.find().sort("fecha", -1))
    if ingresos:
        df = pd.DataFrame(ingresos)
        df["_id"] = df["_id"].astype(str)
        df["fecha"] = pd.to_datetime(df["fecha"]).dt.tz_convert(tz).dt.strftime("%Y-%m-%d %H:%M:%S")
        df.index = range(len(df), 0, -1)
        st.dataframe(df[["fecha", "ip"]], use_container_width=True)
    else:
        st.info("Sin ingresos registrados.")