import streamlit as st
from datetime import datetime
from pymongo import MongoClient
import pytz
import pandas as pd
import requests
from dateutil.relativedelta import relativedelta
from streamlit_autorefresh import st_autorefresh

# === CONFIG ===
st.set_page_config(page_title="🥤 coca-tracker", layout="centered")
colombia = pytz.timezone("America/Bogota")

# === CONEXIÓN A BD ===
client = MongoClient(st.secrets["mongo_uri"])
db = client["bucle_coca"]
coleccion_eventos = db["eventos"]
coleccion_ingresos = db["ingresos"]

# === SELECTOR DE VISTA ===
opciones = {
    "🥤 Registrar consumo": "consumo",
    "📒 Historial completo": "historial"
}

st.title("🥤 coca-tracker")
seleccion = st.selectbox("¿Qué querés hacer?", list(opciones.keys()))
opcion = opciones[seleccion]

# === FUNCIONES ===
def obtener_ip():
    try:
        r = requests.get("https://api64.ipify.org?format=json", timeout=5)
        return r.json()["ip"]
    except:
        return "IP no disponible"

def registrar_ingreso(ip):
    if not coleccion_ingresos.find_one({"ip": ip}):
        coleccion_ingresos.insert_one({
            "ip": ip,
            "primer_ingreso": datetime.now(colombia)
        })

def obtener_ingreso(ip):
    return coleccion_ingresos.find_one({"ip": ip})

def obtener_ultimo_consumo():
    return coleccion_eventos.find_one(sort=[("timestamp", -1)])

def calcular_duracion(inicio, fin):
    delta = relativedelta(fin, inicio)
    return f"{delta.years}a {delta.months}m {delta.days}d {delta.hours}h {delta.minutes}m {delta.seconds}s"

# === INICIO DE SESIÓN ===
ip = obtener_ip()
registrar_ingreso(ip)
ingreso = obtener_ingreso(ip)
if not ingreso:
    st.error("No se pudo registrar tu ingreso.")
    st.stop()

# === VISTA: REGISTRAR CONSUMO ===
if opcion == "consumo":
    st.header("📍 Registrar consumo de Coca-Cola")

    st.markdown(f"**👤 Tu IP registrada:** `{ip}`")
    st.markdown(f"**🕓 Primer ingreso:** {ingreso['primer_ingreso'].astimezone(colombia).strftime('%Y-%m-%d %H:%M:%S')}")

    # Determinar desde dónde contar
    ultimo_consumo = obtener_ultimo_consumo()
    if ultimo_consumo:
        inicio_conteo = ultimo_consumo["timestamp"].astimezone(colombia)
        origen = "último consumo"
    else:
        inicio_conteo = ingreso["primer_ingreso"].astimezone(colombia)
        origen = "primer ingreso"

    st.markdown(f"**⏳ El conteo parte desde tu {origen}:** {inicio_conteo.strftime('%Y-%m-%d %H:%M:%S')}")

    # Cronómetro en tiempo real
    st_autorefresh(interval=1000, key="refresh")
    ahora = datetime.now(colombia)
    duracion = calcular_duracion(inicio_conteo, ahora)
    st.metric("🕒 Tiempo transcurrido", duracion)

    # Botón para registrar consumo
    if st.button("Registrar consumo de Coca-Cola 🟥"):
        coleccion_eventos.insert_one({"timestamp": datetime.now(colombia)})
        st.success("✅ Consumo registrado correctamente")
        st.rerun()

# === VISTA: HISTORIAL COMPLETO ===
elif opcion == "historial":
    st.header("📒 Historial completo")

    # Ingresos (orden descendente)
    ingresos = list(coleccion_ingresos.find().sort("primer_ingreso", -1))
    if ingresos:
        datos = []
        for i, doc in enumerate(ingresos):
            datos.append({
                "#": i + 1,
                "IP": doc["ip"],
                "Fecha y hora": doc["primer_ingreso"].astimezone(colombia).strftime("%Y-%m-%d %H:%M:%S")
            })
        st.subheader("📋 Ingresos registrados")
        st.dataframe(pd.DataFrame(datos), use_container_width=True, hide_index=True)
    else:
        st.info("No hay ingresos registrados aún.")

    # Consumos (orden descendente)
    eventos = list(coleccion_eventos.find().sort("timestamp", -1))
    if eventos:
        filas = []
        for i in range(len(eventos)):
            actual = eventos[i]["timestamp"].astimezone(colombia)
            anterior = eventos[i+1]["timestamp"].astimezone(colombia) if i+1 < len(eventos) else None
            if anterior:
                delta = relativedelta(actual, anterior)
                duracion = f"{delta.years}a {delta.months}m {delta.days}d {delta.hours}h {delta.minutes}m"
            else:
                duracion = "-"
            filas.append({
                "#": i + 1,
                "Fecha": actual.strftime("%Y-%m-%d"),
                "Hora": actual.strftime("%H:%M"),
                "Desde el anterior": duracion
            })
        st.subheader("📋 Consumos registrados")
        st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)
    else:
        st.info("No hay consumos registrados aún.")