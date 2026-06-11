import sqlite3
from pathlib import Path
from contextlib import contextmanager


DB_PATH = Path("empresa.db")


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
    with conectar() as conexion:
        return conexion.execute(
            "SELECT usuario, estado_actual FROM sesiones WHERE id = 1"
        ).fetchone()


def limpiar_sesion():
    guardar_sesion(None, "inicio")

def limpiar_registros():
    with conectar() as conexion:
        conexion.execute("DELETE FROM registros")