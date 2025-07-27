import streamlit as st
from datetime import datetime
from pymongo import MongoClient
import pytz
import time
import requests

# Configuración de la página
st.set_page_config(page_title="🧠 coca-tracker", layout="centered")
st.title("💀 Tiempo sin consumir")

# Zona horaria
colombia = pytz.timezone("America/Bogota")

# Conexión a MongoDB
client = MongoClient(st.secrets["mongo_uri"])
db = client["coca_tracker"]
coleccion_eventos = db["eventos"]
coleccion_ingresos = db["ingresos"]

# === Registrar ingreso a la App ===
def registrar_ingreso():
    try:
        ip_info = requests.get("https://ipinfo.io/json").json()
        ip = ip_info.get("ip", "Desconocida")
        ciudad = ip_info.get("city", "Desconocida")
    except:
        ip = "Error"
        ciudad = "Error"

    ingreso = {
        "fecha": datetime.utcnow(),
        "ip": ip,
        "ciudad": ciudad
    }
    coleccion_ingresos.insert_one(ingreso)

# Ejecutar solo una vez por sesión
if "ingreso_registrado" not in st.session_state:
    registrar_ingreso()
    st.session_state.ingreso_registrado = True

# === Obtener último evento ===
ultimo_evento = coleccion_eventos.find_one(sort=[("fecha", -1)])

if st.button("💀 Registrar consumo"):
    coleccion_eventos.insert_one({"fecha": datetime.utcnow()})
    st.success("Evento registrado. Racha reiniciada.")
    st.rerun()

# === Mostrar cronómetro de abstinencia ===
st.markdown("⏳ **Tiempo transcurrido**")

if ultimo_evento:
    fecha_evento = ultimo_evento["fecha"].replace(tzinfo=pytz.UTC).astimezone(colombia)

    marcador = st.empty()
    while True:
        ahora = datetime.now(colombia)
        delta = ahora - fecha_evento
        horas, rem = divmod(delta.total_seconds(), 3600)
        minutos, segundos = divmod(rem, 60)
        tiempo = f"{int(horas):02}:{int(minutos):02}:{int(segundos):02}"
        marcador.markdown(f"### {tiempo}")
        time.sleep(1)
else:
    st.info("Aún no se ha registrado ningún consumo.")

# === Mostrar historial de ingresos ===
st.subheader("🪪 Historial de ingresos a la App")

ingresos = list(coleccion_ingresos.find().sort("fecha", -1))
if ingresos:
    for ingreso in ingresos:
        fecha = ingreso.get("fecha")
        ip = ingreso.get("ip", "Desconocida")
        ciudad = ingreso.get("ciudad", "Desconocida")

        if isinstance(fecha, str):
            try:
                fecha = datetime.fromisoformat(fecha)
            except:
                fecha = None

        if fecha:
            fecha_str = fecha.replace(tzinfo=pytz.UTC).astimezone(colombia).strftime("%Y-%m-%d %H:%M:%S")
        else:
            fecha_str = "Desconocida"

        st.write(f"{fecha_str} — IP: {ip} — Ciudad: {ciudad}")
else:
    st.info("Aún no hay ingresos registrados.")