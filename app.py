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

# === REGISTRAR INGRESO SI AÚN NO EXISTE HOY PARA ESA IP ===
def registrar_ingreso_si_nuevo():
    ip = obtener_ip()
    ahora = datetime.now(tz)
    hoy = ahora.date()
    ya_existe = col_ingresos.find_one({
        "ip": ip,
        "fecha": {
            "$gte": datetime(hoy.year, hoy.month, hoy.day, tzinfo=tz),
            "$lt": datetime(hoy.year, hoy.month, hoy.day, 23, 59, 59, tzinfo=tz)
        }
    })
    if not ya_existe:
        col_ingresos.insert_one({"ip": ip, "fecha": ahora})

# === REGISTRAR CONSUMO ===
def registrar_consumo():
    col_consumos.insert_one({"fecha": datetime.now(tz)})
    st.error("☠️ Consumo registrado.")

# === OBTENER FECHAS ===
def obtener_ultimo_consumo():
    doc = col_consumos.find_one(sort=[("fecha", -1)])
    return doc["fecha"] if doc else None

def obtener_primer_ingreso():
    doc = col_ingresos.find_one(sort=[("fecha", 1)])
    return doc["fecha"] if doc else None

# === CRONÓMETRO (ACTUALIZA AL SEGUNDO) ===
def cronometro(base):
    placeholder = st.empty()
    while True:
        ahora = datetime.now(tz)
        delta = ahora - base
        duracion_segundos = int(delta.total_seconds())
        horas = duracion_segundos // 3600
        minutos = (duracion_segundos % 3600) // 60
        segundos = duracion_segundos % 60
        placeholder.metric("⏳ Tiempo transcurrido", f"{horas:02d}:{minutos:02d}:{segundos:02d}")
        time.sleep(1)
        st.rerun()

# === BOTÓN CONSUMO ===
if st.button("💀 Registrar consumo"):
    registrar_consumo()

# === REGISTRAR INGRESO UNA VEZ POR DÍA ===
if "ingreso_registrado" not in st.session_state:
    registrar_ingreso_si_nuevo()
    st.session_state["ingreso_registrado"] = True

# === CRONÓMETRO SI HAY DATOS ===
fecha_base = obtener_ultimo_consumo() or obtener_primer_ingreso()
if fecha_base:
    cronometro(fecha_base)
else:
    st.warning("Aún no hay registros de ingreso ni consumo.")

# === HISTORIAL DE CONSUMOS ===
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

# === HISTORIAL DE INGRESOS ===
with st.expander("🛬 Historial de ingresos"):
    ingresos = list(col_ingresos.find().sort("fecha", -1))
    if ingresos:
        df = pd.DataFrame(ingresos)
        df["_id"] = df["_id"].astype(str)
        df["fecha"] = pd.to_datetime(df["fecha"]).dt.tz_convert(tz).dt.strftime("%Y-%m-%d %H:%M:%S")
        df.index = range(len(df), 0, -1)
        st.dataframe(df[["fecha", "ip"]], use_container_width=True)
    else:
        st.info("Sin ingresos registrados.")