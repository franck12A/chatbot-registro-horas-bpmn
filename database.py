import sqlite3
from pathlib import Path
from contextlib import contextmanager


# ==========================================================
# PERSISTENCIA SQLITE
# ----------------------------------------------------------
# SQLite se utiliza para brindar persistencia ligera, local y
# transaccional del proceso de registro. Es adecuado para un TP
# integrador académico porque no requiere servidor externo y
# facilita el trazado del flujo de conversaciones.
# ==========================================================
DB_PATH = Path("empresa.db")

# ==========================================================
# DATOS INICIALES DE PRUEBA
# ----------------------------------------------------------
# Conjunto de empleados precargados utilizado para simular
# una base organizacional real. Estos registros permiten
# validar el flujo BPMN sin necesidad de carga manual de
# información durante las pruebas del sistema.
# ==========================================================
EMPLEADOS_INICIALES = [
    ("Martin Gonzalez", "20-12345678-3", "Tiempo Completo", "Ana Perez"),
    ("Lucia Fernandez", "27-23456789-4", "Tiempo Parcial", "Carlos Ruiz"),
    ("Nicolas Romero", "20-34567890-5", "Tiempo Completo", "Ana Perez"),
    ("Camila Torres", "27-45678901-6", "Tiempo Parcial", "Marta Silva"),
    ("Santiago Lopez", "20-56789012-7", "Tiempo Completo", "Carlos Ruiz"),
    ("Valentina Diaz", "27-67890123-8", "Tiempo Parcial", "Marta Silva"),
    ("Mateo Herrera", "20-78901234-9", "Tiempo Completo", "Ana Perez"),
    ("Florencio Beneddeti de la cruz", "20-89012345-0", "Tiempo Completo", "Carlos Ruiz"),
    ("Eutanacio Benitez", "20-90123456-1", "Tiempo Parcial", "Marta Silva"),
]


@contextmanager
def conectar():
    # ==========================================================
    # CONTEXTO DE CONEXIÓN
    # ----------------------------------------------------------
    # Provee un manejador de conexión que asegura commit/rollback
    # y el cierre adecuado de recursos. El uso de sqlite3.Row
    # facilita el acceso por nombre de columna en la lógica de
    # negocio del chatbot.
    # ==========================================================
    conexion = sqlite3.connect(DB_PATH)
    conexion.row_factory = sqlite3.Row
    try:
        yield conexion
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def inicializar_base():
    with conectar() as conexion:
        # ==========================================================
        # ESCHEMA DE PERSISTENCIA
        # ----------------------------------------------------------
        # Define las tablas necesarias para empleados, registros y
        # sesiones. Este esquema refleja los elementos persistentes
        # del proceso BPMN: identidad del empleado, datos de tiempo
        # y estado de la conversación.
        # ==========================================================
        conexion.execute(
            """
            CREATE TABLE IF NOT EXISTS empleados (
                id INTEGER PRIMARY KEY,
                nombre TEXT NOT NULL,
                cuil TEXT NOT NULL,
                modalidad TEXT NOT NULL,
                supervisor TEXT NOT NULL
            )
            """
        )
        conexion.execute(
            """
            CREATE TABLE IF NOT EXISTS registros (
                id INTEGER PRIMARY KEY,
                empleado_id INTEGER NOT NULL,
                fecha TEXT NOT NULL,
                hora_ingreso TEXT NOT NULL,
                hora_salida TEXT NOT NULL,
                horas_trabajadas REAL NOT NULL,
                horas_extra REAL NOT NULL,
                estado TEXT NOT NULL,
                FOREIGN KEY (empleado_id) REFERENCES empleados(id)
            )
            """
        )
        conexion.execute(
            """
            CREATE TABLE IF NOT EXISTS sesiones (
                id INTEGER PRIMARY KEY,
                usuario TEXT,
                estado_actual TEXT
            )
            """
        )
        _sembrar_empleados(conexion)


def _sembrar_empleados(conexion):
    # ==========================================================
    # CARGA INICIAL DE EMPLEADOS
    # ----------------------------------------------------------
    # Inserta automáticamente los empleados de prueba cuando
    # la base de datos se crea por primera vez. Esta técnica
    # (seeding) asegura que el sistema disponga de datos válidos
    # para ejecutar las validaciones del proceso.
    # ==========================================================
    total = conexion.execute("SELECT COUNT(*) FROM empleados").fetchone()[0]
    if total > 0:
        return

    conexion.executemany(
        """
        INSERT INTO empleados (nombre, cuil, modalidad, supervisor)
        VALUES (?, ?, ?, ?)
        """,
        EMPLEADOS_INICIALES,
    )


def buscar_empleado_por_nombre(nombre):
    # ==========================================================
    # CONSULTA SQLITE: BÚSQUEDA DE EMPLEADO
    # ----------------------------------------------------------
    # Localiza al empleado por nombre, soportando comparación
    # case-insensitive. Esta función es parte del gateway de
    # validación inicial del proceso de registro.
    # ==========================================================
    with conectar() as conexion:
        return conexion.execute(
            """
            SELECT id, nombre, cuil, modalidad, supervisor
            FROM empleados
            WHERE lower(nombre) = lower(?)
            """,
            (nombre.strip(),),
        ).fetchone()


