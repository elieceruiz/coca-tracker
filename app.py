import streamlit as st
from datetime import datetime
from pymongo import MongoClient
import pytz
import requests
import pandas as pd
from dateutil.relativedelta import relativedelta
import time

# === CONFIGURACIÓN INICIAL ===
st.set_page_config("🥤 Coca-Tracker", layout="centered")
st.title("🥤 Coca-Tracker")
tz = pytz.timezone("America/Bogota")

# === CONEXIÓN A MONGO ===
client = MongoClient(st.secrets["mongo_uri"])
db = client["coca_tracker"]
ingresos = db["ingresos"]
consumos = db["consumos"]

# === FUNCIONES ===
def obtener_ip():
    try:
        return requests.get("https://api.ipify.org").text
    except:
        return "desconocida"

def registrar_ingreso_si_es_primero():
    if ingresos.count_documents({}) == 0:
        ip = obtener_ip()
        doc = {"ip": ip, "fecha": datetime.now(tz)}
        ingresos.insert_one(doc)
        st.success("👣 Primer ingreso registrado.")
    else:
        st.info("Ingreso ya registrado anteriormente.")

def registrar_consumo():
    ahora = datetime.now(tz)
    consumos.insert_one({"fecha": ahora})
    st.success(f"✅ Consumo registrado a las {ahora.strftime('%H:%M:%S')}")

def obtener_base_tiempo():
    ultimo_consumo = consumos.find_one(sort=[("fecha", -1)])
    if ultimo_consumo:
        return ultimo_consumo["fecha"]
    else:
        primer_ingreso = ingresos.find_one(sort=[("fecha", 1)])
        return primer_ingreso["fecha"] if primer_ingreso else None

def cronometro(base):
    st.markdown("### ⏱️ Tiempo sin consumir")
    while True:
        ahora = datetime.now(tz)
        delta = ahora - base
        detalle = relativedelta(ahora, base)
        tiempo = f"{detalle.years}a {detalle.months}m {detalle.days}d {detalle.hours}h {detalle.minutes}m {detalle.seconds}s"
        minutos = int(delta.total_seconds() // 60)

        st.metric("Duración", f"{minutos:,} min", tiempo)
        time.sleep(1)
        st.rerun()

def tabla_eventos(coleccion, label):
    datos = list(coleccion.find().sort("fecha", -1 if label == "Consumos" else 1))
    filas = []
    for i, doc in enumerate(datos):
        fecha = doc["fecha"].astimezone(tz)
        fila = {
            "N°": i + 1,
            "Fecha": fecha.strftime("%Y-%m-%d"),
            "Hora": fecha.strftime("%H:%M:%S")
        }
        if "ip" in doc:
            fila["IP"] = doc["ip"]
        filas.append(fila)
    df = pd.DataFrame(filas)
    st.subheader(f"📑 Historial de {label}")
    st.dataframe(df, use_container_width=True, hide_index=True)

# === EJECUCIÓN PRINCIPAL ===
registrar_ingreso_si_es_primero()

st.markdown("### ¿Consumiste Coca-Cola?")
if st.button("☠️ Registrar consumo"):
    registrar_consumo()

# === CRONÓMETRO AL SEGUNDO ===
base = obtener_base_tiempo()
if base:
    cronometro(base)
else:
    st.warning("Aún no hay datos para calcular el tiempo sin consumir.")

# === HISTORIALES ===
with st.expander("📂 Ver historial completo"):
    tabla_eventos(ingresos, "Ingresos")
    tabla_eventos(consumos, "Consumos")