import streamlit as st
import pandas as pd
import pytz
import requests
from datetime import datetime
from pymongo import MongoClient
from streamlit_javascript import st_javascript

# === CONFIGURACIÓN GENERAL ===
st.set_page_config("💀 Tiempo sin consumir", layout="centered")
st.title("💀 Tiempo sin consumir")

# === CONEXIÓN A MONGO ===
client = MongoClient(st.secrets["mongo_uri"])
db = client["coca_tracker"]
ingresos = db["ingresos"]
consumos = db["consumos"]

# === ZONA HORARIA ===
tz = pytz.timezone("America/Bogota")

# === FUNCIONES DE IP Y CIUDAD ===
def obtener_ip_real():
    return st_javascript("await fetch('https://api.ipify.org?format=json').then(res => res.json()).then(data => data.ip)")

def obtener_ciudad(ip):
    try:
        r = requests.get(f"https://ipapi.co/{ip}/json/")
        return r.json().get("city", "Desconocida")
    except:
        return "Desconocida"

# === REGISTRAR INGRESO A LA APP ===
def registrar_ingreso():
    ip = obtener_ip_real()
    ciudad = obtener_ciudad(ip)
    ahora = datetime.now(tz)
    ingresos.insert_one({"timestamp": ahora, "ip": ip, "ciudad": ciudad})
    return ahora

# === TIEMPO DESDE EL PRIMER INGRESO ===
def calcular_tiempo_desde_ultimo_consumo():
    primer_ingreso = ingresos.find_one(sort=[("timestamp", 1)])
    ultimo_consumo = consumos.find_one(sort=[("timestamp", -1)])
    if not primer_ingreso:
        return "00:00:00"
    inicio = primer_ingreso["timestamp"]
    if ultimo_consumo and ultimo_consumo["timestamp"] > inicio:
        inicio = ultimo_consumo["timestamp"]
    ahora = datetime.now(tz)
    duracion = ahora - inicio
    return str(duracion).split(".")[0]

# === REGISTRAR CONSUMO ===
def registrar_consumo():
    ahora = datetime.now(tz)
    consumos.insert_one({"timestamp": ahora})

# === INTERFAZ STREAMLIT ===
tabs = st.tabs(["🕰 Cronómetro", "📜 Historial de ingresos"])

with tabs[0]:
    if st.button("💀 Registrar consumo"):
        registrar_consumo()
        st.rerun()

    st.markdown("⏳ **" + calcular_tiempo_desde_ultimo_consumo() + "**")

with tabs[1]:
    data = list(ingresos.find().sort("timestamp", -1))
    if not data:
        st.info("Aún no hay registros de ingreso.")
    else:
        df = pd.DataFrame(data)
        df["Fecha y hora"] = df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
        df = df[["Fecha y hora", "ip", "ciudad"]]
        st.dataframe(df, use_container_width=True)

# === REGISTRO AUTOMÁTICO DE INGRESO ===
if "registrado" not in st.session_state:
    registrar_ingreso()
    st.session_state.registrado = True