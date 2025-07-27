import streamlit as st
from datetime import datetime
import pytz
import time
import requests
import pandas as pd
from pymongo import MongoClient
from streamlit_javascript import st_javascript

# === CONFIG ===
st.set_page_config("⏱ Tiempo sin consumir", layout="centered")
st.title("💀 Tiempo sin consumir")
tz = pytz.timezone("America/Bogota")

# === MONGO CONNECTION ===
client = MongoClient(st.secrets["mongo_uri"])
db = client["coca_tracker"]
col_consumos = db["consumos"]
col_ingresos = db["ingresos"]

# === FUNCIONES IP y ciudad ===
def obtener_ip_navegador():
    js_code = "await fetch('https://api64.ipify.org?format=json').then(res => res.json()).then(data => data.ip)"
    return st_javascript(js_code=js_code, key="ip_nav")

def obtener_ciudad(ip):
    try:
        res = requests.get(f"http://ip-api.com/json/{ip}", timeout=5).json()
        return res.get("city", "CIUDAD_DESCONOCIDA")
    except:
        return "CIUDAD_DESCONOCIDA"

# === BASE para cronómetro ===
def obtener_fecha_base():
    ultimo = col_consumos.find_one(sort=[("fecha", -1)])
    if ultimo:
        return ultimo["fecha"]
    primero = col_ingresos.find_one(sort=[("timestamp", 1)])
    if primero:
        return primero["timestamp"]
    return None

# === CRONÓMETRO ===
def mostrar_cronometro(base):
    ahora = datetime.now(tz)
    delta = ahora - base
    total_segundos = int(delta.total_seconds())
    horas = total_segundos // 3600
    minutos = (total_segundos % 3600) // 60
    segundos = total_segundos % 60
    st.metric("⏳ Tiempo transcurrido", f"{horas:02}:{minutos:02}:{segundos:02}")
    time.sleep(1)
    st.rerun()

# === Registrar consumo ===
if st.button("💀 Registrar consumo"):
    col_consumos.insert_one({"fecha": datetime.now(tz)})
    st.error("☠️ Consumo registrado.")

# === Registrar ingreso si es la primera vez ===
if "ingreso_registrado" not in st.session_state:
    ip_real = obtener_ip_navegador()
    if ip_real:
        ciudad = obtener_ciudad(ip_real)
        col_ingresos.insert_one({
            "timestamp": datetime.now(tz),
            "ip": ip_real,
            "ciudad": ciudad
        })
        st.success(f"Ingreso registrado desde {ciudad} ({ip_real})")
        st.session_state["ingreso_registrado"] = True

# === Mostrar cronómetro si hay base ===
base = obtener_fecha_base()
if base:
    base = base.astimezone(tz)
    mostrar_cronometro(base)
else:
    st.warning("Aún no hay ingresos ni consumos registrados.")

# === HISTORIAL DE INGRESOS (LISTA COMPLETA) ===
st.markdown("## 🧾 Historial completo de ingresos")
ingresos = list(col_ingresos.find().sort("timestamp", -1))
if ingresos:
    df = pd.DataFrame(ingresos)
    df["_id"] = df["_id"].astype(str)
    df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.tz_convert(tz).dt.strftime("%Y-%m-%d %H:%M:%S")
    df.index = range(len(df), 0, -1)  # Enumeración descendente
    st.dataframe(df[["timestamp", "ip", "ciudad"]], use_container_width=True)
else:
    st.info("Sin ingresos registrados.")