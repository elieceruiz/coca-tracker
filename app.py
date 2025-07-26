import streamlit as st
from datetime import datetime, timezone
from pymongo import MongoClient
import pytz
import requests
import time
import pandas as pd

# ==== CONFIGURACIÓN INICIAL ====
st.set_page_config(page_title="coca-tracker", layout="centered")
st.title("🥤 coca-\n**tracker**")
st.markdown("## ☠️ Registrar consumo")

# ==== BASE DE DATOS ====
client = MongoClient(st.secrets["mongo_uri"])
db = client["coca_tracker"]
col_ingresos = db["ingresos"]
col_consumos = db["consumos"]

# ==== ZONA HORARIA COLOMBIA ====
colombia = pytz.timezone("America/Bogota")

# ==== FUNCIÓN PARA OBTENER IP ====
def obtener_ip():
    try:
        response = requests.get("https://api.ipify.org?format=json", timeout=5)
        return response.json()["ip"]
    except:
        return "IP-desconocida"

# ==== REGISTRO DE INGRESO (solo si no existe en esta sesión) ====
if "registrado_ingreso" not in st.session_state:
    ip = obtener_ip()
    ahora = datetime.now(tz=colombia)
    col_ingresos.insert_one({"ip": ip, "fecha": ahora})
    st.session_state["registrado_ingreso"] = True

# ==== BOTÓN PARA REGISTRAR CONSUMO ====
if st.button("☠️ Registrar consumo"):
    ahora = datetime.now(tz=colombia)
    col_consumos.insert_one({"fecha": ahora})
    st.experimental_rerun()

# ==== OBTENER FECHA DE ÚLTIMO CONSUMO (si existe) ====
ultimo_consumo = col_consumos.find_one(sort=[("fecha", -1)])
fecha_inicio = None

if ultimo_consumo:
    fecha_inicio = ultimo_consumo["fecha"]
else:
    # No hay consumos, usar fecha del primer ingreso
    primer_ingreso = col_ingresos.find_one(sort=[("fecha", 1)])
    if primer_ingreso and "fecha" in primer_ingreso:
        fecha_inicio = primer_ingreso["fecha"]
    else:
        st.warning("No hay ingresos ni consumos registrados aún.")
        st.stop()

# ==== CALCULAR DURACIÓN EN TIEMPO REAL ====
st.markdown("## ⏱️ Tiempo sin consumir")

while True:
    ahora = datetime.now(tz=colombia)
    duracion_segundos = int((ahora - fecha_inicio).total_seconds())
    dias = duracion_segundos // 86400
    horas = (duracion_segundos % 86400) // 3600
    minutos = (duracion_segundos % 3600) // 60
    segundos = duracion_segundos % 60

    st.metric(
        label="Duración",
        value=f"{dias}d {horas}h {minutos}m {segundos}s",
        delta=f"+ {dias}d {horas}h {minutos}m {segundos}s"
    )
    st.caption(f"🔴 Desde: {fecha_inicio.strftime('%Y-%m-%d %H:%M:%S')}")
    time.sleep(1)
    st.rerun()

# ==== HISTORIAL COMPLETO ====
with st.expander("📕 Historial completo", expanded=True):
    st.markdown("### 📋 Ingresos registrados")
    ingresos = list(col_ingresos.find().sort("fecha", -1))
    if ingresos:
        df_ingresos = pd.DataFrame(ingresos)
        df_ingresos = df_ingresos[["ip", "fecha"]]
        df_ingresos["#"] = range(len(df_ingresos), 0, -1)
        df_ingresos = df_ingresos[["#", "ip", "fecha"]]
        st.dataframe(df_ingresos)
    else:
        st.success("No hay ingresos registrados aún.")

    st.markdown("### 📉 Consumos registrados")
    consumos = list(col_consumos.find().sort("fecha", -1))
    if consumos:
        df_consumos = pd.DataFrame(consumos)
        df_consumos["#"] = range(len(df_consumos), 0, -1)
        df_consumos = df_consumos[["#", "fecha"]]
        st.dataframe(df_consumos)
    else:
        st.success("No hay consumos registrados aún.")