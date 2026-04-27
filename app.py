import streamlit as st
import pandas as pd
import hashlib
import sys
import os
from datetime import datetime, date

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="SGDA Panamá", layout="wide", page_icon="⚖️")

ruta_raiz = os.path.dirname(os.path.abspath(__file__))
if ruta_raiz not in sys.path:
    sys.path.append(ruta_raiz)

try:
    from SupabaseConnection import LegalDB
    from configuracion import ModuloConfiguracion
except ImportError:
    st.error("Error: Faltan archivos de conexión.")
    st.stop()

# --- 2. UTILIDADES ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def obtener_nombre_cliente(c):
    nombre = c.get('nombre_completo')
    return str(nombre) if nombre else f"ID: {str(c.get('id'))[:8]}"

# --- 3. LÓGICA PRINCIPAL ---
def main():
    if "_sgda_db" not in st.session_state:
        st.session_state._sgda_db = LegalDB()
    db = st.session_state._sgda_db

    # --- LOGIN ---
    if 'auth' not in st.session_state:
        st.title("⚖️ Acceso SGDA")
        with st.form("login"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                h = hash_password(p)
                try:
                    res = db.conn.table("perfiles").select("*").eq("usuario", u).eq("contraseña", h).execute()
                    if res.data:
                        st.session_state['auth'] = res.data[0]
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas")
                except Exception:
                    st.error("Error al conectar con la tabla 'perfiles'.")
        return

    # --- NAVEGACIÓN ---
    opciones_menu = ["📊 Dashboard", "👤 Gestión de Clientes", "📅 Agenda de Citas", "⚙️ Configuración"]
    if 'menu_actual' not in st.session_state:
        st.session_state.menu_actual = "📊 Dashboard"

    menu = st.sidebar.radio("Navegación", opciones_menu, index=opciones_menu.index(st.session_state.menu_actual))
    st.session_state.menu_actual = menu

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.clear()
        st.rerun()

    # --- MÓDULO 1: DASHBOARD ---
    if st.session_state.menu_actual == "📊 Dashboard":
        st.header(f"Bienvenido, {st.session_state['auth'].get('nombre', 'Abogado')}")
        if st.button("➕ Agendar Nueva Cita", type="primary"):
            st.session_state.menu_actual = "📅 Agenda de Citas"
            st.rerun()

        st.subheader("📅 Citas Próximas")
        try:
            res_c = db.conn.table("citas").select("*").eq("estado", "programada").execute()
            if res_c.data:
                st.table(pd.DataFrame(res_c.data)[['titulo_cita', 'fecha_hora']])
            else:
                st.info("No hay citas programadas.")
        except: pass

    # --- MÓDULO 2: GESTIÓN DE CLIENTES ---
    elif st.session_state.menu_actual == "👤 Gestión de Clientes":
        st.header("👤 Gestión de Clientes")
        res_cli = db.conn.table("clientes").select("*").execute()
        clientes = res_cli.data if res_cli.data else []
        
        col_busq, col_add = st.columns([2, 1])
        with col_busq:
            dict_cli = {obtener_nombre_cliente(c): c for c in clientes}
            sel_nom = st.selectbox("Buscar Cliente:", ["---"] + list(dict_cli.keys()))
            cliente = dict_cli.get(sel_nom)

        with col_add:
            with st.popover("➕ Nuevo Cliente", use_container_width=True):
                with st.form("f_new_cli", clear_on_submit=True):
                    n_comp = st.text_input("Nombre Completo *")
                    t_id = st.selectbox("Tipo Identificación", ["Cédula", "Pasaporte", "RUC"])
                    ident = st.text_input("Identificación *")
                    tel = st.text_input("Teléfono")
                    mail = st.text_input("Correo")
                    dir_c = st.text_area("Dirección")
                    if st.form_submit_button("Guardar"):
                        db.conn.table("clientes").insert({
                            "nombre_completo": n_comp, "tipo_identificacion": t_id,
                            "identificacion": ident, "telefono": tel,
                            "correo_electronico": mail, "direccion": dir_c
                        }).execute()
                        st.rerun()

        if cliente:
            st.subheader(f"Expedientes: {obtener_nombre_cliente(cliente)}")
            t1, t2 = st.tabs(["📋 Historial", "⚖️ Nuevo Expediente"])
            with t1:
                res_exp = db.conn.table("expedientes").select("*").eq("cliente_id", cliente['id']).execute()
                for exp in (res_exp.data or []):
                    with st.expander(f"📁 {exp.get('numero_expediente')} - {exp.get('titulo_caso')}"):
                        res_a = db.conn.table("actuaciones").select("*").eq("expediente_id", exp['id']).execute()
                        for a in (res_a.data or []):
                            st.caption(f"• {a.get('tipo_tramite')}: {a.get('descripcion')}")
                        
                        with st.popover("Añadir Actuación"):
                            with st.form(f"act_{exp['id']}"):
                                d_a = st.text_area("Descripción")
                                t_a = st.text_input("Tipo Trámite")
                                if st.form_submit_button("Guardar"):
                                    db.conn.table("actuaciones").insert({
                                        "expediente_id": exp['id'], "descripcion": d_a, 
                                        "tipo_tramite": t_a, "estado": "pendiente"
                                    }).execute()
                                    st.rerun()

            with t2:
                with st.form("new_exp"):
                    num = st.text_input("Número")
                    tit = st.text_input("Título")
                    if st.form_submit_button("Crear"):
                        db.conn.table("expedientes").insert({
                            "numero_expediente": num, "titulo_caso": tit, "cliente_id": cliente['id']
                        }).execute()
                        st.rerun()

    # --- MÓDULO 3: AGENDA ---
    elif st.session_state.menu_actual == "📅 Agenda de Citas":
        st.header("📅 Agenda de Citas")
        with st.form("f_agenda"):
            asunto = st.text_input("Asunto de la Cita")
            fecha = st.date_input("Fecha")
            hora = st.time_input("Hora")
            if st.form_submit_button("Agendar"):
                dt = datetime.combine(fecha, hora).isoformat()
                db.conn.table("citas").insert({"titulo_cita": asunto, "fecha_hora": dt, "estado": "programada"}).execute()
                st.success("Cita agendada.")
                st.session_state.menu_actual = "📊 Dashboard"
                st.rerun()

    # --- MÓDULO 4: CONFIGURACIÓN ---
    elif st.session_state.menu_actual == "⚙️ Configuración":
        st.header("⚙️ Configuración y Limpieza")
        t_perfil, t_limpieza = st.tabs(["👤 Mi Perfil", "🧹 Mantenimiento"])
        with t_perfil:
            ModuloConfiguracion(db).render()
        with t_limpieza:
            st.warning("Borrado de datos de prueba")
            if st.button("🗑️ Borrar Todo (Actuaciones, Expedientes, Clientes)"):
                db.conn.table("actuaciones").delete().neq("id", "0000-0000").execute()
                db.conn.table("expedientes").delete().neq("id", "0000-0000").execute()
                db.conn.table("clientes").delete().neq("id", "0000-0000").execute()
                st.success("Sistema limpio.")
                st.rerun()

if __name__ == "__main__":
    main()