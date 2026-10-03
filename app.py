import os
import requests
import streamlit as st
from datetime import datetime, timezone
from icalendar import Calendar
from google import genai

# Configuración de la página
st.set_page_config(
    page_title="Jarvis Academic Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo personalizado minimalista / Pro
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #4A90E2; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    .task-card {
        padding: 12px;
        margin-bottom: 8px;
        border-radius: 8px;
        background-color: rgba(255, 255, 255, 0.05);
        border-left: 4px solid #4A90E2;
    }
</style>
""", unsafe_allow_html=True)

# API Keys & URLs
CALENDAR_FEED_URL = st.sidebar.text_input(
    "URL Feed Canvas iCal", 
    value="PEGA_AQUI_TU_URL_DE_FEED_ICAL",
    type="password"
)
GEMINI_API_KEY = "AQ.Ab8RN6KUlRGf7QFNySZjiB9hATjeRt-fTGxIaOiqy13fMvXVeg"

def obtener_tareas():
    if "PEGA_AQUI" in CALENDAR_FEED_URL:
        return []
    try:
        response = requests.get(CALENDAR_FEED_URL)
        if response.status_code != 200:
            return []
        cal = Calendar.from_ical(response.content)
        ahora = datetime.now(timezone.utc)
        tareas_lista = []

        for component in cal.walk():
            if component.name == "VEVENT":
                summary = str(component.get("summary"))
                dtend = component.get("dtend") or component.get("dtstart")
                if dtend:
                    fecha_entrega = dtend.dt
                    if not isinstance(fecha_entrega, datetime):
                        fecha_entrega = datetime.combine(fecha_entrega, datetime.min.time()).replace(tzinfo=timezone.utc)
                    elif fecha_entrega.tzinfo is None:
                        fecha_entrega = fecha_entrega.replace(tzinfo=timezone.utc)

                    horas_restantes = (fecha_entrega - ahora).total_seconds() / 3600

                    if horas_restantes > -24:
                        tareas_lista.append({
                            "actividad": summary,
                            "fecha_entrega": fecha_entrega.strftime("%Y-%m-%d %H:%M UTC"),
                            "horas_restantes": round(horas_restantes, 1)
                        })
        tareas_lista.sort(key=lambda x: x["horas_restantes"])
        return tareas_lista
    except Exception:
        return []

# Sidebar - Menú lateral
st.sidebar.title("🤖 JARVIS AI")
st.sidebar.markdown("---")
sincronizar = st.sidebar.button("🔄 Sincronizar Canvas")

# Panel Principal
st.markdown("<div class='main-header'>⚡ Jarvis Academic Dashboard</div>", unsafe_allow_html=True)
st.caption("Planificación inteligente de entregas y estudio con Gemini")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📋 Tareas Detectadas")
    tareas = obtener_tareas()
    
    if tareas:
        st.success(f"{len(tareas)} actividades encontradas")
        for t in tareas:
            urgencia_color = "🔴" if t['horas_restantes'] < 24 else ("🟡" if t['horas_restantes'] < 72 else "🟢")
            st.markdown(f"""
            <div class='task-card'>
                <strong>{urgencia_color} {t['actividad']}</strong><br>
                <small>⏰ Quedan: {t['horas_restantes']} hrs | Entrega: {t['fecha_entrega']}</small>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Pega tu enlace de Canvas en el menú lateral para sincronizar.")

with col2:
    st.subheader("🤖 Plan Inteligente de Jarvis")
    
    if st.button("🚀 Generar Plan de Estudio con Gemini", type="primary"):
        if not tareas:
            st.warning("Primero necesitas sincronizar las tareas del calendario.")
        else:
            with st.spinner("Conectando con Gemini 3.8 Flash..."):
                try:
                    client = genai.Client(api_key=GEMINI_API_KEY)
                    prompt = f"""
Eres Jarvis, un asistente académico personal de alto nivel.
Aquí está la lista de entregas registradas en Canvas ({len(tareas)} encontradas):

{tareas}

Por favor, genera una respuesta clara y muy bien formateada en Markdown usando tablas o viñetas:
1. Prioridades inmediatas.
2. Estimación de tiempo para cada tarea.
3. Bloques de horario recomendados para hoy.
"""
                    chat = client.chats.create(model="gemini-3.8-flash")
                    respuesta = chat.send_message(prompt)
                    st.markdown(respuesta.text)
                except Exception as e:
                    st.error(f"Error de conexión con el modelo: {e}")
