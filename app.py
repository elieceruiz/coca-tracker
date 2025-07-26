import streamlit as st
from datetime import datetime
from pymongo import MongoClient
import pytz
import pandas as pd
import time
import requests

# === CONFIGURACIÓN DE LA APP ===
st.set_page_config(page_title="🥤 coca-tracker", layout="centered")
st.title("🥤 coca-tracker")

# === ZONA HORARIA ===
tz = pytz.timezone("America/Bogota")

# === CONEXIÓN A BASE DE DATOS ===
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

# === INICIO DE LÓGICA PRINCIPAL ===
ip = obtener_ip()
registrar_ingreso(ip)
ingreso = obtener_ingreso(ip)

if not ingreso:
    st.error("No se pudo registrar tu ingreso.")
    st.stop()

# Mostrar IP actual e ingreso
st.markdown(f"**👤 Tu IP registrada:** `{ip}`")
st.markdown(f"**🕓 Primer ingreso:** {ingreso['primer_ingreso'].astimezone(tz).strftime('%Y-%m-%d %H:%M:%S')}")

# Determinar desde cuándo contar
inicio_conteo = ingreso["primer_ingreso"].astimezone(tz)
ultimo_consumo = obtener_ultimo_consumo()

if ultimo_consumo and ultimo_consumo["timestamp"] > ingreso["primer_ingreso"]:
    inicio_conteo = ultimo_consumo["timestamp"].astimezone(tz)
    origen = "último consumo"
else:
    origen = "primer ingreso"

st.markdown(f"**⏳ El conteo parte desde tu {origen}:** {inicio_conteo.strftime('%Y-%m-%d %H:%M:%S')}")

# Cronómetro
cronometro = st.empty()
now = datetime.now(tz)
elapsed = calcular_duracion(inicio_conteo, now)
cronometro.metric("⏱ Tiempo transcurrido", elapsed)

# === BOTÓN DE REGISTRO DE CONSUMO ===
if st.button("Registrar consumo de Coca-Cola 🟥"):
    coleccion_eventos.insert_one({"timestamp": datetime.now(tz)})
    st.success("✅ Consumo registrado correctamente")
    st.rerun()

# === HISTORIAL DE CONSUMOS ===
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
    st.subheader("📋 Historial de consumos")
    st.dataframe(pd.DataFrame(registros), use_container_width=True)
else:
    st.info("No hay consumos registrados todavía.")

# === HISTORIAL DE INGRESOS (ordenado del primero al último) ===
todos = list(coleccion_ingresos.find().sort("primer_ingreso", 1))
if todos:
    registros_ingreso = []
    for i, doc in enumerate(todos):
        registros_ingreso.append({
            "#": i + 1,
            "IP": doc["ip"],
            "Fecha y hora": doc["primer_ingreso"].astimezone(tz).strftime('%Y-%m-%d %H:%M:%S')
        })
    st.subheader("📒 Historial de ingresos")
    st.dataframe(pd.DataFrame(registros_ingreso), use_container_width=True)