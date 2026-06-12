# ==========================================================
# DEFINICIÓN DE ESTADOS DE LA MÁQUINA DE ESTADOS
# ----------------------------------------------------------
# Este módulo centraliza todos los estados utilizados por el
# chatbot durante la ejecución del proceso BPMN de registro
# y aprobación de horas trabajadas.
#
# Mantener los estados en un archivo independiente mejora la
# mantenibilidad, evita errores por cadenas duplicadas y
# facilita la validación del flujo de negocio.
# ==========================================================
ESTADO_INICIO = "inicio"
ESTADO_NOMBRE = "nombre"
ESTADO_CUIL = "cuil"
ESTADO_FECHA = "fecha"
ESTADO_VERIFICAR_REGISTRO = "verificar_registro"
ESTADO_RECTIFICAR = "rectificar"
ESTADO_HORA_INGRESO = "hora_ingreso"
ESTADO_HORA_SALIDA = "hora_salida"
ESTADO_CALCULO_HORAS = "calculo_horas"
ESTADO_CONFIRMACION = "confirmacion"
ESTADO_AUTORIZACION_SUPERVISOR = "autorizacion_supervisor"
ESTADO_RRHH = "rrhh"
ESTADO_FINAL = "final"
ESTADO_CANCELADO = "cancelado"

# ==========================================================
# CONJUNTO DE ESTADOS VÁLIDOS
# ----------------------------------------------------------
# Se utiliza para verificar que el estado recuperado desde
# la sesión almacenada en SQLite pertenezca a la máquina de
# estados definida. Esto evita inconsistencias y protege la
# continuidad del proceso ante errores o modificaciones.
# ==========================================================
ESTADOS_VALIDOS = {
    ESTADO_INICIO,
    ESTADO_NOMBRE,
    ESTADO_CUIL,
    ESTADO_FECHA,
    ESTADO_VERIFICAR_REGISTRO,
    ESTADO_RECTIFICAR,
    ESTADO_HORA_INGRESO,
    ESTADO_HORA_SALIDA,
    ESTADO_CALCULO_HORAS,
    ESTADO_CONFIRMACION,
    ESTADO_AUTORIZACION_SUPERVISOR,
    ESTADO_RRHH,
    ESTADO_FINAL,
    ESTADO_CANCELADO,
}
