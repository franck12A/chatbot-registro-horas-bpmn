# ==========================================================
# IMPORTACIONES CLAVE
# ----------------------------------------------------------
# Se utiliza datetime para el tratamiento de formatos de fecha
# y hora, re/unicodedata para normalizar entradas de texto,
# y rapidfuzz para interpretar respuestas del usuario con
# tolerancia a errores tipográficos. Esta combinación permite
# mantener la lógica de negocio estable ante variaciones en
# la interacción conversacional.
# ==========================================================
from datetime import datetime
import re
import unicodedata

from rapidfuzz import fuzz

import database
from estados import (
    ESTADO_AUTORIZACION_SUPERVISOR,
    ESTADO_CALCULO_HORAS,
    ESTADO_CANCELADO,
    ESTADO_CONFIRMACION,
    ESTADO_CUIL,
    ESTADO_FECHA,
    ESTADO_FINAL,
    ESTADO_HORA_INGRESO,
    ESTADO_HORA_SALIDA,
    ESTADO_INICIO,
    ESTADO_NOMBRE,
    ESTADO_RECTIFICAR,
    ESTADO_RRHH,
    ESTADO_VERIFICAR_REGISTRO,
    ESTADOS_VALIDOS,
)


# ==========================================================
# CONSTANTES DE VALIDACIÓN Y CONTROL DE FLUJO
# ----------------------------------------------------------
# MAX_INTENTOS define el umbral de reintentos para cada paso
# de la máquina de estados. Los patrones regulares determinan
# formatos válidos para CUIL y hora, garantizando consistencia
# en el registro de datos y evitando errores de procesamiento.
# ==========================================================
MAX_INTENTOS = 3
FORMATO_CUIL = re.compile(r"^\d{2}-\d{8}-\d$")
FORMATO_HORA = re.compile(r"^\d{2}:\d{2}$")


# ==========================================================
# FUNCIONES AUXILIARES DE INTERPRETACIÓN Y VALIDACIÓN
# ----------------------------------------------------------
# Estas funciones apoyan la lógica del chatbot fuera de la
# máquina de estados principal. Permiten normalizar el texto,
# interpretar confirmaciones, detectar cancelaciones y validar
# fechas/horas antes de avanzar en el proceso de BPMN.
# ==========================================================
def normalizar_texto(texto):
    texto_limpio = texto.strip().lower()
    texto_limpio = unicodedata.normalize("NFD", texto_limpio)
    return "".join(
        caracter for caracter in texto_limpio
        if unicodedata.category(caracter) != "Mn"
    )


def interpretar_respuesta(texto):
    afirmaciones = ["si", "sii", "siii", "sip", "ok", "dale", "confirmo"]
    negativas = ["no", "nop", "cancelar", "negativo"]
    texto_normalizado = normalizar_texto(texto)

    if texto_normalizado in afirmaciones:
        return "SI"
    if texto_normalizado in negativas:
        return "NO"

    mejor_si = max(fuzz.ratio(texto_normalizado, opcion) for opcion in afirmaciones)
    mejor_no = max(fuzz.ratio(texto_normalizado, opcion) for opcion in negativas)

    if mejor_si >= 75 and mejor_si > mejor_no:
        return "SI"
    if mejor_no >= 75 and mejor_no > mejor_si:
        return "NO"
    return None


def es_cancelacion(texto):
    return normalizar_texto(texto) == "cancelar"


def validar_fecha(texto):
    try:
        fecha = datetime.strptime(texto, "%d/%m/%Y")
        return fecha.strftime("%d/%m/%Y")
    except ValueError:
        return None


def validar_hora(texto):
    if not FORMATO_HORA.match(texto):
        return None
    try:
        return datetime.strptime(texto, "%H:%M").strftime("%H:%M")
    except ValueError:
        return None


def calcular_horas(fecha, hora_ingreso, hora_salida):
    ingreso = datetime.strptime(f"{fecha} {hora_ingreso}", "%d/%m/%Y %H:%M")
    salida = datetime.strptime(f"{fecha} {hora_salida}", "%d/%m/%Y %H:%M")
    if salida <= ingreso:
        return None
    return round((salida - ingreso).total_seconds() / 3600, 2)


