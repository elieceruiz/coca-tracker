import streamlit as st
from datetime import datetime, timezone
from pymongo import MongoClient
import requests
import pytz
import time
import pandas as pd

# === CONFIGURACIÓN GENERAL ===
st.set_page_config(page_title="coca-tracker", layout="centered")
st.markdown("<h1 style='text-align: center;'>💀 Tiempo sin consumir</h1>", unsafe_allow_html=True)

# === ZONA HORARIA ===
colombia = pytz.timezone("America/Bogota")

# === CONEXIÓN A MONGO ===
client = MongoClient(st.secrets["mongo_uri"])
db = client["coca_tracker"]
coleccion_consumos = db["consumos"]
coleccion_ingresos = db["ingresos"]

# === FUNCIONES ===
def obtener_ip_ciudad():
    try:
        res = requests.get("https://ipinfo.io/json", timeout=3)
        data = res.json()
        return data.get("ip", ""), data.get("city", "")
    except:
        return "", ""

def registrar_ingreso():
    ip, ciudad = obtener_ip_ciudad()
    now = datetime.now(timezone.utc)
    coleccion_ingresos.insert_one({
        "timestamp": now,
        "ip": ip,
        "ciudad": ciudad
    })

def obtener_ultimo_consumo():
    doc = coleccion_consumos.find_one(sort=[("timestamp", -1)])
    return doc["timestamp"] if doc else None

def obtener_primer_ingreso():
    doc = coleccion_ingresos.find_one(sort=[("timestamp", 1)])
    return doc["timestamp"] if doc else None

def formatear_duracion(segundos):
    horas = segundos // 3600
    minutos = (segundos % 3600) // 60
    segundos = segundos % 60
    return f"{int(horas):02d}:{int(minutos):02d}:{int(segundos):02d}"

# === REGISTRAR INGRESO AUTOMÁTICO ===
registrar_ingreso()

# === NAVEGACIÓN ENTRE PESTAÑAS ===
tab1, tab2 = st.tabs(["⏱ Cronómetro", "📜 Historial de ingresos"])

# === TABLA HISTORIAL ===
with tab2:
    st.markdown("### 🧾 Ingresos a la App")
    registros = list(coleccion_ingresos.find().sort("timestamp", -1))
    if registros:
        data = []
        for i, r in enumerate(registros, start=1):
            ts_local = r["timestamp"].astimezone(colombia).strftime("%Y-%m-%d %H:%M:%S")
            data.append({
                "N°": len(registros) - i + 1,
                "Fecha y hora": ts_local,
                "IP": r.get("ip", ""),
                "Ciudad": r.get("ciudad", "")
            })
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No hay registros aún.")

# === CRONÓMETRO ===
with tab1:
    st.markdown("### ⏳ Tiempo transcurrido")

    primer_ingreso = obtener_primer_ingreso()
    ultimo_consumo = obtener_ultimo_consumo()

    if primer_ingreso and (not ultimo_consumo or primer_ingreso > ultimo_consumo):
        while True:
            now = datetime.now(timezone.utc)
            delta = now - primer_ingreso
            segundos = int(delta.total_seconds())
            tiempo = formatear_duracion(segundos)
            st.markdown(f"<h2 style='text-align: center;'>⏳ {tiempo}</h2>", unsafe_allow_html=True)
            time.sleep(1)
            st.rerun()
    else:
        st.warning("Registra un ingreso primero para iniciar el cronómetro.")

# === BOTÓN DE CONSUMO ===
st.markdown("##")
if st.button("💀 Registrar consumo"):
    now = datetime.now(timezone.utc)
    coleccion_consumos.insert_one({"timestamp": now})
    st.success("Consumo registrado correctamente.")
    st.rerun()