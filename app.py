import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from datetime import datetime
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
    .card { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 5px solid #008938; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- INICIALIZACIÓN DE DATOS (MOCK / SIMULADOR GITHUB) ---
if 'db_clientes' not in st.session_state:
    st.session_state.db_clientes = pd.DataFrame(columns=[
        "ID_Cuponera", "Cliente_Nombre", "Correo", "Telefono", "Puntos_Fidelidad", "Fecha_Registro"
    ])

if 'db_redenciones' not in st.session_state:
    st.session_state.db_redenciones = pd.DataFrame(columns=[
        "ID_Cuponera", "Beneficio", "Tienda", "Fecha_Redencion", "Valor_Estimado"
    ])

BENEFICIOS = [
    "Combo Classic",
    "Combo Pollo",
    "Galleta gratis",
    "Bebida gratis",
    "2x1 en Sub 15 cm",
    "Upgrade de combo"
]

# --- NAVEGACIÓN PERFILES ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/5/5c/Subway_2016_logo.svg", width=200)
perfil = st.sidebar.selectbox("Seleccione el Perfil:", [
    "1. Portal Cliente (Escaneo y Registro)",
    "2. Portal Franquicia (Punto de Venta)",
    "3. Dashboard Casa Matriz"
])

# ==========================================
# 1. PORTAL CLIENTE
# ==========================================
if perfil == "1. Portal Cliente (Escaneo y Registro)":
    st.markdown("<h1 class='main-title'>💚 Subway Fest: Activa tu Cuponera</h1>", unsafe_allow_html=True)
    st.write("¡Bienvenido! Registra tu cuponera física o digital para desbloquear tus 6 beneficios y acumular puntos.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📋 Paso 1: Registro del Cliente")
        with st.form("form_registro"):
            codigo_cuponera = st.text_input("Código Único de Cuponera", value="SUB-2026-9912")
            nombre = st.text_input("Nombre Completo")
            correo = st.text_input("Correo Electrónico")
            telefono = st.text_input("Teléfono Móvil")
            submit_reg = st.form_submit_button("Activar Cuponera y Sumar Puntos")

            if submit_reg:
                if correo and telefono:
                    # Guardar datos
                    nuevo_registro = {
                        "ID_Cuponera": codigo_cuponera,
                        "Cliente_Nombre": nombre,
                        "Correo": correo,
                        "Telefono": telefono,
                        "Puntos_Fidelidad": 100, # 100 puntos de bienvenida
                        "Fecha_Registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state.db_clientes = pd.concat([st.session_state.db_clientes, pd.DataFrame([nuevo_registro])], ignore_index=True)
                    st.success("🎉 ¡Cuponera activada exitosamente! Has recibido +100 Subway Points de bienvenida.")
                else:
                    st.warning("Por favor completa tu correo y teléfono para continuar.")

    with col2:
        st.subheader("🎟️ Paso 2: Selecciona un Beneficio a Redimir")
        cupon_busqueda = st.text_input("Ingresa tu ID de Cuponera para consultar:", value="SUB-2026-9912")
        
        cliente_data = st.session_state.db_clientes[st.session_state.db_clientes['ID_Cuponera'] == cupon_busqueda]
        
        if not cliente_data.empty:
            puntos = cliente_data.iloc[0]['Puntos_Fidelidad']
            st.info(f"👤 **Cliente:** {cliente_data.iloc[0]['Cliente_Nombre']} | ⭐ **Puntos Acumulados:** {puntos} pts")
            
            beneficio_sel = st.selectbox("Selecciona el beneficio que deseas usar hoy:", BENEFICIOS)
            
            if st.button("Generar QR Temporal de Redención"):
                qr_payload = json.dumps({
                    "id_cuponera": cupon_busqueda,
                    "beneficio": beneficio_sel,
                    "timestamp": datetime.now().strftime("%Y%m%d%H%M%S")
                })
                
                qr = qrcode.make(qr_payload)
                buffer = BytesIO()
                qr.save(buffer, format="PNG")
                
                st.image(buffer.getvalue(), caption=f"Muestra este QR en caja para: {beneficio_sel}", width=250)
                st.caption("⏳ Válido únicamente por 15 minutos en la tienda física.")

# ==========================================
# 2. PORTAL FRANQUICIA (PUNTO DE VENTA)
# ==========================================
elif perfil == "2. Portal Franquicia (Punto de Venta)":
    st.markdown("<h1 class='main-title'>🏬 Módulo de Redención - Franquiciados</h1>", unsafe_allow_html=True)
    tienda = st.sidebar.selectbox("Punto de Venta Actual:", ["Titán Plaza Piso 3", "Plaza Central", "Centro Mayor", "Unicentro"])

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("🔍 Validar y Escanear QR")
        qr_input = st.text_area("Simulador de Lector QR (Pega el JSON escaneado o datos):", 
                                value='{"id_cuponera": "SUB-2026-9912", "beneficio": "Combo Classic"}')
        
        if st.button("Validar y Redimir"):
            try:
                data = json.loads(qr_input)
                id_c = data.get("id_cuponera")
                beneficio = data.get("beneficio")
                
                # Registrar Redención
                nueva_redencion = {
                    "ID_Cuponera": id_c,
                    "Beneficio": beneficio,
                    "Tienda": tienda,
                    "Fecha_Redencion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Valor_Estimado": 15900
                }
                st.session_state.db_redenciones = pd.concat([st.session_state.db_redenciones, pd.DataFrame([nueva_redencion])], ignore_index=True)
                
                # Otorgar puntos adicionales por compra/redención
                st.session_state.db_clientes.loc[st.session_state.db_clientes['ID_Cuponera'] == id_c, 'Puntos_Fidelidad'] += 50
                
                st.balloons()
                st.success(f"✅ Beneficio '{beneficio}' validado con éxito. +50 puntos sumados al cliente.")
            except Exception as e:
                st.error("Código QR inválido o expirado.")

    with col2:
        st.subheader("📊 Métricas Rápidas del Local")
        redenciones_tienda = st.session_state.db_redenciones[st.session_state.db_redenciones['Tienda'] == tienda]
        st.metric("Redenciones Hoy", len(redenciones_tienda))
        st.metric("Ventas Generadas (Estimadas)", f"${len(redenciones_tienda) * 15900:,.0f} COP")
        if not redenciones_tienda.empty:
            st.dataframe(redenciones_tienda[['ID_Cuponera', 'Beneficio', 'Fecha_Redencion']])

# ==========================================
# 3. DASHBOARD CASA MATRIZ
# ==========================================
elif perfil == "3. Dashboard Casa Matriz":
    st.markdown("<h1 class='main-title'>📈 Dashboard Ejecutivo Nacional - Casa Matriz</h1>", unsafe_allow_html=True)

    # KPIs Consolidados
    total_reg = len(st.session_state.db_clientes)
    total_red = len(st.session_state.db_redenciones)
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Cuponeras Registradas", f"{total_reg + 85000:,}")
    kpi2.metric("Cupones Redimidos", f"{total_red + 320000:,}")
    kpi3.metric("Tasa de Uso", "62.4%")
    kpi4.metric("ROI Estimado Campaña", "500%")

    st.markdown("---")
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("🍩 Productos Más Redimidos")
        df_prod = pd.DataFrame({
            "Producto": ["Combo Classic", "Combo Pollo", "Galleta gratis", "Bebida gratis", "Otros"],
            "Porcentaje": [35, 25, 18, 12, 10]
        })
        st.bar_chart(df_prod.set_index("Producto"))

    with col2:
        st.subheader("📍 Desempeño por Franquicias (Mapa de Calor Simulado)")
        df_tiendas = pd.DataFrame({
            "Tienda": ["Titán Plaza", "Plaza Central", "Centro Mayor", "Unicentro"],
            "Redenciones": [1240, 980, 850, 620]
        })
        st.dataframe(df_tiendas, use_container_width=True)
