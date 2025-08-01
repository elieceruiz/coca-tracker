import streamlit as st
from datetime import datetime
import pytz
import time
import requests
import pandas as pd
from pymongo import MongoClient
from streamlit_javascript import st_javascript

# === CONFIGURACIÓN GENERAL ===
st.set_page_config(page_title="📸 Registro de Azúcar", layout="centered")
st.title("📸 Registro de Azúcar")
tz = pytz.timezone("America/Bogota")

# === CONEXIÓN A MONGO ===
client = MongoClient(st.secrets["mongo_uri"])
db = client["registro_azucar"]
col_consumos = db["consumos"]

# === FUNCIONES PARA IP Y CIUDAD ===
def obtener_ip_navegador():
    js_code = "await fetch('https://api64.ipify.org?format=json').then(res => res.json()).then(data => data.ip)"
    return st_javascript(js_code=js_code, key="ip_nav")

def obtener_ciudad(ip):
    try:
        res = requests.get(f"http://ip-api.com/json/{ip}", timeout=5).json()
        return res.get("city", "CIUDAD_DESCONOCIDA")
    except:
        return "CIUDAD_DESCONOCIDA"

# === CRONÓMETRO DE RACHA ===
def mostrar_racha(fecha_ultima):
    ahora = datetime.now(tz)
    delta = ahora - fecha_ultima
    total_segundos = int(delta.total_seconds())
    horas = total_segundos // 3600
    minutos = (total_segundos % 3600) // 60
    segundos = total_segundos % 60
    st.metric("⏳ Tiempo desde el último consumo", f"{horas:02}:{minutos:02}:{segundos:02}")
    time.sleep(1)
    st.rerun()

# === SECCIÓN DE REGISTRO ===
st.subheader("🍭 Nuevo consumo de azúcar")
with st.form("form_consumo"):
    foto = st.file_uploader("📷 Sube una foto del producto", type=["jpg", "jpeg", "png"])
    comentario = st.text_input("📝 Comentario (opcional)")
    enviar = st.form_submit_button("💀 Registrar consumo")

if enviar:
    if foto:
        ip_real = obtener_ip_navegador()
        ciudad = obtener_ciudad(ip_real) if ip_real else "CIUDAD_DESCONOCIDA"
        col_consumos.insert_one({
            "fecha": datetime.now(tz),
            "comentario": comentario,
            "ciudad": ciudad,
            "foto_nombre": foto.name,
            "foto_bytes": foto.getvalue()
        })
        st.success(f"☠️ Consumo registrado desde {ciudad}")
        st.rerun()
    else:
        st.error("⚠️ Debes subir una foto para registrar el consumo.")

# === RACHA EN TIEMPO REAL ===
ultimo = col_consumos.find_one(sort=[("fecha", -1)])
if ultimo:
    mostrar_racha(ultimo["fecha"])

# === HISTORIAL DE CONSUMOS ===
st.markdown("## 🧾 Historial de consumos")
consumos = list(col_consumos.find().sort("fecha", -1))
if consumos:
    for idx, doc in enumerate(consumos, 1):
        st.markdown(f"### {idx}. {doc.get('comentario', 'Sin comentario')}")
        st.image(doc["foto_bytes"], caption=f"{doc['foto_nombre']} - {doc['ciudad']} - {doc['fecha'].astimezone(tz).strftime('%Y-%m-%d %H:%M:%S')}", use_column_width=True)
else:
    st.info("No hay consumos registrados aún.")