import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from datetime import datetime, date
import uuid
import json
from github import Github

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Subway Fest - Cuponera Digital",
    page_icon="🥪",
    layout="wide"
)

# --- CONFIGURACIÓN DE GITHUB (PERSISTENCIA REAL) ---
# Puedes configurar tu TOKEN de GitHub en Streamlit Secrets o dejarlo en fallback local
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
REPO_NAME = "Yenifercuponera/Cuponera_Subway"
CSV_FILE = "base_clientes_subway.csv"

def guardar_en_github(df_nuevo):
    """Guarda y sincroniza directamente el CSV dentro del repositorio de GitHub"""
    csv_data = df_nuevo.to_csv(index=False)
    if GITHUB_TOKEN:
        try:
            g = Github(GITHUB_TOKEN)
            repo = g.get_repo(REPO_NAME)
            try:
                contents = repo.get_contents(CSV_FILE)
                repo.update_file(contents.path, "Actualización base de clientes", csv_data, contents.sha)
            except Exception:
                repo.create_file(CSV_FILE, "Creación base de clientes", csv_data)
        except Exception as e:
            st.error(f"Error al sincronizar con GitHub: {e}")

def cargar_base_datos():
    try:
        return pd.read_csv(CSV_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=[
            "ID_Cuponera", "Cedula", "Nombre", "Correo", "Telefono", 
            "Fecha_Cumpleanos", "Puntos_Fidelidad", "Fecha_Registro"
        ])

# Inicialización
if 'db_clientes' not in st.session_state:
    st.session_state.db_clientes = cargar_base_datos()

BENEFICIOS = ["Combo Classic", "Combo Pollo", "Galleta gratis", "Bebida gratis", "2x1 en Sub 15 cm", "Upgrade de combo"]

# --- NAVEGACIÓN ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/5/5c/Subway_2016_logo.svg", width=180)
perfil = st.sidebar.selectbox("Seleccione el Perfil:", [
    "1. Portal Cliente (Registro y Cuponera)",
    "2. Portal Franquicia (Validación en Punto de Venta)",
    "3. Generador QR para Publicidad Impresa",
    "4. Dashboard Casa Matriz"
])

# ==========================================
# 1. PORTAL CLIENTE
# ==========================================
if perfil == "1. Portal Cliente (Registro y Cuponera)":
    st.title("💚 Subway Fest: Registro de Cuponera Digital")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📋 Registro de Cliente")
        with st.form("form_registro"):
            nombre = st.text_input("Nombre Completo *")
            cedula = st.text_input("Número de Cédula / Documento")
            correo = st.text_input("Correo Electrónico *")
            telefono = st.text_input("Teléfono Móvil *")
            fecha_cumple = st.date_input("Fecha de Cumpleaños", value=date(2000, 1, 1))
            
            if st.form_submit_button("🎟️ Activar Mi Cuponera Digital"):
                if nombre and correo and telefono:
                    codigo_unico = f"SUB-2026-{uuid.uuid4().hex[:6].upper()}"
                    nuevo_registro = {
                        "ID_Cuponera": codigo_unico,
                        "Cedula": cedula if cedula else "N/A",
                        "Nombre": nombre,
                        "Correo": correo,
                        "Telefono": telefono,
                        "Fecha_Cumpleanos": str(fecha_cumple),
                        "Puntos_Fidelidad": 100,
                        "Fecha_Registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    df_actualizado = pd.concat([st.session_state.db_clientes, pd.DataFrame([nuevo_registro])], ignore_index=True)
                    st.session_state.db_clientes = df_actualizado
                    st.session_state.ultimo_registro = nuevo_registro
                    
                    # Guardar en CSV local y Push a GitHub
                    df_actualizado.to_csv(CSV_FILE, index=False)
                    guardar_en_github(df_actualizado)
                    
                    st.success("🎉 ¡Tu cuponera ha sido registrada y guardada exitosamente!")
                else:
                    st.error("Por favor completa los campos obligatorios (*).")

    with col2:
        st.subheader("🎟️ Tu Cuponera Asignada")
        if 'ultimo_registro' in st.session_state:
            reg = st.session_state.ultimo_registro
            st.info(f"**Código:** {reg['ID_Cuponera']}\n\n**Titular:** {reg['Nombre']}\n\n**Cédula:** {reg['Cedula']}")

            st.write("---")
            st.subheader("🎁 Canjear Beneficio en Tienda")
            beneficio_sel = st.selectbox("Selecciona beneficio:", BENEFICIOS)
            
            if st.button("Generar QR para Mostrar en Caja"):
                payload = json.dumps({
                    "id_cuponera": reg['ID_Cuponera'],
                    "beneficio": beneficio_sel,
                    "cliente": reg['Nombre']
                })
                qr = qrcode.make(payload)
                buffer = BytesIO()
                qr.save(buffer, format="PNG")
                st.image(buffer.getvalue(), caption="Muestra este código al cajero de Subway", width=230)

# ==========================================
# 2. PORTAL FRANQUICIA (VALIDADOR DE CAJA)
# ==========================================
elif perfil == "2. Portal Franquicia (Validación en Punto de Venta)":
    st.title("🏬 Módulo de Caja y Validación")
    st.write("Ingresa o busca el código único de la cuponera para hacer efectiva la redención:")

    codigo_ingresado = st.text_input("Ingrese el Código Único de Cuponera (ej. SUB-2026-XXXXXX):")
    beneficio_redimir = st.selectbox("Beneficio a entregar:", BENEFICIOS)

    if st.button("Validar y Redimir Beneficio"):
        df = st.session_state.db_clientes
        coincidencias = df[df['ID_Cuponera'] == codigo_ingresado.strip()]

        if not coincidencias.empty:
            cliente = coincidencias.iloc[0]
            st.success(f"✅ ¡CUPONERA VÁLIDA! Cliente: {cliente['Nombre']} | Cédula: {cliente['Cedula']}")
            st.balloons()
        else:
            st.error("❌ Código de cuponera no encontrado en el sistema o inválido.")

# ==========================================
# 3. GENERADOR DE QR IMPRESO
# ==========================================
elif perfil == "3. Generador QR para Publicidad Impresa":
    st.title("🖨️ Generador de QR para Afiches")
    app_url = st.text_input("Enlace Público de la App:", value="https://cuponerasubway.streamlit.app/")

    if st.button("Generar QR"):
        qr = qrcode.make(app_url)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        st.image(buffer.getvalue(), width=250)

# ==========================================
# 4. DASHBOARD CASA MATRIZ
# ==========================================
elif perfil == "4. Dashboard Casa Matriz":
    st.title("📈 Base de Datos Centralizada de Clientes")
    st.dataframe(st.session_state.db_clientes, use_container_width=True)
