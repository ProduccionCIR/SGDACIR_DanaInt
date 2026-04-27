import streamlit as st
import pandas as pd
from io import BytesIO
import datetime

class ModuloConfiguracion:
    def __init__(self, db):
        self.db = db
        self.tabla_perfiles = "perfiles"
        self.tabla_inventario = "productos"  # Ajustado a tu JSON
        self.tabla_logs = "logs_sistema"
        # Roles que reconoce tu sistema
        self.roles_disponibles = ["usuario", "supervisor", "administrador", "master", "master_it"]

    def registrar_log(self, accion, modulo, detalle):
        """Guarda movimientos en la base de datos"""
        usuario_actual = st.session_state.get('usuario', 'Desconocido')
        # Usamos .get para evitar errores si la sesión se cierra
        rol_actual = st.session_state.get('auth', {}).get('rol', 
                     st.session_state.get('auth', {}).get('nivel', 'N/A'))
        
        log_data = {
            "usuario": usuario_actual,
            "rol": rol_actual,
            "accion": accion,
            "modulo": modulo,
            "detalle": detalle,
            "fecha": datetime.datetime.now().isoformat()
        }
        try:
            self.db.conn.table(self.tabla_logs).insert(log_data).execute()
        except:
            pass

    def render(self):
        st.markdown("<h2 style='color: #707070; font-weight: bold;'>⚙️ Panel de Control Maestro</h2>", unsafe_allow_html=True)
        
        tab_usuarios, tab_datos, tab_logs, tab_mantenimiento = st.tabs([
            "👥 Usuarios", "📊 Importar/Exportar", "📜 Auditoría (Logs)", "🛡️ Mantenimiento"
        ])

        # --- PESTAÑA 1: GESTIÓN DE USUARIOS ---
        with tab_usuarios:
            st.subheader("Control de Acceso")
            with st.expander("➕ Registrar Nuevo Usuario"):
                with st.form("form_nuevo_usuario"):
                    c1, c2, c3 = st.columns(3)
                    with c1: u = st.text_input("Nombre de Usuario")
                    with c2: p = st.text_input("Contraseña", type="password")
                    with c3: r = st.selectbox("Rol/Nivel", self.roles_disponibles)
                    
                    if st.form_submit_button("✅ Guardar Usuario"):
                        if u and p:
                            # Adaptamos al esquema de tu DB (nivel en lugar de rol si es necesario)
                            nuevo_usuario = {
                                "usuario": u.lower().strip(), 
                                "contraseña": p, # Ajustado a tu columna 'contraseña' con ñ
                                "nivel": r,
                                "estado": "activo"
                            }
                            try:
                                self.db.conn.table(self.tabla_perfiles).insert(nuevo_usuario).execute()
                                st.success(f"Usuario {u} creado.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al crear: {e}")

            st.markdown("---")
            st.markdown("### Usuarios Activos")
            try:
                res = self.db.conn.table(self.tabla_perfiles).select("*").execute()
                usuarios = res.data if res.data else []
                
                for user in usuarios:
                    # FIX CRÍTICO: Detectar si la columna es 'rol' o 'nivel'
                    rol_usuario = user.get('rol') if user.get('rol') else user.get('nivel', 'usuario')
                    
                    with st.container(border=True):
                        col_info, col_rol, col_acc = st.columns([2, 2, 1])
                        with col_info:
                            st.write(f"**{user['usuario']}**")
                            st.caption(f"Nivel actual: {rol_usuario}")
                        with col_rol:
                            # Buscamos el índice del rol para el selectbox
                            try:
                                idx = self.roles_disponibles.index(rol_usuario)
                            except:
                                idx = 0
                                
                            nuevo_rol = st.selectbox("Cambiar Nivel", self.roles_disponibles, 
                                                   index=idx,
                                                   key=f"edit_rol_{user['id']}")
                        with col_acc:
                            if st.button("💾", key=f"btn_save_{user['id']}"):
                                # Actualizamos la columna correcta (nivel)
                                self.db.conn.table(self.tabla_perfiles).update({"nivel": nuevo_rol}).eq("id", user['id']).execute()
                                st.toast("Nivel actualizado")
                                st.rerun()
            except Exception as e:
                st.error(f"No se pudieron cargar los usuarios: {e}")

        # --- PESTAÑA 2: DATOS ---
        with tab_datos:
            st.subheader("Centro de Datos")
            col_up, col_down = st.columns(2)
            with col_up:
                st.info("Subir Clientes desde Excel")
                archivo = st.file_uploader("Archivo .xlsx", type=["xlsx"])
                if archivo:
                    df = pd.read_excel(archivo)
                    if st.button("🚀 Procesar Importación"):
                        registros = df.to_dict(orient='records')
                        try:
                            self.db.conn.table("clientes").insert(registros).execute()
                            st.success("¡Importación exitosa!")
                        except Exception as e:
                            st.error(f"Error: {e}")

            with col_down:
                st.info("Descargar Plantilla Clientes")
                df_template = pd.DataFrame(columns=["nombre_completo", "cedula_ruc", "es_extranjero"])
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_template.to_excel(writer, sheet_name='Plantilla', index=False)
                st.download_button("📥 Bajar Formato", data=output.getvalue(), 
                                 file_name="plantilla_clientes.xlsx", use_container_width=True)

        # --- PESTAÑA 3: LOGS ---
        with tab_logs:
            st.subheader("Auditoría")
            try:
                res_logs = self.db.conn.table(self.tabla_logs).select("*").order("fecha", desc=True).limit(100).execute()
                if res_logs.data:
                    st.dataframe(pd.DataFrame(res_logs.data), use_container_width=True)
                else:
                    st.info("Sin actividad reciente.")
            except:
                st.info("Tabla de logs no disponible aún.")

        # --- PESTAÑA 4: MANTENIMIENTO ---
        with tab_mantenimiento:
            st.subheader("Seguridad y Respaldo")
            if st.button("🛠️ Preparar Respaldo de Clientes y Perfiles", use_container_width=True):
                try:
                    c = self.db.conn.table("clientes").select("*").execute().data
                    p = self.db.conn.table("perfiles").select("*").execute().data
                    
                    output_bak = BytesIO()
                    with pd.ExcelWriter(output_bak, engine='xlsxwriter') as writer:
                        pd.DataFrame(c).to_excel(writer, sheet_name='Clientes', index=False)
                        pd.DataFrame(p).to_excel(writer, sheet_name='Usuarios', index=False)
                    
                    st.download_button("⬇️ Descargar Backup", data=output_bak.getvalue(),
                                     file_name=f"BACKUP_SGDA_{datetime.date.today()}.xlsx",
                                     use_container_width=True)
                except Exception as e:
                    st.error(f"Error al generar backup: {e}")