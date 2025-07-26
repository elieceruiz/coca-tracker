import streamlit as st
from pymongo import MongoClient
from datetime import datetime, timedelta
import pytz
import pandas as pd
import time
import requests

# === CONFIGURACIÓN INICIAL ===
st.set_page_config(page_title="coca-tracker", layout="centered")
st.markdown("# 🥤 **coca-**\n### tracker")

# Zona horaria Colombia
colombia = pytz.timezone("America/Bogota")

# Conexión MongoDB
client = MongoClient(st.secrets["mongo_uri"])
db = client["coca_tracker"]
consumos_col = db["consumos"]
ingresos_col = db["ingresos"]

# === REGISTRO DE INGRESO POR IP ===
ip = requests.get("https://api.ipify.org").text
ya_registrado = ingresos_col.find_one({"ip": ip})
if not ya_registrado:
    ingresos_col.insert_one({"ip": ip, "fecha": datetime.now(colombia)})

# === BOTÓN PARA REGISTRAR CONSUMO ===
if st.button("💀 Registrar consumo"):
    consumos_col.insert_one({"fecha": datetime.now(colombia)})
    st.rerun()

# === DEFINIR FECHA DE REFERENCIA PARA EL CRONÓMETRO ===
ultimo_consumo = consumos_col.find_one(sort=[("fecha", -1)])
primer_ingreso = ingresos_col.find_one(sort=[("fecha", 1)])

# Validación robusta
if ultimo_consumo and "fecha" in ultimo_consumo:
    fecha_inicio = ultimo_consumo["fecha"]
elif primer_ingreso and "fecha" in primer_ingreso:
    fecha_inicio = primer_ingreso["fecha"]
else:
    fecha_inicio = None

# === CRONÓMETRO TIEMPO SIN CONSUMIR ===
st.subheader("⏱️ Tiempo sin consumir")

if fecha_inicio:
    while True:
        duracion_segundos = int((datetime.now(colombia) - fecha_inicio).total_seconds())
        dias = duracion_segundos // 86400
        horas = (duracion_segundos % 86400) // 3600
        minutos = (duracion_segundos % 3600) // 60
        segundos = duracion_segundos % 60

        st.metric("Duración", f"{minutos} min", f"↑ {dias}d {horas}h {minutos}m {segundos}s")
        st.markdown(f"🔴 Desde: {fecha_inicio.strftime('%Y-%m-%d %H:%M:%S')}")
        time.sleep(1)
        st.rerun()
else:
    st.warning("No hay ingresos ni consumos registrados aún.")

# === HISTORIAL COMPLETO ===
with st.expander("📒 Historial completo", expanded=False):
    st.subheader("📋 Ingresos registrados")
    ingresos = list(ingresos_col.find().sort("fecha", -1))
    if ingresos:
        df_ingresos = pd.DataFrame(ingresos)
        df_ingresos["fecha"] = df_ingresos["fecha"].dt.strftime("%Y-%m-%d %H:%M:%S")
        df_ingresos.insert(0, "#", range(len(df_ingresos), 0, -1))
        df_ingresos = df_ingresos[["#", "ip", "fecha"]]
        st.dataframe(df_ingresos, use_container_width=True)
    else:
        st.info("No hay ingresos registrados aún.")

    st.subheader("📉 Consumos registrados")
    consumos = list(consumos_col.find().sort("fecha", -1))
    if consumos:
        df_consumos = pd.DataFrame(consumos)
        df_consumos["fecha"] = df_consumos["fecha"].dt.strftime("%Y-%m-%d %H:%M:%S")
        df_consumos.insert(0, "#", range(len(df_consumos), 0, -1))
        df_consumos = df_consumos[["#", "fecha"]]
        st.dataframe(df_consumos, use_container_width=True)
    else:
        st.success("No hay consumos registrados aún 🙌")