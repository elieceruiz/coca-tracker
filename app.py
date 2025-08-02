import streamlit as st
from datetime import datetime
import pytz
import time
from pymongo import MongoClient
from streamlit_javascript import st_javascript
from dateutil.parser import parse
from bson.objectid import ObjectId

# === CONFIGURACIÓN ===
st.set_page_config(page_title="📸 Registro de Azúcar", layout="wide")
st.title("📸 Registro de Azúcar")
tz = pytz.timezone("America/Bogota")

# === CONEXIÓN A MONGO ===
client = MongoClient(st.secrets["mongo_uri"])
db = client["registro_azucar"]
col_consumos = db["consumos"]

# === MENÚ LATERAL ===
st.sidebar.markdown("## 📂 Menú")
if st.sidebar.button("📥 Registrar consumo"):
    st.session_state["menu"] = "registro"
if st.sidebar.button("🧾 Ver historial"):
    st.session_state["menu"] = "historial"
if "menu" not in st.session_state:
    st.session_state["menu"] = "registro"

# === VISTA: REGISTRO ===
if st.session_state["menu"] == "registro":
    st.subheader("🍭 Nuevo consumo de azúcar")
    foto = st.file_uploader("📷 Sube una foto del producto", type=["jpg", "jpeg", "png"])
    comentario = st.text_input("📝 Comentario (opcional)")

    if st.button("💀 Registrar consumo"):
        if foto:
            col_consumos.insert_one({
                "fecha": datetime.now(pytz.utc),
                "comentario": comentario,
                "foto_nombre": foto.name,
                "foto_bytes": foto.getvalue()
            })
            st.success("☠️ Consumo registrado")
            st.balloons()
            st.rerun()
        else:
            st.error("⚠️ Debes subir una foto para registrar el consumo.")

    # === CRONÓMETRO Y PROGRESO ===
    ultimo = col_consumos.find_one(sort=[("fecha", -1)])
    if ultimo:
        fecha_ultima = ultimo["fecha"]
        if isinstance(fecha_ultima, str):
            fecha_ultima = parse(fecha_ultima)
        if fecha_ultima.tzinfo is None:
            fecha_ultima = pytz.utc.localize(fecha_ultima)

        ahora = datetime.now(pytz.utc)
        delta = ahora - fecha_ultima
        total_segundos = int(delta.total_seconds())
        horas = total_segundos // 3600
        minutos = (total_segundos % 3600) // 60
        segundos = total_segundos % 60
        st.metric("⏳ Tiempo desde el último consumo", f"{horas:02}:{minutos:02}:{segundos:02}")
        time.sleep(1)
        st.rerun()

        dias = delta.total_seconds() / 86400
        progreso = min(dias / 21, 1.0)
        st.progress(progreso, text=f"🌱 Hacia 21 días sin consumir: {dias:.1f} días")

# === VISTA: HISTORIAL ===
elif st.session_state["menu"] == "historial":
    st.subheader("📷 Historial de consumos")
    consumos = list(col_consumos.find().sort("fecha", -1))
    if consumos:
        for idx, doc in enumerate(consumos, 1):
            comentario = doc.get("comentario", "Sin comentario")
            fecha = doc["fecha"]
            if isinstance(fecha, str):
                fecha = parse(fecha)
            fecha_local = fecha.astimezone(tz).strftime("%Y-%m-%d %H:%M:%S")

            with st.expander(f"{idx}. {comentario} – {fecha_local}"):
                st.image(doc["foto_bytes"], caption=doc["foto_nombre"], width=300)
                if st.button("🗑 Eliminar", key=str(doc["_id"])):
                    col_consumos.delete_one({"_id": ObjectId(doc["_id"])})
                    st.warning("Registro eliminado.")
                    st.rerun()
    else:
        st.info("No hay consumos registrados aún.")
