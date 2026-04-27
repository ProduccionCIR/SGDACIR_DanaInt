import streamlit as st
import pandas as pd
from datetime import datetime, date
from SupabaseConnection import LegalDB
from configuracion import ModuloConfiguracion
from contabilidad import ModuloContabilidad


def _backend():
    """Crea una sola vez por sesión de navegador (evita fallar al importar si no hay secrets.toml)."""
    if "_sgda_db" not in st.session_state:
        st.session_state._sgda_db = LegalDB()
        st.session_state._sgda_mod_config = ModuloConfiguracion(st.session_state._sgda_db)
        st.session_state._sgda_mod_contabilidad = ModuloContabilidad(st.session_state._sgda_db)
    return (
        st.session_state._sgda_db,
        st.session_state._sgda_mod_config,
        st.session_state._sgda_mod_contabilidad,
    )


def main():
    st.set_page_config(page_title="SGDA Legal ERP", layout="wide", page_icon="⚖️")

    try:
        db, mod_config, mod_contabilidad = _backend()
    except ValueError as e:
        st.error("⚠️ No se pudieron cargar las credenciales de Supabase.")
        st.caption(str(e))
        st.markdown(
            "En **GitHub Codespaces**: *Settings* (tu avatar) → *Your personal settings* → "
            "*Codespaces* → *Codespaces secrets*, o secretos del **repositorio**: "
            "`SUPABASE_URL` y `SUPABASE_KEY`."
        )
        st.info(
            "Alternativa sin Streamlit secrets: cree un archivo **`.env`** en la raíz del repo "
            "(copie `.env.example` a `.env` y pegue URL y clave). Luego `pip install python-dotenv` si falta."
        )
        return

    # --- LÓGICA DE SESIÓN ---
    if 'auth' not in st.session_state:
        mostrar_login(db)
        return

    user = st.session_state['auth']
    st.sidebar.title("⚖️ SGDA PANAMÁ")
    st.sidebar.markdown(f"**Abogado:** {user['nombre_abogado']}")
    
    menu = st.sidebar.radio("Navegación", [
        "📊 Dashboard", 
        "👤 Clientes", 
        "📂 Inventario Judicial", 
        "💰 Cobros y Gastos", 
        "⚙️ Administración"
    ])

    if st.sidebar.button("🔒 Cerrar Sesión", use_container_width=True):
        del st.session_state['auth']
        st.rerun()

    # --- ROUTING DE MÓDULOS ---
    if menu == "📊 Dashboard":
        st.header("Resumen del Despacho")
        # Aquí puedes integrar tus alarmas de Expediente.py
        st.info("Bienvenido al panel de control judicial.")

    elif menu == "👤 Clientes":
        gestionar_clientes_legal(db, mod_config)

    elif menu == "📂 Inventario Judicial":
        st.header("Gestión de Expedientes")
        st.write("Consulta de Fincas, Tomos y Folios.")
        # Aquí va la lógica de tus archivos originales

    elif menu == "💰 Cobros y Gastos":
        st.subheader("Control Financiero del Despacho")
        # 'Inyectamos' el módulo de contabilidad que subiste
        mod_contabilidad.render()

    elif menu == "⚙️ Administración":
        # 'Inyectamos' el módulo de configuración que subiste
        mod_config.render()

def mostrar_login(db):
    st.title("⚖️ Acceso SGDA")
    with st.form("login"):
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.form_submit_button("Entrar", use_container_width=True):
            try:
                res = db.table("usuarios").select("*").eq("usuario", u).eq("password_hash", p).execute()
            except Exception as e:
                st.error(f"No se pudo conectar con Supabase. Revise secrets y red. Detalle: {e}")
                return
            if res.data:
                st.session_state['auth'] = res.data[0]
                # Datos para auditoría de configuracion.py
                st.session_state['usuario'] = res.data[0]['usuario']
                st.session_state['rol'] = res.data[0].get('rol', 'usuario')
                st.rerun()
            else:
                st.error("Credenciales Incorrectas")

def gestionar_clientes_legal(db, mod_config):
    st.header("Registro de Clientes")
    with st.form("registro_cliente"):
        nom = st.text_input("Nombre Completo / Razón Social")
        es_ext = st.toggle("¿Es Extranjero? (Habilita Pasaporte)")
        
        if es_ext:
            ident = st.text_input("Número de Pasaporte (Formato Libre)")
        else:
            ident = st.text_input("Cédula (Formato: N-XXX-XXXX)")
            
        if st.form_submit_button("Guardar Cliente"):
            if nom and ident:
                ok = db.insert("clientes", {
                    "nombre_completo": nom,
                    "cedula_ruc": ident,
                    "es_extranjero": es_ext
                })
                if ok:
                    st.success("Cliente guardado exitosamente.")
                    mod_config.registrar_log("CREAR", "CLIENTES", f"Registró a {nom}")
            else:
                st.error("Campos obligatorios faltantes.")

if __name__ == "__main__":
    main()