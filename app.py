import streamlit as st
from datetime import datetime
from pymongo import MongoClient
import pytz
import pandas as pd
import time
import requests

# === CONFIG ===
st.set_page_config(page_title="🥤 Seguimiento de Consumo – Coca-Cola", layout="centered")
st.title("🥤 Seguimiento de Consumo – Coca-Cola")
tz = pytz.timezone("America/Bogota")

# === DB CONNECTION ===
client = MongoClient(st.secrets["mongo_uri"])
db = client["bucle_coca"]
coleccion_eventos = db["eventos"]
coleccion_ingresos = db["ingresos"]

# === FUNCIONES ===
def obtener_ip():
    try:
        r = requests.get("https://api64.ipify.org?format=json", timeout=5)
        return r.json()["ip"]
    except:
        return "IP no disponible"

def registrar_ingreso(ip):
    if not coleccion_ingresos.find_one({"ip": ip}):
        coleccion_ingresos.insert_one({
            "ip": ip,
            "primer_ingreso": datetime.now(tz)
        })

def obtener_ingreso(ip):
    return coleccion_ingresos.find_one({"ip": ip})

def obtener_ultimo_consumo():
    return coleccion_eventos.find_one(sort=[("timestamp", -1)])

def calcular_duracion(inicio, fin):
    return str(fin - inicio).split(".")[0]

# === LÓGICA PRINCIPAL ===
ip = obtener_ip()
registrar_ingreso(ip)
ingreso = obtener_ingreso(ip)

if not ingreso:
    st.error("No se pudo registrar tu ingreso.")
    st.stop()

inicio_conteo = ingreso["primer_ingreso"].astimezone(tz)
ultimo_consumo = obtener_ultimo_consumo()

# Si hay consumo posterior al ingreso, usarlo como nuevo inicio de conteo
if ultimo_consumo and ultimo_consumo["timestamp"] > ingreso["primer_ingreso"]:
    inicio_conteo = ultimo_consumo["timestamp"].astimezone(tz)
    origen = "último consumo"
else:
    origen = "primer ingreso"

st.markdown(f"**El conteo parte desde tu {origen}:** {inicio_conteo.strftime('%Y-%m-%d %H:%M:%S')}")

cronometro = st.empty()
while True:
    ahora = datetime.now(tz)
    cronometro.metric("⏱ Tiempo transcurrido", calcular_duracion(inicio_conteo, ahora))
    time.sleep(1)

# === BOTÓN PARA REGISTRAR CONSUMO ===
if st.button("Registrar consumo de Coca-Cola 🟥"):
    coleccion_eventos.insert_one({"timestamp": datetime.now(tz)})
    st.success("✅ Consumo registrado")
    st.rerun()

# === HISTORIAL ===
eventos = list(coleccion_eventos.find().sort("timestamp", -1))
if eventos:
    registros = []
    for i in range(len(eventos)):
        actual = eventos[i]["timestamp"].astimezone(tz)
        anterior = eventos[i+1]["timestamp"].astimezone(tz) if i+1 < len(eventos) else None
        duracion = calcular_duracion(anterior, actual) if anterior else "-"
        registros.append({
            "#": len(eventos) - i,
            "Fecha y hora": actual.strftime('%Y-%m-%d %H:%M:%S'),
            "Desde el anterior": duracion
        })
    df = pd.DataFrame(registros)
    st.subheader("📋 Historial de consumos")
    st.dataframe(df, use_container_width=True)
else:
    st.info("No hay consumos registrados todavía.")