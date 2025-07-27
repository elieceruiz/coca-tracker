import streamlit as st
from datetime import datetime
import pytz
import time
import requests
from pymongo import MongoClient
import pandas as pd

# === CONFIG ===
st.set_page_config("Tiempo sin consumir", layout="centered")
st.title("💀 Tiempo sin consumir")
tz = pytz.timezone("America/Bogota")

# === MONGO ===
client = MongoClient(st.secrets["mongo_uri"])
db = client["coca_tracker"]
col_consumos = db["consumos"]
col_ingresos = db["ingresos"]

# === OBTENER IP Y CIUDAD ===
def obtener_ip_y_ciudad():
    try:
        data = requests.get("https://ipinfo.io/json", timeout=5).json()
        return data.get("ip", "Desconocida"), data.get("city", "Desconocida")
    except:
        return "IP_ERROR", "CIUDAD_ERROR"

# === REGISTRAR INGRESO (una vez por sesión) ===
if "ingreso_registrado" not in st.session_state:
    ip, ciudad = obtener_ip_y_ciudad()
    col_ingresos.insert_one({
        "ip": ip,
        "ciudad": ciudad,
        "fecha": datetime.utcnow()
    })
    st.session_state["ingreso_registrado"] = True

# === REGISTRAR CONSUMO ===
if st.button("💀 Registrar consumo"):
    col_consumos.insert_one({"fecha": datetime.utcnow()})
    st.error("☠️ Consumo registrado.")
    st.rerun()

# === DEFINIR FECHA BASE DEL CRONÓMETRO ===
ultimo_consumo = col_consumos.find_one(sort=[("fecha", -1)])
primer_ingreso = col_ingresos.find_one(sort=[("fecha", 1)])

if ultimo_consumo:
    fecha_base = ultimo_consumo["fecha"].replace(tzinfo=pytz.UTC).astimezone(tz)
elif primer_ingreso:
    fecha_base = primer_ingreso["fecha"].replace(tzinfo=pytz.UTC).astimezone(tz)
else:
    fecha_base = None

# === CRONÓMETRO ===
if fecha_base:
    marcador = st.empty()
    while True:
        ahora = datetime.now(tz)
        delta = ahora - fecha_base
        h, rem = divmod(delta.total_seconds(), 3600)
        m, s = divmod(rem, 60)
        tiempo = f"{int(h):02}:{int(m):02}:{int(s):02}"
        marcador.markdown(f"### ⏳ {tiempo}")
        time.sleep(1)
else:
    st.info("No hay registros aún. Ingresa o registra consumo.")

# === HISTORIAL DE CONSUMOS ===
with st.expander("📜 Historial de consumos"):
    registros = list(col_consumos.find().sort("fecha", -1))
    if registros:
        df = pd.DataFrame(registros)
        df["_id"] = df["_id"].astype(str)
        df["fecha"] = pd.to_datetime(df["fecha"]).dt.tz_convert(tz).dt.strftime("%Y-%m-%d %H:%M:%S")
        df.index = range(len(df), 0, -1)
        st.dataframe(df[["fecha"]], use_container_width=True)
    else:
        st.info("Sin consumos registrados.")

# === HISTORIAL DE INGRESOS ===
with st.expander("🧾 Ingresos a la App"):
    ingresos = list(col_ingresos.find().sort("fecha", -1))
    if ingresos:
        df = pd.DataFrame(ingresos)
        df["_id"] = df["_id"].astype(str)
        df["fecha"] = pd.to_datetime(df["fecha"]).dt.tz_convert(tz).dt.strftime("%Y-%m-%d %H:%M:%S")
        df.index = range(len(df), 0, -1)
        df["N°"] = df.index
        df = df[["N°", "fecha", "ip", "ciudad"]]
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Sin ingresos registrados.")