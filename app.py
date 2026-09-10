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

# --- PERSISTENCIA EN BASE DE DATOS LOCAL (CSV) ---
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

BENEFICIOS = [
    "Combo Classic", "Combo Pollo", "Galleta gratis", 
    "Bebida gratis", "2x1 en Sub 15 cm", "Upgrade de combo"
]

# --- NAVEGACIÓN PERFILES ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/5/5c/Subway_2016_logo.svg", width=180)
perfil = st.sidebar.selectbox("Seleccione el Perfil:", [
    "1. Portal Cliente (Escaneo y Registro)",
    "2. Generador de QR Impreso (Para Publicidad)",
    "3. Dashboard Casa Matriz"
])

# ==========================================
# 1. PORTAL CLIENTE (FASE DE REGISTRO)
# ==========================================
if perfil == "1. Portal Cliente (Escaneo y Registro)":
    st.markdown("<h1 class='main-title'>💚 Subway Fest: Registro de Cuponera Digital</h1>", unsafe_allow_html=True)
    st.write("Completa el formulario para activar tu cuponera digital única y ganar +100 Subway Points de bienvenida.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📋 Formulario de Registro")
        with st.form("form_registro_cliente"):
            nombre = st.text_input("Nombre Completo *")
            cedula = st.text_input("Número de Cédula / Documento (para acumular puntos)")
            correo = st.text_input("Correo Electrónico *")
            telefono = st.text_input("Teléfono Móvil *")
            fecha_cumple = st.date_input("Fecha de Cumpleaños (Para beneficios especiales)", value=date(2000, 1, 1))
            
            submit_reg = st.form_submit_button("🎟️ Registrarme y Obtener Cuponera")

            if submit_reg:
                if nombre and correo and telefono:
                    # Generación de Código Único
                    codigo_unico = f"SUB-2026-{uuid.uuid4().hex[:6].upper()}"
                    
                    nuevo_registro = {
                        "ID_Cuponera": codigo_unico,
                        "Cedula": cedula,
                        "Nombre": nombre,
                        "Correo": correo,
                        "Telefono": telefono,
                        "Fecha_Cumpleanos": str(fecha_cumple),
                        "Puntos_Fidelidad": 100,
                        "Fecha_Registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    # Guardar registro
                    st.session_state.db_clientes = guardar_registro(nuevo_registro)
                    st.session_state.ultimo_registro = nuevo_registro
                    st.success("🎉 ¡Registro completado con éxito!")
                else:
                    st.error("Por favor completa los campos obligatorios (*).")

    with col2:
        st.subheader("🎟️ Tu Cuponera Digital Asignada")
        if 'ultimo_registro' in st.session_state:
            reg = st.session_state.ultimo_registro
            
            st.markdown(f"""
                <div class='ticket-box'>
                    <h3 style='color: #FFC72C; margin:0;'>CUPONERA SUBWAY FEST</h3>
                    <p style='margin:5px 0;'><b>Código Único:</b> <span style='color:#008938; font-size:18px;'>{reg['ID_Cuponera']}</span></p>
                    <p style='margin:0;'><b>Titular:</b> {reg['Nombre']} | <b>Cédula:</b> {reg['Cedula']}</p>
                    <p style='margin:0;'>⭐ <b>Subway Points:</b> {reg['Puntos_Fidelidad']} pts</p>
                </div>
            """, unsafe_allow_html=True)

            st.write("---")
            st.write("#### Canjear Beneficio en Restaurante")
            beneficio_sel = st.selectbox("Selecciona un beneficio:", BENEFICIOS)
            
            if st.button("Generar QR para Canje en Caja"):
                payload = json.dumps({
                    "id_cuponera": reg['ID_Cuponera'],
                    "beneficio": beneficio_sel,
                    "timestamp": datetime.now().strftime("%Y%m%d%H%M%S")
                })
                
                qr = qrcode.make(payload)
                buffer = BytesIO()
                qr.save(buffer, format="PNG")
                
                st.image(buffer.getvalue(), caption=f"Muestra este QR en caja para: {beneficio_sel}", width=220)
        else:
            st.info("Completa tu registro a la izquierda para ver tu cuponera personalizada.")

# ==========================================
# 2. GENERADOR DE QR IMPRESO (PUBLICIDAD)
# ==========================================
elif perfil == "2. Generador de QR Impreso (Para Publicidad)":
    st.markdown("<h1 class='main-title'>🖨️ Generador de Código QR de Registro</h1>", unsafe_allow_html=True)
    st.write("Este módulo genera el código QR que se imprimirá en los cupones físicos o afiches para dirigir a los clientes a la aplicación.")

    app_url = st.text_input("Ingresa el enlace público de tu app de Streamlit:", 
                            value="https://cuponerasubway.streamlit.app/")

    if st.button("Generar QR para Imprimir"):
        qr = qrcode.make(app_url)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        
        st.image(buffer.getvalue(), caption="Código QR de Acceso al Formulario de Registro", width=250)
        st.download_button(
            label="💾 Descargar Imagen del QR para Diseños",
            data=buffer.getvalue(),
            file_name="QR_Registro_Subway.png",
            mime="image/png"
        )

# ==========================================
# 3. DASHBOARD CASA MATRIZ
# ==========================================
elif perfil == "3. Dashboard Casa Matriz":
    st.markdown("<h1 class='main-title'>📈 Base de Datos Centralizada</h1>", unsafe_allow_html=True)
    st.dataframe(st.session_state.db_clientes, use_container_width=True)