def buscar_empleado_por_id(empleado_id):
    # ==========================================================
    # CONSULTA SQLITE: BÚSQUEDA POR IDENTIFICADOR
    # ----------------------------------------------------------
    # Recupera un empleado mediante su clave primaria. Aunque
    # no forma parte del flujo principal, permite futuras
    # extensiones y mantiene encapsulado el acceso a datos.
    # ==========================================================
    with conectar() as conexion:
        return conexion.execute(
            """
            SELECT id, nombre, cuil, modalidad, supervisor
            FROM empleados
            WHERE id = ?
            """,
            (empleado_id,),
        ).fetchone()


def obtener_registro_por_fecha(empleado_id, fecha):
    # ==========================================================
    # CONSULTA SQLITE: VERIFICACIÓN DE REGISTRO EXISTENTE
    # ----------------------------------------------------------
    # Recupera el último registro para un empleado en una fecha
    # determinada. Esto permite detectar duplicados y habilitar
    # la ruta de rectificación en el flujo.
    # ==========================================================
    with conectar() as conexion:
        return conexion.execute(
            """
            SELECT id, empleado_id, fecha, hora_ingreso, hora_salida,
                   horas_trabajadas, horas_extra, estado
            FROM registros
            WHERE empleado_id = ? AND fecha = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (empleado_id, fecha),
        ).fetchone()


def guardar_registro(
    empleado_id,
    fecha,
    hora_ingreso,
    hora_salida,
    horas_trabajadas,
    horas_extra,
    estado,
    rectificar=False,
):
    # ==========================================================
    # CONSULTA SQLITE: GUARDADO Y RECTIFICACIÓN DE REGISTRO
    # ----------------------------------------------------------
    # Inserta un nuevo registro de horas o actualiza uno existente
    # si se trata de una rectificación. Esta decisión preserva la
    # historia de la sesión y evita duplicados mientras se mantiene
    # la trazabilidad académica.
    # ==========================================================
    with conectar() as conexion:
        existente = obtener_registro_por_fecha(empleado_id, fecha)
        if rectificar and existente:
            conexion.execute(
                """
                UPDATE registros
                SET hora_ingreso = ?,
                    hora_salida = ?,
                    horas_trabajadas = ?,
                    horas_extra = ?,
                    estado = ?
                WHERE id = ?
                """,
                (
                    hora_ingreso,
                    hora_salida,
                    horas_trabajadas,
                    horas_extra,
                    estado,
                    existente["id"],
                ),
            )
            return existente["id"]

        cursor = conexion.execute(
            """
            INSERT INTO registros (
                empleado_id, fecha, hora_ingreso, hora_salida,
                horas_trabajadas, horas_extra, estado
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                empleado_id,
                fecha,
                hora_ingreso,
                hora_salida,
                horas_trabajadas,
                horas_extra,
                estado,
            ),
        )
        return cursor.lastrowid


def listar_registros(limite=20):
    # ==========================================================
    # CONSULTA SQLITE: LISTADO DE REGISTROS
    # ----------------------------------------------------------
    # Recupera los registros almacenados junto con los datos del
    # empleado asociado mediante una operación JOIN. Esta función
    # alimenta el panel de consulta disponible en la interfaz.
    # ==========================================================
    with conectar() as conexion:
        return conexion.execute(
            """
            SELECT r.id, e.nombre, e.cuil, e.modalidad, e.supervisor,
                   r.fecha, r.hora_ingreso, r.hora_salida,
                   r.horas_trabajadas, r.horas_extra, r.estado
            FROM registros r
            JOIN empleados e ON e.id = r.empleado_id
            ORDER BY r.id DESC
            LIMIT ?
            """,
            (limite,),
        ).fetchall()


def guardar_sesion(usuario, estado_actual):
    # ==========================================================
    # GUARDADO DE SESIÓN
    # ----------------------------------------------------------
    # Persiste el usuario y el estado actual de la conversación
    # para permitir recuperación de sesión y continuidad del
    # flujo en la máquina de estados entre ejecuciones.
    # ==========================================================
    with conectar() as conexion:
        conexion.execute(
            """
            INSERT INTO sesiones (id, usuario, estado_actual)
            VALUES (1, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                usuario = excluded.usuario,
                estado_actual = excluded.estado_actual
            """,
            (usuario, estado_actual),
        )


def obtener_sesion():
    # ==========================================================
    # RECUPERACIÓN DE SESIÓN
    # ----------------------------------------------------------
    # Obtiene el estado persistido de la conversación para que
    # la máquina de estados pueda continuar el proceso desde el
    # último punto registrado.
    # ==========================================================
    with conectar() as conexion:
        return conexion.execute(
            "SELECT usuario, estado_actual FROM sesiones WHERE id = 1"
        ).fetchone()


def limpiar_sesion():
    # ==========================================================
    # REINICIO DE SESIÓN
    # ----------------------------------------------------------
    # Restablece la información de sesión almacenada en SQLite,
    # devolviendo el flujo al estado inicial del chatbot.
    # ==========================================================
    guardar_sesion(None, "inicio")

def limpiar_registros():
    # ==========================================================
    # ELIMINACIÓN DE REGISTROS
    # ----------------------------------------------------------
    # Borra todos los registros de horas almacenados en la base
    # de datos. Esta operación se utiliza principalmente para
    # pruebas y reinicio de escenarios durante la ejecución.
    # ==========================================================
    with conectar() as conexion:
        conexion.execute("DELETE FROM registros")