def jornada_por_modalidad(modalidad):
    if normalizar_texto(modalidad) == "tiempo parcial":
        return 4
    return 8


# ==========================================================
# CLASE PRINCIPAL: CHATBOT DE REGISTRO DE HORAS
# ----------------------------------------------------------
# Representa la máquina de estados que guía al usuario por el
# proceso de registro de horas. Cada estado corresponde a un
# paso del diagrama BPMN: validación de empleado, ingreso de
# datos, verificación de duplicados, confirmación y aprobación.
# ==========================================================
class ChatbotRegistroHoras:
    def __init__(self):
        database.inicializar_base()
        sesion = database.obtener_sesion()
        estado_guardado = sesion["estado_actual"] if sesion else ESTADO_INICIO
        usuario_guardado = sesion["usuario"] if sesion else None

        self.estado = estado_guardado if estado_guardado in ESTADOS_VALIDOS else ESTADO_INICIO
        self.empleado = database.buscar_empleado_por_nombre(usuario_guardado) if usuario_guardado else None
        self.fecha = None
        self.hora_ingreso = None
        self.hora_salida = None
        self.horas_trabajadas = 0
        self.horas_extra = 0
        self.rectificar = False
        self.intentos = {
            ESTADO_NOMBRE: 0,
            ESTADO_CUIL: 0,
            ESTADO_FECHA: 0,
            ESTADO_HORA_INGRESO: 0,
            ESTADO_HORA_SALIDA: 0,
            ESTADO_RECTIFICAR: 0,
            ESTADO_CONFIRMACION: 0,
            ESTADO_AUTORIZACION_SUPERVISOR: 0,
        }

        if self.estado not in [ESTADO_INICIO, ESTADO_NOMBRE] and not self.empleado:
            self.estado = ESTADO_NOMBRE
            self._persistir_sesion()

    def iniciar(self):
        # ==========================================================
        # INICIO DEL PROCESO BPMN
        # ----------------------------------------------------------
        # Al arrancar o terminar un ciclo, el chatbot evalúa si debe
        # reiniciar el proceso completo. Este método conecta la fase
        # inicial del BPMN con la siguiente tarea: ingreso de nombre.
        # ==========================================================
        if self.estado in [ESTADO_FINAL, ESTADO_CANCELADO]:
            self._reiniciar_proceso()

        respuestas = []
        if self.estado == ESTADO_INICIO:
            respuestas.append(
                "Hola, bienvenido al proceso de registro y aprobacion de horas trabajadas."
            )
            self.estado = ESTADO_NOMBRE
            self._persistir_sesion()

        respuestas.extend(self._mensaje_estado_actual())
        return respuestas

    def procesar_entrada(self, texto):
        texto = texto.strip()
        if not texto:
            return ["Ingrese un valor para continuar."]

        if es_cancelacion(texto):
            return self.cancelar_proceso()

        if self.estado == ESTADO_INICIO:
            return self.iniciar()
        if self.estado == ESTADO_NOMBRE:
            return self._procesar_nombre(texto)
        if self.estado == ESTADO_CUIL:
            return self._procesar_cuil(texto)
        if self.estado == ESTADO_FECHA:
            return self._procesar_fecha(texto)
        if self.estado == ESTADO_RECTIFICAR:
            return self._procesar_rectificacion(texto)
        if self.estado == ESTADO_HORA_INGRESO:
            return self._procesar_hora_ingreso(texto)
        if self.estado == ESTADO_HORA_SALIDA:
            return self._procesar_hora_salida(texto)
        if self.estado == ESTADO_CONFIRMACION:
            return self._procesar_confirmacion(texto)
        if self.estado == ESTADO_AUTORIZACION_SUPERVISOR:
            return self._procesar_supervisor(texto)
        if self.estado in [ESTADO_FINAL, ESTADO_CANCELADO]:
            self._reiniciar_proceso()
            return self.iniciar()

        # ==========================================================
        # GATEWAY DE RECUPERACIÓN
        # ----------------------------------------------------------
        # Si el estado no corresponde a ninguno de los definidos,
        # se retorna al inicio para evitar que el flujo quede en un
        # estado no válido. Esto protege la consistencia de la sesión.
        # ==========================================================
        self.estado = ESTADO_INICIO
        self._persistir_sesion()
        return self.iniciar()

    def cancelar_proceso(self):
        self.estado = ESTADO_CANCELADO
        self._persistir_sesion()
        self._reiniciar_proceso()
        return ["Proceso cancelado. Se reinicio la sesion administrativa."]

    def obtener_usuario_actual(self):
        if not self.empleado:
            return "Sin usuario"
        return self.empleado["nombre"]

    def obtener_estado_actual(self):
        return self.estado

    def obtener_modalidad_actual(self):
        if not self.empleado:
            return "Sin modalidad"
        return self.empleado["modalidad"]

    def obtener_supervisor_actual(self):
        if not self.empleado:
            return "Sin supervisor"
        return self.empleado["supervisor"]

    def _procesar_nombre(self, nombre):
        # ==========================================================
        # GATEWAY BPMN: VALIDACIÓN DE EMPLEADO
        # ----------------------------------------------------------
        # Verifica si el nombre del empleado existe en la tabla de
        # empleados. Si el empleado es válido, el flujo continúa al
        # estado de validación de CUIL; de lo contrario, se solicita
        # reingresar el nombre.
        # ==========================================================       
        empleado = database.buscar_empleado_por_nombre(nombre)
        if empleado:
            self.empleado = empleado
            self._reiniciar_intentos(ESTADO_NOMBRE)
            self.estado = ESTADO_CUIL
            self._persistir_sesion()
            return [
                f"Empleado validado: {empleado['nombre']}.",
                "Ingrese el CUIL con formato XX-XXXXXXXX-X:",
            ]

        return self._fallar_o_reintentar(
            ESTADO_NOMBRE,
            "Empleado inexistente.",
            "Ingrese nuevamente el nombre del empleado:",
        )

    def _procesar_cuil(self, cuil):
        # ==========================================================
        # GATEWAY BPMN: VALIDACIÓN DE CUIL
        # ----------------------------------------------------------
        # Comprueba que el formato del CUIL sea correcto y que
        # corresponda al empleado previamente validado. Esta etapa
        # garantiza la identidad del usuario antes de continuar con
        # el registro de horas trabajadas.
        # ==========================================================
        if not FORMATO_CUIL.match(cuil):
            return self._fallar_o_reintentar(
                ESTADO_CUIL,
                "CUIL invalido. Debe respetar el formato XX-XXXXXXXX-X.",
                "Ingrese nuevamente el CUIL:",
            )

        if self.empleado and cuil == self.empleado["cuil"]:
            self._reiniciar_intentos(ESTADO_CUIL)
            self.estado = ESTADO_FECHA
            self._persistir_sesion()
            return ["CUIL validado correctamente.", "Ingrese la fecha (DD/MM/AAAA):"]

        return self._fallar_o_reintentar(
            ESTADO_CUIL,
            "El CUIL ingresado no coincide con el empleado validado.",
            "Ingrese nuevamente el CUIL:",
        )

    def _procesar_fecha(self, texto):
        # ==========================================================
        # VALIDACIÓN DE FECHA DEL REGISTRO
        # ----------------------------------------------------------
        # Verifica que la fecha ingresada respete el formato
        # DD/MM/AAAA. Una vez validada, el flujo avanza hacia la
        # comprobación de registros existentes para evitar
        # duplicidades en la base de datos.
        # ==========================================================
        fecha = validar_fecha(texto)
        if not fecha:
            return self._fallar_o_reintentar(
                ESTADO_FECHA,
                "Fecha invalida. Use el formato DD/MM/AAAA.",
                "Ingrese nuevamente la fecha:",
            )

        self.fecha = fecha
        self._reiniciar_intentos(ESTADO_FECHA)
        self.estado = ESTADO_VERIFICAR_REGISTRO
        self._persistir_sesion()
        return self._verificar_registro_existente()

    def _verificar_registro_existente(self):
        # ==========================================================
        # GATEWAY BPMN: VERIFICACIÓN DE DUPLICIDAD
        # ----------------------------------------------------------
        # Comprueba si ya existe un registro para el empleado en la
        # fecha seleccionada. Si hay un duplicado, el proceso ofrece
        # rectificación; si no, avanza al ingreso de horas.
        # ==========================================================
        existente = database.obtener_registro_por_fecha(self.empleado["id"], self.fecha)
        if existente:
            self.estado = ESTADO_RECTIFICAR
            self._persistir_sesion()
            return [
                "Ya existe un registro para ese empleado y fecha.",
                "Desea rectificarlo? (si/no)",
            ]

        self.estado = ESTADO_HORA_INGRESO
        self._persistir_sesion()
        return ["No se encontraron registros previos para este empleado en la fecha seleccionada.", "Ingrese hora de ingreso (HH:MM):"]

    def _procesar_rectificacion(self, respuesta):
        # ==========================================================
        # GATEWAY BPMN: DECISIÓN DE RECTIFICACIÓN
        # ----------------------------------------------------------
        # Si el usuario decide rectificar un registro existente, el
        # flujo regresa al ingreso de horas con una bandera que
        # habilita la actualización en la base de datos.
        # En caso negativo, se finaliza el proceso para evitar
        # duplicar registros.
        # ==========================================================
        decision = interpretar_respuesta(respuesta)
        if decision == "SI":
            self.rectificar = True
            self._reiniciar_intentos(ESTADO_RECTIFICAR)
            self.estado = ESTADO_HORA_INGRESO
            self._persistir_sesion()
            return ["Rectificacion habilitada.", "Ingrese hora de ingreso (HH:MM):"]

        if decision == "NO":
            return self._finalizar_sin_guardar(
                "Operacion finalizada para evitar un registro duplicado."
            )

        return self._fallar_o_reintentar(
            ESTADO_RECTIFICAR,
            "Responda si o no.",
            "Desea rectificarlo? (si/no)",
        )

    def _procesar_hora_ingreso(self, texto):
        hora = validar_hora(texto)
        if not hora:
            return self._fallar_o_reintentar(
                ESTADO_HORA_INGRESO,
                "Hora de ingreso invalida. Use el formato HH:MM.",
                "Ingrese nuevamente la hora de ingreso:",
            )

        self.hora_ingreso = hora
        self._reiniciar_intentos(ESTADO_HORA_INGRESO)
        self.estado = ESTADO_HORA_SALIDA
        self._persistir_sesion()
        return ["Ingrese hora de salida (HH:MM):"]

    def _procesar_hora_salida(self, texto):
        hora = validar_hora(texto)
        if not hora:
            return self._fallar_o_reintentar(
                ESTADO_HORA_SALIDA,
                "Hora de salida invalida. Use el formato HH:MM.",
                "Ingrese nuevamente la hora de salida:",
            )

        horas = calcular_horas(self.fecha, self.hora_ingreso, hora)
        if horas is None:
            return self._fallar_o_reintentar(
                ESTADO_HORA_SALIDA,
                "La hora de salida debe ser posterior a la hora de ingreso.",
                "Ingrese nuevamente la hora de salida:",
            )

        self.hora_salida = hora
        self.horas_trabajadas = horas
        self.estado = ESTADO_CALCULO_HORAS
        self._persistir_sesion()
        return self._calcular_y_resumir()

    def _calcular_y_resumir(self):
        # ==========================================================
        # CÁLCULO DE HORAS Y RESUMEN
        # ----------------------------------------------------------
        # Calcula las horas trabajadas y las horas extras en función
        # de la modalidad de empleo. Esta etapa corresponde a una
        # tarea de negocio donde la regla de cálculo se aplica antes
        # de solicitar confirmación.
        # ==========================================================
        jornada = jornada_por_modalidad(self.empleado["modalidad"])
        self.horas_extra = round(max(0, self.horas_trabajadas - jornada), 2)
        self.estado = ESTADO_CONFIRMACION
        self._persistir_sesion()
        return [
            "Resumen del registro:",
            f"Empleado: {self.empleado['nombre']}",
            f"Fecha: {self.fecha}",
            f"Ingreso: {self.hora_ingreso}",
            f"Salida: {self.hora_salida}",
            f"Horas trabajadas: {self.horas_trabajadas}",
            f"Horas extra: {self.horas_extra}",
            "Confirma el registro? (si/no)",
        ]

    def _procesar_confirmacion(self, respuesta):
        # ==========================================================
        # GATEWAY BPMN: DECISIÓN DEL USUARIO SOBRE EL RESUMEN
        # ----------------------------------------------------------
        # El chatbot presenta un resumen de los datos ingresados y
        # pide confirmación. Esta decisión determina si el registro
        # avanza hacia la autorización o si requiere una corrección.
        # ==========================================================
        decision = interpretar_respuesta(respuesta)
        if decision == "SI":
            self._reiniciar_intentos(ESTADO_CONFIRMACION)
            self.estado = ESTADO_AUTORIZACION_SUPERVISOR
            self._persistir_sesion()
            return [
                f"Solicitud enviada al supervisor {self.empleado['supervisor']}.",
                "El supervisor aprueba la solicitud? (si/no)",
            ]

        if decision == "NO":
            self.estado = ESTADO_HORA_INGRESO
            self._persistir_sesion()
            return ["Volvemos a editar el registro.", "Ingrese hora de ingreso (HH:MM):"]

        return self._fallar_o_reintentar(
            ESTADO_CONFIRMACION,
            "Responda si o no.",
            "Confirma el registro? (si/no)",
        )

    def _procesar_supervisor(self, respuesta):
        # ==========================================================
        # GATEWAY BPMN: APROBACIÓN DEL SUPERVISOR
        # ----------------------------------------------------------
        # Representa la revisión de un supervisor. Una aprobación
        # mueve el registro al área de Recursos Humanos; un rechazo
        # guarda el estado RECHAZADO y cierra el ciclo.
        # ==========================================================
        decision = interpretar_respuesta(respuesta)
        if decision == "SI":
            self._reiniciar_intentos(ESTADO_AUTORIZACION_SUPERVISOR)
            self.estado = ESTADO_RRHH
            self._persistir_sesion()
            return self._procesar_rrhh()

        if decision == "NO":
            self._guardar_registro("RECHAZADO")
            return self._finalizar_sin_guardar(
                "Solicitud rechazada por el supervisor. Estado: RECHAZADO."
            )

        return self._fallar_o_reintentar(
            ESTADO_AUTORIZACION_SUPERVISOR,
            "Responda si o no.",
            "El supervisor aprueba la solicitud? (si/no)",
        )

    def _procesar_rrhh(self):
        # ==========================================================
        # TAREA DE RRHH Y PERSISTENCIA FINAL
        # ----------------------------------------------------------
        # En esta instancia se materializa la persistencia del
        # registro final en SQLite. Se asume que Recursos Humanos
        # aprueba el registro y se cierra el ciclo de negocio.
        # ==========================================================
        self._guardar_registro("APROBADO")
        mensajes = [
            "Registro enviado a Recursos Humanos.",
            "Recursos Humanos aprobo y guardo el registro en SQLite.",
            "Proceso finalizado.",
        ]
        self.estado = ESTADO_FINAL
        self._persistir_sesion()
        self._reiniciar_proceso()
        return mensajes

    def _guardar_registro(self, estado):
        # ==========================================================
        # PERSISTENCIA DE REGISTRO EN BASE DE DATOS
        # ----------------------------------------------------------
        # Centraliza la escritura del registro en SQLite, manteniendo
        # la separación entre la lógica de negocio del chatbot y el
        # acceso a datos. El flag rectificar permite actualizar una
        # entrada existente cuando corresponde.
        # ==========================================================
        database.guardar_registro(
            self.empleado["id"],
            self.fecha,
            self.hora_ingreso,
            self.hora_salida,
            self.horas_trabajadas,
            self.horas_extra,
            estado,
            rectificar=self.rectificar,
        )

    def _mensaje_estado_actual(self):
        if self.estado == ESTADO_NOMBRE:
            return ["Ingrese el nombre del empleado:"]
        if self.estado == ESTADO_CUIL:
            return ["Ingrese el CUIL con formato XX-XXXXXXXX-X:"]
        if self.estado == ESTADO_FECHA:
            return ["Ingrese la fecha (DD/MM/AAAA):"]
        if self.estado == ESTADO_RECTIFICAR:
            return ["Desea rectificarlo? (si/no)"]
        if self.estado == ESTADO_HORA_INGRESO:
            return ["Ingrese hora de ingreso (HH:MM):"]
        if self.estado == ESTADO_HORA_SALIDA:
            return ["Ingrese hora de salida (HH:MM):"]
        if self.estado == ESTADO_CONFIRMACION:
            return ["Confirma el registro? (si/no)"]
        if self.estado == ESTADO_AUTORIZACION_SUPERVISOR:
            return ["El supervisor aprueba la solicitud? (si/no)"]
        return []

    def _fallar_o_reintentar(self, estado_intento, error, siguiente_mensaje):
        # ==========================================================
        # CONTROL DE ERRORES Y REINTENTOS
        # ----------------------------------------------------------
        # Gestiona los intentos permitidos para cada estado de la
        # conversación. Cuando el usuario supera el límite definido,
        # el proceso se cancela automáticamente para evitar ciclos
        # infinitos y mantener la robustez del sistema.
        # ==========================================================
        self.intentos[estado_intento] += 1
        if self.intentos[estado_intento] >= MAX_INTENTOS:
            self.estado = ESTADO_CANCELADO
            self._persistir_sesion()
            self._reiniciar_proceso()
            return [error, "Maximo de intentos alcanzado. Proceso cancelado."]
        return [error, siguiente_mensaje]

    def _finalizar_sin_guardar(self, mensaje):
        self.estado = ESTADO_FINAL
        self._persistir_sesion()
        self._reiniciar_proceso()
        return [mensaje, "Proceso finalizado."]

    def _reiniciar_intentos(self, estado_intento):
        self.intentos[estado_intento] = 0

    def _persistir_sesion(self):
        # ==========================================================
        # PERSISTENCIA DEL ESTADO DE LA CONVERSACIÓN
        # ----------------------------------------------------------
        # Guarda el usuario actual y el estado de la máquina de
        # estados en SQLite. Esto permite recuperar la sesión ante
        # cierres inesperados y continuar el proceso desde el punto
        # donde fue interrumpido.
        # ==========================================================
        usuario = self.empleado["nombre"] if self.empleado else None
        database.guardar_sesion(usuario, self.estado)

    def _reiniciar_proceso(self):
        # ==========================================================
        # REINICIO COMPLETO DEL PROCESO
        # ----------------------------------------------------------
        # Restablece todas las variables de trabajo, elimina la
        # sesión almacenada y devuelve la máquina de estados al
        # punto inicial. Se ejecuta cuando el proceso finaliza o es
        # cancelado por el usuario.
        # ==========================================================
        database.limpiar_sesion()
        self.estado = ESTADO_INICIO
        self.empleado = None
        self.fecha = None
        self.hora_ingreso = None
        self.hora_salida = None
        self.horas_trabajadas = 0
        self.horas_extra = 0
        self.rectificar = False
        for estado_intento in self.intentos:
            self.intentos[estado_intento] = 0


def main():
    # ==========================================================
    # PUNTO DE ENTRADA DE LA APLICACIÓN
    # ----------------------------------------------------------
    # Inicia la interfaz gráfica del chatbot. Desde este punto
    # comienza la interacción con el usuario y se conecta la
    # interfaz con la lógica de negocio implementada en la
    # máquina de estados.
    # ==========================================================
    from interfaz import iniciar_interfaz

    iniciar_interfaz()


if __name__ == "__main__":
    main()
