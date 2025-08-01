import streamlit as st
from datetime import datetime
import pytz
import time
import requests
import pandas as pd
from pymongo import MongoClient
from streamlit_javascript import st_javascript
from dateutil.parser import parse

# === CONFIG ===
st.set_page_config(page_title="📸 Registro de Azúcar", layout="centered")
st.title("📸 Registro de Azúcar")
tz = pytz.timezone("America/Bogota")

# === CONEXIÓN A MONGO ===
client = MongoClient(st.secrets["mongo_uri"])
db = client["registro_azucar"]
col_consumos = db["consumos"]

# === FUNCIONES ===
def obtener_ip_navegador():
    js_code = "await fetch('https://api64.ipify.org?format=json').then(res => res.json()).then(data => data.ip)"
    return st_javascript(js_code=js_code, key="ip_nav")

def obtener_ciudad(ip):
    try:
        res = requests.get(f"http://ip-api.com/json/{ip}", timeout=5).json()
        return res.get("city", "CIUDAD_DESCONOCIDA")
    except:
        return "CIUDAD_DESCONOCIDA"

def mostrar_racha(fecha_ultima):
    ahora = datetime.now(pytz.utc)
    if fecha_ultima.tzinfo is None:
        fecha_ultima = pytz.utc.localize(fecha_ultima)
    delta = ahora - fecha_ultima
    total_segundos = int(delta.total_seconds())
    horas = total_segundos // 3600
    minutos = (total_segundos % 3600) // 60
    segundos = total_segundos % 60
    st.metric("⏳ Tiempo desde el último consumo", f"{horas:02}:{minutos:02}:{segundos:02}")
    time.sleep(1)
    st.rerun()

# === FORMULARIO DE REGISTRO ===
st.subheader("🍭 Nuevo consumo de azúcar")

# HTML puro para evitar doble tap en móviles compatibles
st.markdown("""
<label for="file_input" style="font-weight:bold">📷 Sube una foto del producto:</label><br>
<input type="file" accept="image/*" capture="environment" id="file_input" style="margin-top:8px;margin-bottom:10px;">
""", unsafe_allow_html=True)

foto = st.file_uploader("📁 También puedes seleccionar desde archivos", type=["jpg", "jpeg", "png"])
comentario = st.text_input("📝 Comentario (opcional)")

if st.button("💀 Registrar consumo"):
    if foto:
        ip_real = obtener_ip_navegador()
        ciudad = obtener_ciudad(ip_real) if ip_real else "CIUDAD_DESCONOCIDA"
        fecha_actual = datetime.now(pytz.utc)
        col_consumos.insert_one({
            "fecha": fecha_actual,
            "comentario": comentario,
            "ciudad": ciudad,
            "foto_nombre": foto.name,
            "foto_bytes": foto.getvalue()
        })
        st.success(f"☠️ Consumo registrado desde {ciudad}")
        st.write("✅ DEBUG: Registro guardado en Mongo:", fecha_actual.isoformat())
        st.rerun()
    else:
        st.error("⚠️ Debes subir una foto para registrar el consumo.")

# === RACHA EN TIEMPO REAL ===
ultimo = col_consumos.find_one(sort=[("fecha", -1)])
if ultimo:
    fecha_ultima = ultimo["fecha"]
    if isinstance(fecha_ultima, str):
        fecha_ultima = parse(fecha_ultima)
    mostrar_racha(fecha_ultima)

# === HISTORIAL ===
st.markdown("## 🧾 Historial de consumos")
consumos = list(col_consumos.find().sort("fecha", -1))
if consumos:
    for idx, doc in enumerate(consumos, 1):
        fecha_str = doc["fecha"]
        if isinstance(fecha_str, str):
            fecha_str = parse(fecha_str)
        fecha_local = fecha_str.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S")
        st.markdown(f"### {idx}. {doc.get('comentario', 'Sin comentario')}")
        st.image(doc["foto_bytes"], caption=f"{doc['foto_nombre']} - {doc['ciudad']} - {fecha_local}", use_column_width=True)
else:
    st.info("No hay consumos registrados aún.")