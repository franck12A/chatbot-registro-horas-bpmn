# CHATBOT DE REGISTRO DE HORAS

## Descripción

Sistema de automatización de registro de horas trabajadas desarrollado para el Trabajo Práctico Integrador de Organización Empresarial.

Tecnologías utilizadas:

* Python
* CustomTkinter
* SQLite
* RapidFuzz
* Expresiones Regulares (Regex)
* Máquina de Estados
* BPMN 2.0

---

## Ejecución

Instalar dependencias:

```bash
pip install customtkinter rapidfuzz
```

Ejecutar:

```bash
py interfaz.py
```

---

## Usuarios de Prueba

| Nombre                         | CUIL          | Modalidad       | Supervisor  |
| ------------------------------ | ------------- | --------------- | ----------- |
| Martin Gonzalez                | 20-12345678-3 | Tiempo Completo | Ana Perez   |
| Lucia Fernandez                | 27-23456789-4 | Tiempo Parcial  | Carlos Ruiz |
| Nicolas Romero                 | 20-34567890-5 | Tiempo Completo | Ana Perez   |
| Camila Torres                  | 27-45678901-6 | Tiempo Parcial  | Marta Silva |
| Santiago Lopez                 | 20-56789012-7 | Tiempo Completo | Carlos Ruiz |
| Valentina Diaz                 | 27-67890123-8 | Tiempo Parcial  | Marta Silva |
| Mateo Herrera                  | 20-78901234-9 | Tiempo Completo | Ana Perez   |
| Florencio Beneddeti de la Cruz | 20-89012345-0 | Tiempo Completo | Carlos Ruiz |
| Eutanacio Benitez              | 20-90123456-1 | Tiempo Parcial  | Marta Silva |

---

## Flujo del Proceso

1. Validación de empleado.
2. Validación de CUIL.
3. Ingreso de fecha.
4. Verificación de registros existentes.
5. Posible rectificación.
6. Ingreso de hora de entrada.
7. Ingreso de hora de salida.
8. Cálculo de horas trabajadas.
9. Detección de horas extra.
10. Autorización de supervisor.
11. Envío a Recursos Humanos.
12. Registro final en SQLite.

---

## Casos de Error Contemplados

* Nombre inexistente.
* CUIL inválido.
* Fecha inválida.
* Registro duplicado.
* Hora de salida menor que hora de ingreso.
* Rechazo de supervisor.
* Cancelación de proceso.
* Exceso de intentos.

---

## Persistencia

La información se almacena en SQLite mediante la base de datos:

empresa.db

Tablas:

* empleados
* registros
* sesiones
