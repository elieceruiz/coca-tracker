import streamlit as st
from datetime import datetime
from pymongo import MongoClient
import pytz
import pandas as pd
import requests

# Configuración de la App
st.set_page_config(page_title="Coca Tracker", layout="centered")
st.markdown("<h1 style='text-align: center;'>💀 Tiempo sin consumir</h1>", unsafe_allow_html=True)

# Zona horaria
colombia = pytz.timezone("America/Bogota")
ahora = datetime.now(tz=colombia)

# Conexión a MongoDB
client = MongoClient(st.secrets["mongo_uri"])
db = client["coca_tracker"]
coleccion_consumos = db["consumos"]
coleccion_ingresos = db["ingresos"]

# Función para obtener IP y ciudad
def obtener_info_ip():
    try:
        r = requests.get("https://ipinfo.io/json", timeout=5)
        data = r.json()
        return data.get("ip", ""), data.get("city", "")
    except:
        return "", ""

# Registrar ingreso si no se ha registrado aún
if "ingreso_registrado" not in st.session_state:
    ip, ciudad = obtener_info_ip()
    coleccion_ingresos.insert_one({
        "timestamp": ahora,
        "ip": ip,
        "ciudad": ciudad
    })
    st.session_state["ingreso_registrado"] = True

# Obtener primer ingreso absoluto
primer_ingreso = coleccion_ingresos.find_one(sort=[("timestamp", 1)])
if primer_ingreso and "timestamp" in primer_ingreso:
    inicio = primer_ingreso["timestamp"].astimezone(colombia)
else:
    inicio = ahora  # fallback

# Obtener último consumo (si existe)
ultimo_consumo = coleccion_consumos.find_one(sort=[("timestamp", -1)])
if ultimo_consumo and "timestamp" in ultimo_consumo:
    inicio = max(inicio, ultimo_consumo["timestamp"].astimezone(colombia))

# Calcular tiempo transcurrido
diferencia = ahora - inicio
horas, resto = divmod(diferencia.seconds, 3600)
minutos, segundos = divmod(resto, 60)
tiempo_transcurrido = f"{diferencia.days*24 + horas:02}:{minutos:02}:{segundos:02}"

# Pestañas
tabs = st.tabs(["🕰 Cronómetro", "📜 Historial de ingresos"])

# Sección Cronómetro
with tabs[0]:
    if st.button("💀 Registrar consumo"):
        coleccion_consumos.insert_one({"timestamp": ahora})
        st.rerun()
    st.markdown(f"⏳ **{tiempo_transcurrido}**")

# Sección Historial
with tabs[1]:
    st.subheader("📜 Ingresos a la App")
    registros = list(coleccion_ingresos.find().sort("timestamp", -1))

    if registros:
        data = []
        for i, r in enumerate(registros, start=1):
            timestamp = r.get("timestamp")
            ts_local = timestamp.astimezone(colombia).strftime("%Y-%m-%d %H:%M:%S") if timestamp else "—"
            data.append({
                "N°": len(registros) - i + 1,
                "Fecha y hora": ts_local,
                "IP": r.get("ip", ""),
                "Ciudad": r.get("ciudad", "")
            })

        df_registros = pd.DataFrame(data)
        st.dataframe(df_registros, use_container_width=True)
    else:
        st.info("Aún no hay ingresos registrados.")