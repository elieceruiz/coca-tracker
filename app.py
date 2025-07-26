import streamlit as st
from pymongo import MongoClient
from datetime import datetime
import pytz
import time
import pandas as pd
import requests

# Configuración
st.set_page_config(page_title="coca-tracker", layout="centered")
st.title("🥤 coca-\ntracker")

# Zona horaria
tz = pytz.timezone("America/Bogota")

# MongoDB
client = MongoClient(st.secrets["mongo_uri"])
db = client["coca_tracker"]
col_ingresos = db["ingresos"]
col_consumos = db["consumos"]

# Obtener IP del visitante
def obtener_ip():
    try:
        ip = requests.get('https://api.ipify.org').text
    except:
        ip = "0.0.0.0"
    return ip

ip_actual = obtener_ip()

# Registrar IP si no está
existe = col_ingresos.find_one({"ip": ip_actual})
if not existe:
    col_ingresos.insert_one({
        "ip": ip_actual,
        "fecha": datetime.now(tz)
    })

# Determinar punto de inicio del conteo
ultimo_consumo = col_consumos.find_one({"ip": ip_actual}, sort=[("fecha", -1)])
primer_ingreso = col_ingresos.find_one({"ip": ip_actual}, sort=[("fecha", 1)])

if ultimo_consumo:
    inicio = ultimo_consumo["fecha"]
else:
    inicio = primer_ingreso["fecha"]

# Mostrar tiempo transcurrido desde `inicio`
st.markdown("### ⏱️ Tiempo sin consumir")

duracion_segundos = int((datetime.now(tz) - inicio).total_seconds())
while True:
    dias = duracion_segundos // 86400
    horas = (duracion_segundos % 86400) // 3600
    minutos = (duracion_segundos % 3600) // 60
    segundos = duracion_segundos % 60
    st.metric("Duración", f"{minutos} min")
    st.success(f"🟢 + {dias}a {horas}h {minutos}m {segundos}s")
    st.error(f"🔴 Desde: {inicio.strftime('%Y-%m-%d %H:%M:%S')}")
    time.sleep(1)
    duracion_segundos += 1
    st.rerun()

# Registrar consumo
with st.expander("☠️ Registrar consumo"):
    if st.button("Registrar consumo"):
        col_consumos.insert_one({
            "ip": ip_actual,
            "fecha": datetime.now(tz)
        })
        st.success("✅ Consumo registrado. Reiniciando conteo...")
        time.sleep(1)
        st.rerun()

# Historial de ingresos
st.markdown("### 📋 Historial de ingresos")

ingresos = list(col_ingresos.find().sort("fecha", -1))
if ingresos:
    df_ingresos = pd.DataFrame(ingresos)[["ip", "fecha"]]
    df_ingresos.insert(0, "#", range(1, len(df_ingresos)+1))
    with st.expander("📄 Ingresos registrados", expanded=True):
        st.dataframe(df_ingresos, use_container_width=True)
else:
    st.info("Aún no hay ingresos registrados.")

# Historial de consumos
st.markdown("### 🧾 Historial de consumos")

consumos = list(col_consumos.find({"ip": ip_actual}).sort("fecha", -1))
if consumos:
    df_consumos = pd.DataFrame(consumos)[["fecha"]]
    df_consumos.insert(0, "#", range(1, len(df_consumos)+1))
    with st.expander("🍷 Consumos registrados", expanded=True):
        st.dataframe(df_consumos, use_container_width=True)
else:
    st.info("No hay consumos registrados aún.")