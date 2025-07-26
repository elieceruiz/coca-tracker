import streamlit as st
from pymongo import MongoClient
from datetime import datetime
import pytz
import pandas as pd
import requests
import time

# CONFIG
st.set_page_config(page_title="coca-tracker", layout="centered")
st.title("🥤 coca-\ntracker")

# ZONA HORARIA
colombia = pytz.timezone("America/Bogota")

# CONEXIÓN MONGO
client = MongoClient(st.secrets["mongo_uri"])
db = client["coca_tracker"]
consumos = db["consumos"]
ingresos = db["ingresos"]

# IP USUARIO
ip = requests.get("https://api.ipify.org").text

# REGISTRAR INGRESO SI NO EXISTE
if ingresos.count_documents({"ip": ip}) == 0:
    ingresos.insert_one({"ip": ip, "fecha": datetime.now(colombia)})

# OBTENER FECHA DE REFERENCIA
ultimo_consumo = consumos.find_one(sort=[("fecha", -1)])
primer_ingreso = ingresos.find_one(sort=[("fecha", 1)])

if ultimo_consumo:
    fecha_inicio = ultimo_consumo["fecha"]
else:
    fecha_inicio = primer_ingreso["fecha"] if primer_ingreso else None

# MENÚ
opcion = st.selectbox("¿Qué querés hacer?", ["Registrar consumo", "Historial completo"])

# === REGISTRO DE CONSUMO ===
if opcion == "Registrar consumo":
    st.subheader("💀 Registrar consumo")
    if st.button("🧊 Registrar consumo"):
        consumos.insert_one({"fecha": datetime.now(colombia)})
        st.success("¡Consumo registrado!")

    st.markdown("## ⏱ Tiempo sin consumir")

    if fecha_inicio:
        while True:
            now = datetime.now(colombia)
            duracion_segundos = int((now - fecha_inicio).total_seconds())

            dias = duracion_segundos // 86400
            horas = (duracion_segundos % 86400) // 3600
            minutos = (duracion_segundos % 3600) // 60
            segundos = duracion_segundos % 60

            st.metric("Duración", f"{minutos} min", f"↑ {dias}a {horas}h {minutos}m {segundos}s")
            st.markdown(f"🔴 Desde: {fecha_inicio.strftime('%Y-%m-%d %H:%M:%S')}")
            time.sleep(1)
            st.rerun()
    else:
        st.warning("No hay datos para calcular el tiempo.")

# === HISTORIAL COMPLETO ===
elif opcion == "Historial completo":
    st.header("📒 Historial completo")

    st.subheader("📋 Ingresos registrados")
    datos_ingresos = list(ingresos.find().sort("fecha", -1))
    if datos_ingresos:
        df = pd.DataFrame(datos_ingresos)
        df["_id"] = None
        df = df[["ip", "fecha"]]
        df.columns = ["IP", "Fecha y hora"]
        df["#"] = range(1, len(df) + 1)
        df = df[["#", "IP", "Fecha y hora"]]
        st.dataframe(df)
    else:
        st.info("No hay ingresos registrados.")

    st.subheader("🥤 Consumos registrados")
    datos_consumos = list(consumos.find().sort("fecha", -1))
    if datos_consumos:
        df_c = pd.DataFrame(datos_consumos)
        df_c["_id"] = None
        df_c.columns = ["_", "Fecha y hora"]
        df_c["#"] = range(1, len(df_c) + 1)
        df_c = df_c[["#", "Fecha y hora"]]
        st.dataframe(df_c)
    else:
        st.info("No hay consumos registrados.")