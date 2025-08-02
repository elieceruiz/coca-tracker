import streamlit as st
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pytz
import pandas as pd
from pymongo import MongoClient
from bson import ObjectId

# === CONFIGURACION ===
st.set_page_config("🍬 Registro de Azúcar", layout="centered")
st.title("📸 Registro de Azúcar")

# === CONEXION A MONGO ===
client = MongoClient(st.secrets["mongo_uri"])
db = client.azucar
col = db.consumos

# === ZONA HORARIA ===
tz = pytz.timezone("America/Bogota")

# === FUNCIONES ===
def tiempo_desde_ultimo():
    ultimo = col.find_one(sort=[("timestamp", -1)])
    if not ultimo:
        return "Nunca"
    ahora = datetime.now(tz)
    diferencia = relativedelta(ahora, ultimo["timestamp"])
    return f"{diferencia.years}a {diferencia.months}m {diferencia.days}d {diferencia.hours:02}:{diferencia.minutes:02}:{diferencia.seconds:02}"

def obtener_record():
    registros = list(col.find().sort("timestamp", 1))
    if len(registros) < 2:
        return "--"
    max_dif = relativedelta()
    for i in range(1, len(registros)):
        diff = relativedelta(registros[i]["timestamp"], registros[i-1]["timestamp"])
        if (diff.years, diff.months, diff.days, diff.hours, diff.minutes, diff.seconds) > (max_dif.years, max_dif.months, max_dif.days, max_dif.hours, max_dif.minutes, max_dif.seconds):
            max_dif = diff
    return f"{max_dif.years}a {max_dif.months}m {max_dif.days}d {max_dif.hours:02}:{max_dif.minutes:02}:{max_dif.seconds:02}"

def mostrar_cronometro():
    st.markdown("""
    <style>
    .cronometro {
        border-radius: 12px;
        background-color: #111;
        padding: 10px 20px;
        font-size: 32px;
        color: #39FF14;
        font-weight: bold;
        text-align: center;
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)
    st.markdown(f"""<div class='cronometro'>{tiempo_desde_ultimo()}</div>""", unsafe_allow_html=True)

# === QUERY PARAMS PARA MENU ===
view = st.query_params.get("view", "registro")

# === MENU ESTILO PERSONALIZADO ===
menu_style = """
<style>
.boton-menu {
    display: inline-block;
    width: 180px;
    padding: 0.5rem 1rem;
    margin: 0.5rem;
    font-size: 16px;
    font-weight: 600;
    text-align: center;
    border-radius: 12px;
    border: 2px solid;
    text-decoration: none;
}
.boton-registro {
    color: #ffffff !important;
    background-color: #4444aa;
    border-color: #4444aa;
}
.boton-registro:hover {
    background-color: #333388;
}
.boton-historial {
    color: #ff4444 !important;
    background-color: transparent;
    border-color: #ff4444;
}
.boton-historial:hover {
    background-color: #220000;
}
</style>
"""
st.markdown(menu_style, unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    st.markdown('<a class="boton-menu boton-registro" href="?view=registro">📥 Registrar consumo</a>', unsafe_allow_html=True)
with col2:
    st.markdown('<a class="boton-menu boton-historial" href="?view=historial">📑 Ver historial</a>', unsafe_allow_html=True)

# === REGISTRO ===
if view == "registro":
    st.subheader("🍭 Nuevo consumo de azúcar")
    archivo = st.file_uploader("📷 Sube una foto del producto", type=["jpg", "jpeg", "png"])
    comentario = st.text_input("📝 Comentario (opcional)")
    if st.button("💀 Registrar consumo"):
        doc = {"timestamp": datetime.now(tz)}
        if archivo:
            doc["foto"] = archivo.getvalue()
        if comentario:
            doc["comentario"] = comentario
        col.insert_one(doc)
        st.success("✅ Consumo registrado correctamente")
        st.rerun()
    st.markdown("⏳ **Tiempo desde el último consumo**")
    mostrar_cronometro()
    st.caption(f"🏅 Récord sin consumir: {obtener_record()}")

# === HISTORIAL ===
eliminar = st.query_params.get("eliminar")
if eliminar:
    col.delete_one({"_id": ObjectId(eliminar)})
    st.rerun()

if view == "historial":
    st.subheader("📑 Historial de consumos")
    registros = list(col.find().sort("timestamp", -1))
    for r in registros:
        st.markdown("---")
        cols = st.columns([1, 3])
        with cols[0]:
            if "foto" in r:
                st.image(r["foto"], use_column_width=True)
        with cols[1]:
            st.markdown(f"🕒 {r['timestamp'].astimezone(tz).strftime('%Y-%m-%d %H:%M:%S')}")
            if "comentario" in r:
                st.markdown(f"💬 _{r['comentario']}_")
            st.markdown(f"[🗑️ Eliminar](?view=historial&eliminar={r['_id']})")
