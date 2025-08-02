# 🍬 Registro de Azúcar – App Streamlit

import streamlit as st
from datetime import datetime
import pytz
import time
import pandas as pd
from pymongo import MongoClient
from dateutil.relativedelta import relativedelta
from bson.objectid import ObjectId

# === CONFIG ===
st.set_page_config("🍬 Registro de Azúcar", layout="centered")
st.title("📸 Registro de Azúcar")
tz = pytz.timezone("America/Bogota")

# === CONEXIÓN A MONGO ===
client = MongoClient(st.secrets["mongo_uri"])
db = client["coca_tracker"]
col = db["ingresos"]

# === FUNCIONES ===
def obtener_ultimo_consumo():
    ultimo = col.find_one(sort=[("timestamp", -1)])
    return ultimo["timestamp"] if ultimo else None

def formatear_diferencia(t1, t2):
    delta = relativedelta(t1, t2)
    return f"{delta.years}a {delta.months}m {delta.days}d {delta.hours:02}:{delta.minutes:02}:{delta.seconds:02}"

def mostrar_cronometro():
    st.markdown("""
    <style>
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.01); }
        100% { transform: scale(1); }
    }
    .cronometro {
        font-size: 2em;
        padding: 1em;
        margin-top: 1em;
        border: 1px solid #555;
        border-radius: 16px;
        text-align: center;
        background-color: #222846;
        color: #fff;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        animation: pulse 2s infinite;
    }
    </style>
    """, unsafe_allow_html=True)

    placeholder = st.empty()
    while True:
        now = datetime.now(tz)
        ultimo = obtener_ultimo_consumo()
        if ultimo:
            ultimo = ultimo.astimezone(tz)
            texto = formatear_diferencia(now, ultimo)
        else:
            texto = "Sin registros previos"
        placeholder.markdown(f'<div class="cronometro">⏳ {texto}</div>', unsafe_allow_html=True)
        time.sleep(1)

# === MENÚ LATERAL ===
st.sidebar.title("📂 Menú")
opcion = st.sidebar.radio("Selecciona una opción:", ["📥 Registrar consumo", "📑 Ver historial"])
vista = "registro" if "Registrar" in opcion else "historial"

# === LÓGICA DE VISTA ===
if vista == "registro":
    st.subheader("🔍 Nuevo consumo de azúcar")

    archivo = st.file_uploader("📷 Sube una foto del producto", type=["jpg", "jpeg", "png"], label_visibility="visible")
    comentario = st.text_input("📜 Comentario (opcional)", max_chars=200)

    if st.button("📅 Registrar consumo"):
        now = datetime.now(tz)
        doc = {"timestamp": now, "comentario": comentario}
        if archivo:
            doc["foto"] = archivo.read()
        col.insert_one(doc)
        st.success("¡Consumo registrado!")
        st.rerun()

    mostrar_cronometro()

elif vista == "historial":
    st.subheader("📁 Historial de consumos")
    data = list(col.find().sort("timestamp", -1))

    for i, item in enumerate(data):
        with st.container():
            st.markdown("---")
            col1, col2 = st.columns([4, 1])
            with col1:
                fecha = item["timestamp"].astimezone(tz).strftime("%Y-%m-%d %H:%M:%S")
                st.markdown(f"🕒 **{fecha}**")
                if "comentario" in item and item["comentario"]:
                    st.markdown(f"📜 _{item['comentario']}_")
            with col2:
                if st.button("🗑️", key=f"del_{i}"):
                    col.delete_one({"_id": item["_id"]})
                    st.rerun()
            if "foto" in item:
                st.image(item["foto"], use_column_width=True)
