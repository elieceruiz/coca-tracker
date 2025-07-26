import streamlit as st
from pymongo import MongoClient
from datetime import datetime
import pytz
import requests
import time
import pandas as pd

# Configuración de página
st.set_page_config("⏱ Tiempo sin consumir", layout="centered")
st.title("⏱ Tiempo sin consumir")
tz = pytz.timezone("America/Bogota")

# Conexión a MongoDB
client = MongoClient(st.secrets["mongo_uri"])
db = client["coca_tracker"]
col_consumos = db["consumos"]
col_ingresos = db["ingresos"]

# Obtener IP actual
def obtener_ip():
    try:
        return requests.get("https://api.ipify.org").text
    except:
        return "ip_desconocida"

# Registrar ingreso único por día e IP
def registrar_ingreso_unico():
    ip_actual = obtener_ip()
    hoy = datetime.now(tz).date()
    ya_existe = col_ingresos.find_one({
        "ip": ip_actual,
        "fecha": {"$gte": datetime.combine(hoy, datetime.min.time(), tz)}
    })
    if not ya_existe:
        col_ingresos.insert_one({
            "ip": ip_actual,
            "fecha": datetime.now(tz)
        })

# Cronómetro que corre al segundo
def cronometro(base):
    placeholder = st.empty()
    while True:
        ahora = datetime.now(tz)
        delta = ahora - base
        segundos = int(delta.total_seconds())
        dias = segundos // 86400
        horas = (segundos % 86400) // 3600
        minutos = (segundos % 3600) // 60
        segundos_restantes = segundos % 60
        placeholder.markdown(
            f"**{dias} días, {horas:02d}:{minutos:02d}:{segundos_restantes:02d} sin consumir.**"
        )
        time.sleep(1)

# Obtener fechas
def obtener_ultimo_consumo():
    doc = col_consumos.find_one(sort=[("fecha", -1)])
    return doc["fecha"] if doc else None

def obtener_primer_ingreso():
    doc = col_ingresos.find_one(sort=[("fecha", 1)])
    return doc["fecha"] if doc else None

# Registrar consumo actual
if st.button("💀 Registrar consumo"):
    col_consumos.insert_one({
        "fecha": datetime.now(tz),
        "ip": obtener_ip()
    })
    st.success("Registro de consumo realizado correctamente.")
    st.rerun()

# Registrar ingreso diario por IP
registrar_ingreso_unico()

# Base del cronómetro
fecha_base = obtener_ultimo_consumo() or obtener_primer_ingreso()

if fecha_base:
    cronometro(fecha_base)
else:
    st.warning("Aún no hay registros de ingreso ni consumo.")

# Historial
st.subheader("📜 Historial")

tabs = st.tabs(["💀 Consumos", "📥 Ingresos"])

with tabs[0]:
    docs = list(col_consumos.find().sort("fecha", -1))
    if docs:
        df = pd.DataFrame([{
            "Fecha": doc["fecha"].astimezone(tz).strftime("%Y-%m-%d %H:%M:%S"),
            "IP": doc.get("ip", "desconocida")
        } for doc in docs])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No hay registros de consumo.")

with tabs[1]:
    docs = list(col_ingresos.find().sort("fecha", -1))
    if docs:
        df = pd.DataFrame([{
            "Fecha": doc["fecha"].astimezone(tz).strftime("%Y-%m-%d %H:%M:%S"),
            "IP": doc.get("ip", "desconocida")
        } for doc in docs])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No hay ingresos registrados.")