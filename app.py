import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from datetime import datetime, date
import uuid
import json

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Subway - Plataforma Centralizada de Cuponeras",
    page_icon="🥪",
    layout="wide"
)

# --- ESTILOS VISUALES (PALETA SUBWAY) ---
st.markdown("""
    <style>
    .main-title { color: #008938; font-weight: bold; text-align: center; }
    .stButton>button { background-color: #FFC72C; color: #008938; font-weight: bold; border-radius: 8px; }
    .ticket-box {
        border: 2px dashed #008938;
        background-color: #1e2530;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        margin-top: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# --- PERSISTENCIA LOCAL Y SINCRONIZACIÓN CSV ---
CSV_FILE = "base_clientes_subway.csv"

def cargar_base_datos():
    try:
        return pd.read_csv(CSV_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=[
            "ID_Cuponera", "Cedula", "Nombre", "Correo", "Telefono", 
            "Fecha_Cumpleanos", "Puntos_Fidelidad", "Fecha_Registro"
        ])

def guardar_registro(nuevo_registro):
    df = cargar_base_datos()
    df = pd.concat([df, pd.DataFrame([nuevo_registro])], ignore_index=True)
    df.to_csv(CSV_FILE, index=False)
    return df

# Inicialización en Session State
if 'db_clientes' not in st.session_state:
    st.session_state.db_clientes = cargar_base_datos()

if 'db_redenciones' not in st.session_state:
    st.session_state.db_redenciones = pd.DataFrame(columns=[
        "ID_Cuponera", "Beneficio", "Tienda", "Fecha_Redencion"
    ])

BENEFICIOS = [
    "Combo Classic", "Combo Pollo", "Galleta gratis", 
    "Bebida gratis", "2x1 en Sub 15 cm", "Upgrade de combo"
]

# --- MENÚ LATERAL ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/5/5c/Subway_2016_logo.svg", width=180)
perfil = st.sidebar.selectbox("Seleccione el Perfil:", [
    "1. Portal Cliente (Registro y Cuponera Digital)",
    "2. Portal Franquicia (Punto de Venta)",
    "3. Dashboard Casa Matriz"
])

# ==========================================
# 1. PORTAL CLIENTE (FASE 1)
# ==========================================
if perfil == "1. Portal Cliente (Registro y Cuponera Digital)":
    st.markdown("<h1 class='main-title'>💚 Subway Fest: Activa tu Cuponera Digital</h1>", unsafe_allow_html=True)
    st.write("Escanea, regístrate y recibe tu cuponera digital única para acceder a 6 beneficios y acumular puntos de fidelización.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📋 Formulario de Registro de Cliente")
        with st.form("form_registro_cliente"):
            nombre = st.text_input("Nombre Completo *")
            cedula = st.text_input("Número de Cédula / Documento (para acumular puntos)")
            correo = st.text_input("Correo Electrónico *")
            telefono = st.text_input("Teléfono Móvil *")
            fecha_cumple = st.date_input("Fecha de Cumpleaños (Beneficios especiales)", value=date(2000, 1, 1))
            
            submit_reg = st.form_submit_button("🎟️ Generar Mi Cuponera Digital")

            if submit_reg:
                if nombre and correo and telefono:
                    # Generar ID único e irrepetible para la cuponera del cliente
                    codigo_unico = f"SUB-2026-{uuid.uuid4().hex[:6].upper()}"
                    
                    nuevo_registro = {
                        "ID_Cuponera": codigo_unico,
                        "Cedula": cedula,
                        "Nombre": nombre,
                        "Correo": correo,
                        "Telefono": telefono,
                        "Fecha_Cumpleanos": str(fecha_cumple),
                        "Puntos_Fidelidad": 100,  # 100 puntos por bienvenida
                        "Fecha_Registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    # Guardar en la base de datos (CSV / GitHub)
                    st.session_state.db_clientes = guardar_registro(nuevo_registro)
                    st.session_state.ultimo_registro = nuevo_registro
                    st.success("🎉 ¡Registro completado con éxito!")
                else:
                    st.error("Por favor completa los campos obligatorios (*).")

    with col2:
        st.subheader("🎟️ Tu Cuponera Digital")
        if 'ultimo_registro' in st.session_state:
            reg = st.session_state.ultimo_registro
            
            st.markdown(f"""
                <div class='ticket-box'>
                    <h3 style='color: #FFC72C; margin:0;'>CUPONERA SUBWAY FEST</h3>
                    <p style='margin:5px 0;'><b>Código Único:</b> <span style='color:#008938; font-size:18px;'>{reg['ID_Cuponera']}</span></p>
                    <p style='margin:0;'><b>Titular:</b> {reg['Nombre']} | <b>Cédula:</b> {reg['Cedula']}</p>
                    <p style='margin:0;'>⭐ <b>Puntos de Fidelidad:</b> {reg['Puntos_Fidelidad']} pts</p>
                </div>
            """, unsafe_allow_html=True)

            st.write("---")
            st.write("#### Activar Beneficio para Tienda")
            beneficio_sel = st.selectbox("Selecciona el beneficio que deseas redimir:", BENEFICIOS)
            
            if st.button("Generar QR para Canjear en Caja"):
                payload = json.dumps({
                    "id_cuponera": reg['ID_Cuponera'],
                    "cedula": reg['Cedula'],
                    "beneficio": beneficio_sel,
                    "timestamp": datetime.now().strftime("%Y%m%d%H%M%S")
                })
                
                qr = qrcode.make(payload)
                buffer = BytesIO()
                qr.save(buffer, format="PNG")
                
                st.image(buffer.getvalue(), caption=f"Muestra este QR al cajero para: {beneficio_sel}", width=220)
        else:
            st.info("Diligencia el formulario de la izquierda para generar y visualizar tu cuponera digital personalizada.")

# ==========================================
# 2. PORTAL FRANQUICIA & 3. CASA MATRIZ
# ==========================================
elif perfil == "2. Portal Franquicia (Punto de Venta)":
    st.markdown("<h1 class='main-title'>🏬 Validador en Punto de Venta</h1>", unsafe_allow_html=True)
    st.write("Escanea el QR o ingresa la cuponera para aplicar la redención.")
    st.dataframe(st.session_state.db_clientes, use_container_width=True)

elif perfil == "3. Dashboard Casa Matriz":
    st.markdown("<h1 class='main-title'>📈 Base de Datos Centralizada de Clientes</h1>", unsafe_allow_html=True)
    st.dataframe(st.session_state.db_clientes, use_container_width=True)
