import streamlit as st
from datetime import datetime
from pymongo import MongoClient
import pytz
import pandas as pd
from dateutil.relativedelta import relativedelta
import time

# === CONFIGURACIÓN GENERAL ===
st.set_page_config(page_title="Coca Tracker", layout="centered")
colombia = pytz.timezone("America/Bogota")

# === CONEXIÓN A MONGODB ===
client = MongoClient(st.secrets["mongo_uri"])
db = client["coca_tracker"]
coleccion_eventos = db["eventos"]
coleccion_metadata = db["app_metadata"]

# === REGISTRAR PRIMER INGRESO SI NO EXISTE ===
def registrar_primer_ingreso_si_no_existe():
    if not coleccion_metadata.find_one({"clave": "primer_ingreso"}):
        coleccion_metadata.insert_one({
            "clave": "primer_ingreso",
            "fecha": datetime.now(colombia)
        })

# === OBTENER PRIMER INGRESO GENERAL ===
def obtener_primer_ingreso():
    doc = coleccion_metadata.find_one({"clave": "primer_ingreso"})
    return doc["fecha"].astimezone(colombia) if doc else None

# === OBTENER ÚLTIMO CONSUMO ===
def obtener_ultimo_consumo():
    doc = coleccion_eventos.find_one(sort=[("timestamp", -1)])
    return doc["timestamp"].astimezone(colombia) if doc else None

# === REGISTRAR CONSUMO ===
def registrar_consumo():
    ahora = datetime.now(colombia)
    coleccion_eventos.insert_one({"timestamp": ahora})
    st.success(f"🍷 Consumo registrado a las {ahora.strftime('%H:%M:%S')}")

# === MOSTRAR CRONÓMETRO ===
def mostrar_cronometro():
    st.markdown("### ⏱️ Tiempo sin consumir")

    referencia = obtener_ultimo_consumo() or obtener_primer_ingreso()

    if referencia:
        ahora = datetime.now(colombia)
        delta = ahora - referencia
        detalle = relativedelta(ahora, referencia)
        minutos = int(delta.total_seconds() // 60)
        tiempo = f"{detalle.years}a {detalle.months}m {detalle.days}d {detalle.hours}h {detalle.minutes}m {detalle.seconds}s"

        st.metric("Duración", f"{minutos:,} min", tiempo)
        st.caption(f"🔴 Desde: {referencia.strftime('%Y-%m-%d %H:%M:%S')}")
        time.sleep(1)
        st.rerun()
    else:
        st.metric("Duración", "0 min")
        st.caption("0a 0m 0d 0h 0m 0s")

# === HISTORIAL DE CONSUMOS ===
def obtener_historial():
    eventos = list(coleccion_eventos.find().sort("timestamp", -1))
    filas = []
    total = len(eventos)
    for i, e in enumerate(eventos):
        fecha = e["timestamp"].astimezone(colombia)
        anterior = eventos[i + 1]["timestamp"].astimezone(colombia) if i + 1 < len(eventos) else None
        diferencia = ""
        if anterior:
            detalle = relativedelta(fecha, anterior)
            diferencia = f"{detalle.years}a {detalle.months}m {detalle.days}d {detalle.hours}h {detalle.minutes}m"
        filas.append({
            "N°": total - i,
            "Fecha": fecha.strftime("%Y-%m-%d"),
            "Hora": fecha.strftime("%H:%M"),
            "Duración sin consumir": diferencia
        })
    return pd.DataFrame(filas)

# === INICIO DE APP ===
registrar_primer_ingreso_si_no_existe()

st.title("🥤 coca-tracker")

# Botón para registrar consumo
if st.button("☠️ Registrar consumo"):
    registrar_consumo()

# Cronómetro
mostrar_cronometro()

# Historial desplegable
with st.expander("📑 Historial de consumos"):
    df = obtener_historial()
    st.dataframe(df, use_container_width=True, hide_index=True)