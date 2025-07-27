import streamlit as st
from datetime import datetime
import pytz
import time
import requests
from pymongo import MongoClient
import pandas as pd

# === CONFIGURACIÓN DE LA APP ===
st.set_page_config("⏱ Tiempo sin consumir", layout="centered")
st.title("💀 Tiempo sin consumir")
tz = pytz.timezone("America/Bogota")

# === CONEXIÓN A MONGODB ===
client = MongoClient(st.secrets["mongo_uri"])
db = client["coca_tracker"]
col_consumos = db["consumos"]
col_ingresos = db["ingresos"]

# === FUNCIÓN PARA OBTENER IP ===
def obtener_ip():
    try:
        return requests.get("https://api.ipify.org").text.strip()
    except:
        return "IP_DESCONOCIDA"

# === REGISTRAR INGRESO (SOLO UNA VEZ POR SESIÓN) ===
if "ingreso_registrado" not in st.session_state:
    col_ingresos.insert_one({
        "ip": obtener_ip(),
        "fecha": datetime.now(tz)
    })
    st.session_state["ingreso_registrado"] = True

# === BOTÓN PARA REGISTRAR CONSUMO ===
if st.button("💀 Registrar consumo"):
    col_consumos.insert_one({
        "fecha": datetime.now(tz)
    })
    st.error("☠️ Consumo registrado.")

# === OBTENER FECHA BASE PARA EL CRONÓMETRO ===
def obtener_fecha_base():
    ultimo_consumo = col_consumos.find_one(sort=[("fecha", -1)])
    if ultimo_consumo:
        return ultimo_consumo["fecha"]
    primer_ingreso = col_ingresos.find_one(sort=[("fecha", 1)])
    if primer_ingreso:
        return primer_ingreso["fecha"]
    return None

# === MOSTRAR CRONÓMETRO EN TIEMPO REAL ===
fecha_base = obtener_fecha_base()
if fecha_base:
    fecha_base = fecha_base.astimezone(tz)
    ahora = datetime.now(tz)
    delta = ahora - fecha_base
    segundos = int(delta.total_seconds())
    horas = segundos // 3600
    minutos = (segundos % 3600) // 60
    segundos_restantes = segundos % 60

    st.metric("⏳ Tiempo transcurrido", f"{horas:02}:{minutos:02}:{segundos_restantes:02}")
    time.sleep(1)
    st.rerun()
else:
    st.warning("No hay registros aún. Ingresá o registrá consumo.")

# === HISTORIAL DE CONSUMOS ===
with st.expander("📜 Historial de consumos"):
    registros = list(col_consumos.find().sort("fecha", -1))
    if registros:
        df = pd.DataFrame(registros)
        df["_id"] = df["_id"].astype(str)
        df["fecha"] = pd.to_datetime(df["fecha"]).dt.tz_convert(tz).dt.strftime("%Y-%m-%d %H:%M:%S")
        df.index = range(len(df), 0, -1)
        st.dataframe(df[["fecha"]], use_container_width=True)
    else:
        st.info("Sin consumos registrados.")

# === HISTORIAL DE INGRESOS ===
with st.expander("🧾 Ingresos a la App"):
    ingresos = list(col_ingresos.find().sort("fecha", -1))
    if ingresos:
        df_ing = pd.DataFrame(ingresos)
        df_ing["_id"] = df_ing["_id"].astype(str)
        df_ing["fecha"] = pd.to_datetime(df_ing["fecha"]).dt.tz_convert(tz).dt.strftime("%Y-%m-%d %H:%M:%S")
        df_ing.index = range(len(df_ing), 0, -1)
        st.dataframe(df_ing[["fecha", "ip"]], use_container_width=True)
    else:
        st.info("Sin ingresos registrados.")