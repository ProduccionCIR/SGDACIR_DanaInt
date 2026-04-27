import os
from pathlib import Path

import streamlit as st
from st_supabase_connection import SupabaseConnection

try:
    from streamlit.errors import StreamlitSecretNotFoundError
except ImportError:
    StreamlitSecretNotFoundError = KeyError


def _cargar_env():
    """Carga .env en la raíz del repo (sin usar st.secrets). Evita errores si no hay secrets.toml."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.is_file():
        load_dotenv(env_path)


def _ruta_secrets_streamlit() -> Path:
    return Path(__file__).resolve().parent / ".streamlit" / "secrets.toml"


def _hay_secrets_toml_streamlit() -> bool:
    """Streamlit solo considera válidos estos archivos; si no existen, st.connection puede fallar."""
    return _ruta_secrets_streamlit().is_file() or (Path.home() / ".streamlit" / "secrets.toml").is_file()


def _credenciales_supabase():
    """Orden: .env → variables de entorno → secrets.toml de Streamlit (solo si el archivo existe)."""
    _cargar_env()
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if url:
        url = str(url).strip()
    if key:
        key = str(key).strip()
    if url and key:
        return url, key
    if _hay_secrets_toml_streamlit():
        try:
            sec = st.secrets["connections"]["supabase"]
            if isinstance(sec, dict):
                if not url:
                    url = sec.get("SUPABASE_URL") or sec.get("url")
                if not key:
                    key = sec.get("SUPABASE_KEY") or sec.get("key")
        except (StreamlitSecretNotFoundError, KeyError, TypeError):
            pass
    if url:
        url = str(url).strip()
    if key:
        key = str(key).strip()
    return url, key


def get_supabase_connection():
    """
    Cliente Supabase. Sin secrets.toml, usa supabase.create_client (no pasa por st.connection,
    que en muchas versiones exige que exista el archivo de secrets de Streamlit).
    """
    url, key = _credenciales_supabase()
    if not url or not key:
        raise ValueError(
            "Faltan SUPABASE_URL y SUPABASE_KEY. Opciones: "
            "(1) Archivo .env en la raíz del proyecto (copie .env.example → .env); "
            "(2) Archivo .streamlit/secrets.toml con [connections.supabase]; "
            "(3) Secretos de Codespaces o export en terminal con SUPABASE_URL y SUPABASE_KEY."
        )
    if not _hay_secrets_toml_streamlit():
        from supabase import create_client

        return create_client(url, key)
    try:
        return st.connection(
            "supabase",
            type=SupabaseConnection,
            url=url,
            key=key,
        )
    except TypeError:
        return st.connection("supabase", type=SupabaseConnection)


class LegalDB:
    def __init__(self):
        self.conn = get_supabase_connection()

    def table(self, tabla):
        return self.conn.table(tabla)

    def fetch(self, tabla):
        """Obtiene datos para Contabilidad y Configuración"""
        try:
            res = self.conn.table(tabla).select("*").execute()
            return res.data if res.data else []
        except Exception as e:
            st.error(f"Error en DB ({tabla}): {e}")
            return []

    def insert(self, tabla, datos):
        """Inserción con manejo de errores de red/API"""
        try:
            return self.conn.table(tabla).insert(datos).execute()
        except Exception as e:
            st.error(f"No se pudo insertar en {tabla}: {e}")
            return None

    def update(self, tabla, datos, id_registro):
        """Actualización para el módulo de Configuración"""
        try:
            return self.conn.table(tabla).update(datos).eq("id", id_registro).execute()
        except Exception as e:
            st.error(f"No se pudo actualizar {tabla} (id={id_registro}): {e}")
            return None
