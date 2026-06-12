import customtkinter

import database
from main import ChatbotRegistroHoras

# ==========================================================
# CONFIGURACIÓN VISUAL DE LA INTERFAZ
# ----------------------------------------------------------
# Se establece el modo oscuro y el tema visual de la
# aplicación para ofrecer una interfaz moderna y consistente.
# ==========================================================
customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("blue")


# ==========================================================
# CLASE PRINCIPAL DE INTERFAZ GRÁFICA
# ----------------------------------------------------------
# Implementa la interfaz visual del chatbot utilizando
# CustomTkinter. Su responsabilidad es gestionar la
# interacción con el usuario y comunicar la capa visual
# con la lógica de negocio definida en ChatbotRegistroHoras.
# ==========================================================
class InterfazChatbot(customtkinter.CTk):
    # ==========================================================
    # INICIALIZACIÓN DE LA VENTANA PRINCIPAL
    # ----------------------------------------------------------
    # Configura la estructura general de la aplicación,
    # crea los componentes gráficos e inicia la conversación
    # con el chatbot.
    # ==========================================================
    def __init__(self):
        super().__init__()
        self.chatbot = ChatbotRegistroHoras()

        self.title("Registro de Horas - Organizacion Empresarial")
        self._centrar_ventana(900, 650)
        self.minsize(860, 590)

        self.grid_columnconfigure(0, weight=3, uniform="columnas")
        self.grid_columnconfigure(1, weight=1, uniform="columnas")
        self.grid_rowconfigure(0, weight=1)

        self._crear_columna_chat()
        self._crear_panel_informativo()

        for mensaje in self.chatbot.iniciar():
            self.agregar_mensaje("Bot", mensaje)
        self._actualizar_panel_desde_chatbot()

    def _centrar_ventana(self, ancho, alto):
        self.update_idletasks()
        pantalla_ancho = self.winfo_screenwidth()
        pantalla_alto = self.winfo_screenheight()
        posicion_x = int((pantalla_ancho - ancho) / 2)
        posicion_y = int((pantalla_alto - alto) / 2)
        self.geometry(f"{ancho}x{alto}+{posicion_x}+{posicion_y}")

    def _crear_columna_chat(self):
        # ==========================================================
        # PANEL DE CONVERSACIÓN
        # ----------------------------------------------------------
        # Construye la sección principal donde se muestran los
        # mensajes intercambiados entre el usuario y el chatbot,
        # además del área de ingreso de texto.
        # ==========================================================
        self.frame_chat = customtkinter.CTkFrame(self, corner_radius=10)
        self.frame_chat.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="nsew")
        self.frame_chat.grid_columnconfigure(0, weight=1)
        self.frame_chat.grid_rowconfigure(1, weight=1)

        self.titulo_chat = customtkinter.CTkLabel(
            self.frame_chat,
            text="Chat de Registro de Horas",
            font=customtkinter.CTkFont(size=26, weight="bold"),
            anchor="w",
        )
        self.titulo_chat.grid(row=0, column=0, padx=24, pady=(22, 14), sticky="ew")

        self.area_conversacion = customtkinter.CTkTextbox(
            self.frame_chat,
            state="disabled",
            wrap="word",
            font=customtkinter.CTkFont(size=14),
            corner_radius=8,
            border_width=1,
        )
        self.area_conversacion.grid(row=1, column=0, padx=24, pady=(0, 14), sticky="nsew")

        self.frame_entrada = customtkinter.CTkFrame(self.frame_chat, fg_color="transparent")
        self.frame_entrada.grid(row=2, column=0, padx=24, pady=(0, 24), sticky="ew")
        self.frame_entrada.grid_columnconfigure(0, weight=1)

        self.entrada_texto = customtkinter.CTkEntry(
            self.frame_entrada,
            placeholder_text="Escriba aqui...",
            height=42,
            font=customtkinter.CTkFont(size=14),
        )
        self.entrada_texto.grid(row=0, column=0, padx=(0, 12), sticky="ew")
        self.entrada_texto.bind("<Return>", self.enviar_mensaje)

        self.boton_enviar = customtkinter.CTkButton(
            self.frame_entrada,
            text="Enviar",
            height=42,
            width=120,
            command=self.enviar_mensaje,
            font=customtkinter.CTkFont(size=14, weight="bold"),
        )
        self.boton_enviar.grid(row=0, column=1, sticky="e")

    def _crear_panel_informativo(self):
        # ==========================================================
        # PANEL DE MONITOREO DEL PROCESO
        # ----------------------------------------------------------
        # Muestra información relevante sobre la ejecución del
        # proceso BPMN, incluyendo usuario activo, estado actual,
        # modalidad laboral y supervisor asignado.
        # ==========================================================
        self.panel_info = customtkinter.CTkFrame(self, corner_radius=10)
        self.panel_info.grid(row=0, column=1, padx=(10, 20), pady=20, sticky="nsew")
        self.panel_info.grid_columnconfigure(0, weight=1)

        self.titulo_panel = customtkinter.CTkLabel(
            self.panel_info,
            text="Panel del proceso",
            font=customtkinter.CTkFont(size=18, weight="bold"),
            anchor="w",
        )
        self.titulo_panel.grid(row=0, column=0, padx=18, pady=(22, 18), sticky="ew")

        self.usuario_valor = self._crear_dato_panel(1, "Usuario actual:", "Sin usuario")
        self.estado_valor = self._crear_dato_panel(3, "Estado actual:", "inicio")
        self.modalidad_valor = self._crear_dato_panel(5, "Modalidad:", "Sin modalidad")
        self.supervisor_valor = self._crear_dato_panel(7, "Supervisor:", "Sin supervisor")

        self.info_proceso_titulo = customtkinter.CTkLabel(
            self.panel_info,
            text="Informacion del proceso",
            font=customtkinter.CTkFont(size=15, weight="bold"),
            anchor="w",
        )
        self.info_proceso_titulo.grid(row=9, column=0, padx=18, pady=(8, 10), sticky="ew")

        pasos = [
            "Inicio",
            "Validacion de empleado",
            "Validacion de CUIL",
            "Verificacion de duplicado",
            "Registro de horas",
            "Confirmacion",
            "Autorizacion supervisor",
            "RRHH",
            "Finalizacion",
        ]

        for indice, paso in enumerate(pasos, start=10):
            etiqueta = customtkinter.CTkLabel(
                self.panel_info,
                text=f"- {paso}",
                font=customtkinter.CTkFont(size=12),
                anchor="w",
            )
            etiqueta.grid(row=indice, column=0, padx=22, pady=2, sticky="ew")

        self.panel_info.grid_rowconfigure(19, weight=1)

        self.boton_registros = customtkinter.CTkButton(
            self.panel_info,
            text="Ver registros",
            height=38,
            command=self.mostrar_registros,
        )
        self.boton_registros.grid(row=20, column=0, padx=18, pady=(14, 8), sticky="ew")

        self.boton_limpiar = customtkinter.CTkButton(
        self.panel_info,
        text="Limpiar registros",
        height=38,
        command=self.limpiar_registros,
)
        self.boton_limpiar.grid(row=21, column=0, padx=18, pady=(0, 8), sticky="ew")

        self.boton_cancelar = customtkinter.CTkButton(
            self.panel_info,
            text="Cancelar proceso",
            height=38,
            fg_color="#8a1f2d",
            hover_color="#a52a3a",
            command=self.cancelar_proceso,
        )
        self.boton_cancelar.grid(
            row=22,
            column=0,
            padx=18,
            pady=(0, 22),
            sticky="ew",
)

    def _crear_dato_panel(self, fila, titulo, valor):
        titulo_label = customtkinter.CTkLabel(
            self.panel_info,
            text=titulo,
            font=customtkinter.CTkFont(size=13, weight="bold"),
            anchor="w",
        )
        titulo_label.grid(row=fila, column=0, padx=18, pady=(0, 4), sticky="ew")


        valor_label = customtkinter.CTkLabel(
            self.panel_info,
            text=valor,
            font=customtkinter.CTkFont(size=13),
            anchor="w",
            wraplength=185,
        )
        valor_label.grid(row=fila + 1, column=0, padx=18, pady=(0, 12), sticky="ew")
        return valor_label

    def agregar_mensaje(self, remitente, texto):
        self.area_conversacion.configure(state="normal")
        self.area_conversacion.insert("end", f"{remitente}: {texto}\n\n")
        self.area_conversacion.configure(state="disabled")
        self.area_conversacion.see("end")

    def actualizar_estado(self, nombre_usuario, estado):
        self.usuario_valor.configure(text=nombre_usuario)
        self.estado_valor.configure(text=estado)

    def enviar_mensaje(self, event=None):
        # ==========================================================
        # GESTIÓN DE MENSAJES DEL USUARIO
        # ----------------------------------------------------------
        # Captura el texto ingresado, lo envía al chatbot para
        # su procesamiento y muestra las respuestas generadas.
        # También actualiza el panel informativo.
        # ==========================================================
        texto = self.entrada_texto.get().strip()
        if not texto:
            return

        self.agregar_mensaje("Usuario", texto)
        self.entrada_texto.delete(0, "end")

        respuestas = self.chatbot.procesar_entrada(texto)
        for respuesta in respuestas:
            self.agregar_mensaje("Bot", respuesta)

        self._actualizar_panel_desde_chatbot()

    def mostrar_registros(self):
        # ==========================================================
        # CONSULTA DE REGISTROS ALMACENADOS
        # ----------------------------------------------------------
        # Recupera los registros persistidos en SQLite y los
        # muestra dentro del área de conversación para consulta.
        # ==========================================================
        registros = database.listar_registros()
        if not registros:
            self.agregar_mensaje("Bot", "No hay registros cargados en SQLite.")
            return

        self.agregar_mensaje("Bot", "Ultimos registros:")
        for registro in registros:
            self.agregar_mensaje(
                "SQLite",
                (
                    f"#{registro['id']} | {registro['nombre']} | {registro['fecha']} | "
                    f"{registro['hora_ingreso']}-{registro['hora_salida']} | "
                    f"{registro['horas_trabajadas']} hs | Extra: {registro['horas_extra']} | "
                    f"{registro['estado']}"
                ),
            )
    def limpiar_registros(self):
        # ==========================================================
        # ELIMINACIÓN DE REGISTROS
        # ----------------------------------------------------------
        # Borra todos los registros almacenados en la base de
        # datos SQLite con fines de prueba o reinicio del sistema.
        # ==========================================================
        database.limpiar_registros()
        self.agregar_mensaje(
            "Bot",
            "Todos los registros fueron eliminados correctamente."
        )

    def cancelar_proceso(self):
        # ==========================================================
        # CANCELACIÓN DEL PROCESO ACTUAL
        # ----------------------------------------------------------
        # Permite interrumpir el flujo de negocio en cualquier
        # momento y reiniciar la máquina de estados.
        # ==========================================================
        for mensaje in self.chatbot.cancelar_proceso():
            self.agregar_mensaje("Bot", mensaje)
        self._actualizar_panel_desde_chatbot()
    

    def _actualizar_panel_desde_chatbot(self):
        # ==========================================================
        # SINCRONIZACIÓN DE DATOS CON LA INTERFAZ
        # ----------------------------------------------------------
        # Actualiza los elementos visuales utilizando la
        # información actual de la máquina de estados.
        # ==========================================================
        self.actualizar_estado(
            self.chatbot.obtener_usuario_actual(),
            self.chatbot.obtener_estado_actual(),
        )
        self.modalidad_valor.configure(text=self.chatbot.obtener_modalidad_actual())
        self.supervisor_valor.configure(text=self.chatbot.obtener_supervisor_actual())


def iniciar_interfaz():
    # ==========================================================
    # PUNTO DE ENTRADA DE LA INTERFAZ GRÁFICA
    # ----------------------------------------------------------
    # Crea la ventana principal y pone en ejecución el
    # ciclo de eventos de CustomTkinter.
    # ==========================================================
    app = InterfazChatbot()
    app.mainloop()


if __name__ == "__main__":
    iniciar_interfaz()
