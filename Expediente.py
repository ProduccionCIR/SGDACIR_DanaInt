class Expediente:
    def __init__(self, db_manager):
        # Usamos db_manager.conn para asegurar acceso a los métodos de Supabase
        self.db = db_manager.conn if hasattr(db_manager, 'conn') else db_manager
        self.tabla = "expedientes"

    def crear(self, datos):
        return self.db.table(self.tabla).insert(datos).execute()

    def obtener_todos(self):
        return self.db.table(self.tabla).select("*, clientes(nombre_completo)").execute()

    def buscar_por_id(self, exp_id):
        return self.db.table(self.tabla).select("*, clientes(*)").eq("id", exp_id).single().execute()

    def actualizar(self, exp_id, nuevos_datos):
        return self.db.table(self.tabla).update(nuevos_datos).eq("id", exp_id).execute()

    # --- Gestión de Actuaciones (Historial) ---
    def agregar_actuacion(self, expediente_id, descripcion, fecha=None):
        from datetime import datetime
        datos = {
            "expediente_id": expediente_id,
            "descripcion": descripcion,
            "fecha_actuacion": fecha if fecha else datetime.now().date().isoformat()
        }
        return self.db.table("actuaciones").insert(datos).execute()

    def obtener_actuaciones(self, expediente_id):
        return self.db.table("actuaciones").select("*").eq("expediente_id", expediente_id).order("fecha_actuacion", desc=True).execute()