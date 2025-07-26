import streamlit as st
from datetime import datetime, timezone
from pymongo import MongoClient
import pytz
import time

# --- CONFIGURACIÓN ---
st.set_page_config("🧃 coca-tracker", layout="centered")
st.title("🧃 coca-\ntracker")
col = st.container()

# --- CONEXIÓN A MONGODB ---
client = MongoClient(st.secrets["mongo_uri"])
db = client["coca_tracker"]
consumos_col = db["consumos"]
ingresos_col = db["ingresos"]

# --- FUNCIONES ---

def registrar_ingreso_si_es_primero():
    if ingresos_col.count_documents({}) == 0:
        ip = st.session_state.get("ip_address", "ip_desconocida")
        ingresos_col.insert_one({
            "ip": ip,
            "fecha": datetime.now(timezone.utc)
        })

def obtener_base_tiempo():
    ultimo_consumo = consumos_col.find_one(sort=[("fecha", -1)])
    if ultimo_consumo:
        return ultimo_consumo["fecha"]
    primer_ingreso = ingresos_col.find_one(sort=[("fecha", 1)])
    if primer_ingreso:
        return primer_ingreso["fecha"]
    return None

def registrar_consumo():
    consumos_col.insert_one({"fecha": datetime.now(timezone.utc)})

def cronometro(base):
    st.subheader("⏱ Tiempo sin consumir")
    while True:
        ahora = datetime.now(timezone.utc)
        delta = ahora - base
        duracion_segundos = int(delta.total_seconds())
        horas, resto = divmod(duracion_segundos, 3600)
        minutos, segundos = divmod(resto, 60)
        st.metric("Tiempo", f"{horas:02}:{minutos:02}:{segundos:02}")
        time.sleep(1)
        st.rerun()

def mostrar_historial():
    st.subheader("📜 Historial")

    # --- HISTORIAL CONSUMOS ---
    consumos = list(consumos_col.find().sort("fecha", -1))
    if consumos:
        fechas = [c["fecha"].astimezone(pytz.timezone("America/Bogota")).strftime("%Y-%m-%d %H:%M:%S") for c in consumos]
        numeracion = list(range(len(fechas), 0, -1))
        st.markdown("**☠️ Consumos**")
        st.dataframe({"#": numeracion, "Fecha": fechas})
    else:
        st.info("No hay consumos registrados aún.")

    # --- HISTORIAL INGRESOS ---
    ingresos = list(ingresos_col.find().sort("fecha", -1))
    if ingresos:
        fechas = [i["fecha"].astimezone(pytz.timezone("America/Bogota")).strftime("%Y-%m-%d %H:%M:%S") for i in ingresos]
        ips = [i.get("ip", "desconocida") for i in ingresos]
        numeracion = list(range(len(fechas), 0, -1))
        st.markdown("**🚪 Ingresos**")
        st.dataframe({"#": numeracion, "IP": ips, "Fecha": fechas})
    else:
        st.info("No hay ingresos registrados aún.")

# --- REGISTRAR PRIMER INGRESO ---
registrar_ingreso_si_es_primero()

# --- BOTÓN PARA REGISTRAR CONSUMO ---
st.subheader("💀 Registrar consumo")
if st.button("💀 Registrar consumo"):
    registrar_consumo()
    st.success("Consumo registrado.")
    st.rerun()

# --- CRONÓMETRO ---
base = obtener_base_tiempo()
if base is not None:
    cronometro(base)
else:
    st.warning("⚠️ No se ha registrado ningún ingreso ni consumo aún.")

# --- HISTORIAL ---
mostrar_historial()