import streamlit as st
from datetime import datetime, timezone
from pymongo import MongoClient
import pytz
import pandas as pd
import requests
import time
from dateutil.relativedelta import relativedelta

# === CONFIGURACIÓN ===
st.set_page_config("🥤 coca-tracker", layout="centered")
st.title("🥤 coca-tracker")
tz = pytz.timezone("America/Bogota")

# === CONEXIÓN MONGO ===
client = MongoClient(st.secrets["mongo_uri"])
db = client["coca_tracker"]
ingresos_col = db["ingresos"]
consumos_col = db["consumos"]

# === REGISTRAR PRIMER INGRESO ===
def obtener_ip():
    try:
        return requests.get("https://api.ipify.org").text
    except:
        return "IP no disponible"

ip_actual = obtener_ip()
existe = ingresos_col.find_one({"ip": ip_actual})
if not existe:
    ingresos_col.insert_one({"ip": ip_actual, "fecha": datetime.now(tz=tz)})

# === DEFINIR FECHA BASE PARA EL CRONÓMETRO ===
ultimo_consumo = consumos_col.find_one(sort=[("fecha", -1)])
primer_ingreso = ingresos_col.find_one(sort=[("fecha", 1)])

if ultimo_consumo:
    fecha_base = ultimo_consumo["fecha"].astimezone(tz)
    fuente = "último consumo"
elif primer_ingreso:
    fecha_base = primer_ingreso["fecha"].astimezone(tz)
    fuente = "primer ingreso"
else:
    fecha_base = None
    fuente = None

# === CRONÓMETRO AL SEGUNDO ===
st.subheader("⏱ Tiempo desde " + (fuente if fuente else "N/A"))

if fecha_base:
    ahora = datetime.now(tz)
    delta = ahora - fecha_base
    detalle = relativedelta(ahora, fecha_base)
    minutos = int(delta.total_seconds() // 60)
    tiempo_str = f"{detalle.years}a {detalle.months}m {detalle.days}d {detalle.hours}h {detalle.minutes}m {detalle.seconds}s"
    st.metric("Duración", f"{minutos:,} min", tiempo_str)
    time.sleep(1)
    st.rerun()
else:
    st.info("No hay registros para iniciar el conteo.")

# === BOTÓN REGISTRAR CONSUMO ===
st.markdown("---")
st.subheader("💀 Registrar consumo de Coca-Cola")

if st.button("💀 Registrar consumo"):
    ahora = datetime.now(tz=tz)
    anterior = consumos_col.find_one(sort=[("fecha", -1)])
    doc = {"fecha": ahora}
    if anterior:
        delta = ahora - anterior["fecha"].astimezone(tz)
        segundos = int(delta.total_seconds())
        minutos, segundos = divmod(segundos, 60)
        horas, minutos = divmod(minutos, 60)
        dias = delta.days
        doc["desde_anterior"] = {
            "dias": dias,
            "horas": horas,
            "minutos": minutos,
            "segundos": segundos
        }
    consumos_col.insert_one(doc)
    st.success("Consumo registrado.")
    time.sleep(1)
    st.rerun()

# === HISTORIAL DE INGRESOS ===
st.markdown("---")
st.subheader("📍 Ingresos a la App")
ingresos = list(ingresos_col.find({}).sort("fecha", -1))
filas = []
for i, x in enumerate(ingresos):
    fecha = x["fecha"].astimezone(tz)
    filas.append({
        "N°": len(ingresos) - i,
        "IP": x.get("ip", "Desconocida"),
        "Fecha": fecha.strftime("%Y-%m-%d"),
        "Hora": fecha.strftime("%H:%M:%S")
    })
df_ingresos = pd.DataFrame(filas)
st.dataframe(df_ingresos, use_container_width=True)

# === HISTORIAL DE CONSUMOS ===
st.markdown("---")
st.subheader("📍 Historial de consumos")
consumos = list(consumos_col.find({}).sort("fecha", -1))
filas = []
for i, c in enumerate(consumos):
    fecha = c["fecha"].astimezone(tz)
    dur = c.get("desde_anterior")
    tiempo = f"{dur['dias']}d {dur['horas']}h {dur['minutos']}m {dur['segundos']}s" if dur else "-"
    filas.append({
        "N°": len(consumos) - i,
        "Fecha": fecha.strftime("%Y-%m-%d"),
        "Hora": fecha.strftime("%H:%M:%S"),
        "Desde el anterior": tiempo
    })
df_consumos = pd.DataFrame(filas)
st.dataframe(df_consumos, use_container_width=True)