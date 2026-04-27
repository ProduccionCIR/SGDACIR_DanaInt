"""
Vista mínima para comprobar credenciales y API de Supabase con Streamlit.
Ejecutar: streamlit run test_supabase_streamlit.py
"""
import streamlit as st
from SupabaseConnection import get_supabase_connection

st.set_page_config(page_title="Prueba Supabase", layout="centered")
st.title("Prueba de conexión Supabase")
st.caption("Credenciales: .streamlit/secrets.toml o variables de entorno SUPABASE_URL y SUPABASE_KEY.")

try:
    conn = get_supabase_connection()
except ValueError as e:
    st.error(str(e))
    st.stop()
except Exception as e:
    st.error(f"No se pudo inicializar la conexión: {e}")
    st.stop()

st.success("Cliente de conexión creado (st.connection + SupabaseConnection).")

st.subheader("Consulta de prueba")
tabla_prueba = st.text_input("Tabla a consultar (ej. usuarios)", value="usuarios")

if st.button("Ejecutar SELECT limit 1"):
    try:
        r = conn.table(tabla_prueba).select("*").limit(1).execute()
        st.write("**Filas (máx. 1):**", r.data if r.data is not None else [])
        st.success("Petición REST a PostgREST completada.")
    except Exception as e:
        st.error(f"Error en la consulta (tabla, RLS o red): {e}")

st.divider()
st.info(
    "Si falla aquí pero las credenciales son correctas, revise en Supabase: "
    "nombre de la tabla, políticas RLS y que la clave anónima tenga permiso."
)
