import streamlit as st
from datetime import datetime
import pytz
import time
import requests
from pymongo import MongoClient
from streamlit_javascript import st_javascript
from dateutil.parser import parse
from bson.objectid import ObjectId

# === CONFIG ===
st.set_page_config(page_title="📸 Registro de Azúcar", layout="centered")
tz = pytz.timezone("America/Bogota")
st.title("📸 Registro de Azúcar")

# === RECARGA SUAVE DESPUÉS DE REGISTRO ===
if st.query_params.get("refrescar"):
    st.experimental_set_query_params()
    st.rerun()

# === CONEXIÓN A MONGO ===
client = MongoClient(st.secrets["mongo_uri"])
db = client["registro_azucar"]
col_consumos = db["consumos"]
col_ingresos = db["ingresos"]

# === FUNCIONES IP Y CIUDAD ===
def obtener_ip_navegador():
    js_code = "await fetch('https://api64.ipify.org?format=json').then(res => res.json()).then(data => data.ip)"
    return st_javascript(js_code=js_code, key="ip_nav")

def obtener_ciudad(ip):
    try:
        res = requests.get(f"http://ip-api.com/json/{ip}", timeout=5).json()
        return res.get("city", "CIUDAD_DESCONOCIDA")
    except:
        return "CIUDAD_DESCONOCIDA"

# === REGISTRO DE INGRESO (UNA VEZ POR SESIÓN) ===
if "ingreso_registrado" not in st.session_state:
    ip_real = obtener_ip_navegador()
    ciudad = obtener_ciudad(ip_real) if ip_real else "CIUDAD_DESCONOCIDA"
    fecha_ingreso = datetime.now(pytz.utc)
    col_ingresos.insert_one({
        "timestamp": fecha_ingreso,
        "ip": ip_real,
        "ciudad": ciudad
    })
    st.session_state["ingreso_registrado"] = {
        "ciudad": ciudad,
        "fecha": fecha_ingreso
    }

# Mostrar entrada discreta
if isinstance(st.session_state["ingreso_registrado"], dict):
    ingreso = st.session_state["ingreso_registrado"]
    ciudad = ingreso["ciudad"]
    local = ingreso["fecha"].astimezone(tz).strftime("%Y-%m-%d %H:%M:%S")
    st.caption(f"📍 Ingresaste desde **{ciudad}** el {local}")

# === ÚLTIMO CONSUMO Y RACHA ===
ultimo = col_consumos.find_one(sort=[("fecha", -1)])
if ultimo:
    fecha_ultima = ultimo["fecha"]
    if isinstance(fecha_ultima, str):
        fecha_ultima = parse(fecha_ultima)
    ahora = datetime.now(pytz.utc)
    delta = ahora - fecha_ultima if fecha_ultima.tzinfo else ahora - pytz.utc.localize(fecha_ultima)
    total_segundos = int(delta.total_seconds())
    horas = total_segundos // 3600
    minutos = (total_segundos % 3600) // 60
    segundos = total_segundos % 60
    st.metric("⏳ Tiempo desde el último consumo", f"{horas:02}:{minutos:02}:{segundos:02}")
    time.sleep(1)
    st.rerun()

    # Barra de progreso hacia 21 días
    dias = delta.total_seconds() / 86400
    porcentaje = min(dias / 21, 1.0)
    st.progress(porcentaje, text=f"🌱 Progreso hacia 21 días sin consumir: {dias:.1f} días")

# === HISTORIAL CON CHECKBOX PARA CONTRAER ===
st.markdown("## 📷 Registros anteriores")

mostrar_historial = st.checkbox("Mostrar historial completo", value=False)

if mostrar_historial:
    consumos = list(col_consumos.find().sort("fecha", -1))
    if consumos:
        for idx, doc in enumerate(consumos, 1):
            st.markdown(f"### {idx}. {doc.get('comentario', 'Sin comentario')}")
            st.image(doc["foto_bytes"], caption=f"{doc['foto_nombre']} - {doc['ciudad']}", width=300)
            fecha_str = doc["fecha"]
            if isinstance(fecha_str, str):
                fecha_str = parse(fecha_str)
            fecha_local = fecha_str.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S")
            st.markdown(f"📅 {fecha_local}")
            borrar = st.button(f"🗑 Eliminar este registro", key=str(doc["_id"]))
            if borrar:
                col_consumos.delete_one({"_id": ObjectId(doc["_id"])})
                st.warning("Registro eliminado.")
                st.experimental_rerun()
    else:
        st.info("🔍 No hay consumos registrados aún.")
else:
    st.caption("☝🏽 Marca la casilla si quieres ver el historial completo.")

# === FORMULARIO DE REGISTRO ===
st.markdown("## 🍭 Nuevo consumo de azúcar")
foto = st.file_uploader("📷 Sube una foto del producto", type=["jpg", "jpeg", "png"])
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
        st.success(f"☠️ Consumo registrado desde {ciudad} a las {fecha_actual.astimezone(tz).strftime('%H:%M:%S')}")
        st.balloons()
        st.experimental_set_query_params(refrescar="1")
        st.stop()
    else:
        st.error("⚠️ Debes subir una foto para registrar el consumo.")