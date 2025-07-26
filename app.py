import streamlit as st
from datetime import datetime
from pymongo import MongoClient
import pytz
import pandas as pd
import requests
import time

# === CONFIGURACIÓN ===
st.set_page_config("🥤 coca-tracker", layout="centered")
tz = pytz.timezone("America/Bogota")
st.markdown("## 🥤 coca-\n### tracker")

# === CONEXIÓN A BASE DE DATOS ===
client = MongoClient(st.secrets["mongo_uri"])
db = client["coca_tracker"]
consumos = db["consumos"]
ingresos = db["ingresos"]

# === REGISTRAR IP E INGRESO ===
def obtener_ip():
    try:
        ip = requests.get("https://api.ipify.org").text
        return ip
    except:
        return "Desconocida"

ip_usuario = obtener_ip()
ahora = datetime.now(tz)

# Verificar si la IP ya ha ingresado antes
registro_existente = ingresos.find_one({"ip": ip_usuario})

# Si no hay registro previo, registrar este ingreso
if not registro_existente:
    ingresos.insert_one({"ip": ip_usuario, "fecha_hora": ahora})

# Obtener primer ingreso general para esta IP
primer_ingreso_ip = ingresos.find_one({"ip": ip_usuario}, sort=[("fecha_hora", 1)])

# Obtener último consumo, si existe
ultimo_consumo = consumos.find_one(sort=[("fecha_hora", -1)])

# Establecer el inicio del conteo
if ultimo_consumo:
    inicio = ultimo_consumo["fecha_hora"]
else:
    inicio = primer_ingreso_ip["fecha_hora"] if primer_ingreso_ip else ahora

# === PANTALLA PRINCIPAL ===
opcion = st.selectbox("¿Qué querés hacer?", ["🥴 Registrar consumo", "📒 Historial completo"])

# === REGISTRAR CONSUMO ===
if opcion == "🥴 Registrar consumo":
    if st.button("💀 Registrar consumo"):
        consumos.insert_one({"fecha_hora": datetime.now(tz)})
        st.success("✅ Consumo registrado correctamente.")
        st.rerun()

    st.subheader("⏱️ Tiempo sin consumir")

    if inicio:
        while True:
            duracion_segundos = int((datetime.now(tz) - inicio).total_seconds())
            dias = duracion_segundos // 86400
            horas = (duracion_segundos % 86400) // 3600
            minutos = (duracion_segundos % 3600) // 60
            segundos = duracion_segundos % 60
            st.metric("Duración", f"{dias}d {horas}h {minutos}m {segundos}s")
            st.markdown(f"🟢 Desde: {inicio.strftime('%Y-%m-%d %H:%M:%S')}")
            time.sleep(1)
            st.rerun()

# === HISTORIAL COMPLETO ===
elif opcion == "📒 Historial completo":
    st.subheader("📋 Ingresos registrados")

    ingresos_cursor = ingresos.find().sort("fecha_hora", -1)
    ingresos_df = pd.DataFrame(ingresos_cursor)

    if not ingresos_df.empty:
        ingresos_df["fecha_hora"] = ingresos_df["fecha_hora"].dt.strftime('%Y-%m-%d %H:%M:%S')
        ingresos_df = ingresos_df[["ip", "fecha_hora"]]
        ingresos_df.insert(0, "#", range(1, len(ingresos_df) + 1))
        st.dataframe(ingresos_df, use_container_width=True)
    else:
        st.info("No hay ingresos registrados aún.")

    st.divider()
    st.subheader("📍 Consumos registrados")

    consumos_cursor = consumos.find().sort("fecha_hora", -1)
    consumos_df = pd.DataFrame(consumos_cursor)

    if not consumos_df.empty:
        consumos_df["fecha_hora"] = consumos_df["fecha_hora"].dt.strftime('%Y-%m-%d %H:%M:%S')
        consumos_df = consumos_df[["fecha_hora"]]
        consumos_df.insert(0, "#", range(1, len(consumos_df) + 1))
        st.dataframe(consumos_df, use_container_width=True)
    else:
        st.info("No hay consumos registrados aún.")