import streamlit as st

class AuthManager:
    def __init__(self, db_manager):
        self.db = db_manager

    def iniciar_sesion(self, usuario_o_email, password):
        try:
            # Consultamos la tabla 'perfiles' en lugar del sistema de Auth nativo
            # Buscamos por la columna 'usuario' o 'email' y validamos la 'contraseña'
            res = self.db.conn.table("perfiles") \
                .select("*") \
                .eq("usuario", usuario_o_email) \
                .eq("contraseña", password) \
                .eq("estado", "activo") \
                .execute()

            if res.data and len(res.data) > 0:
                user_data = res.data[0]
                # Guardamos el usuario en el estado de la sesión de Streamlit
                st.session_state.usuario_actual = user_data
                return user_data
            else:
                st.error("Credenciales incorrectas o usuario inactivo.")
                return None
                
        except Exception as e:
            st.error(f"Error crítico de conexión: {str(e)}")
            return None

    def cerrar_sesion(self):
        # Limpiamos el estado de la sesión
        if "usuario_actual" in st.session_state:
            del st.session_state.usuario_actual
        st.rerun()

    def verificar_sesion(self):
        # Verificamos si existe el objeto en el session_state
        return st.session_state.get("usuario_actual", None)