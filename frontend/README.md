frontend/README.md

# Diseño y Arquitectura del Frontend (Cubatron)

Interfaz web responsiva para el control e interacción con el sistema Cubatron. Desarrollada con **React, Vite y Tailwind CSS**. El diseño está pensado con un enfoque "Mobile First" tipo App, ideal para usarse en un teléfono o tablet junto a la máquina.

## Progressive Web App (PWA)
Para ofrecer una experiencia 100% nativa (pantalla completa, sin barra de direcciones del navegador) en móviles o tablets, el frontend está configurado como una **PWA** utilizando `vite-plugin-pwa`.
- **Instalación:** Al abrir la web en Safari (iOS) o Chrome (Android), el usuario puede seleccionar "Añadir a la pantalla de inicio".
- **Manifest:** El archivo `manifest.json` provee el icono de la app, colores de tema y asegura que arranque en modo `standalone`.

## Navegación Principal (Bottom Navigation Bar)

La aplicación utiliza una barra de navegación inferior fija (Bottom Bar) con 5 elementos alineados de izquierda a derecha:

1. **Home**: Pantalla principal de resumen y estado.
2. **Stats**: Panel de estadísticas del usuario (XP, nivel).
3. **[Botón Central Destacado]**: Botón flotante o resaltado de acción principal para iniciar el flujo de "Preparar una Bebida". (Si la máquina está ocupada por otro usuario, este botón se deshabilita o muestra un indicador visual)
4. **Friends**: Interacción comunitaria (Ranking global y consumiciones de otros usuarios).
5. **Menu**: Menú de opciones adicionales (Historial personal, Mi perfil, y Panel de Administración si el usuario es admin).

## Estructura de Secciones y Funcionalidades

### 1. Pantalla de Login (`/`)
- Autenticación segura mediante usuario y contraseña.
- Gestión de sesión con tokens JWT.
- Redirección automática a *Home* si la sesión está activa.

### 2. Pantalla Home (`/dashboard` o `/home`)
*Vista principal inspirada en dashboards de progreso personal.*
- **Cabecera:** Saludo personalizado al usuario (ej. "¡Buenos días, [Nombre]!") con acceso rápido a notificaciones.
- **Tarjeta Semanal (Weekly Progress):** Tarjeta destacada que muestra la racha de días consumidos en la última semana, con un gráfico circular de progreso.
- **Tarjetas de Resumen (Widgets):**
  - Consumiciones de la última semana (contador o métrica rápida).
  - XP o nivel actual resumido.
- **Calendario / Visión Semanal:** Selector de días tipo píldora (S, M, T, W, T, F, S) para ver la actividad de un día específico.
- **Historial Breve:** Lista rápida en formato tarjeta con las últimas consumiciones del usuario, incluyendo el icono del vaso y los datos de la bebida.

### 3. Flujo de Preparación (Botón Central)
*Este botón lanza el modal de servicio de bebidas.*
- **Catálogo y Configuración:** Selección de receta, Vaso y Modo (`low`, `medium`, `high`, `extreme`, o `custom` mediante *sliders* para proporciones manuales). Previsualización de la XP que se va a obtener tras preparar la bebida.
- **Control de Concurrencia:** Si el endpoint devuelve HTTP `409 Conflict`, se avisa al usuario de que la máquina está en uso.
- **Pantalla de Progreso (Polling):**
  - Una vez enviada la orden `MAKE`, el frontend entra en un bucle de **polling**, consultando el endpoint `GET /api/machine/status` cada X segundos (ej. cada 1-2s).
  - La interfaz renderiza una barra de progreso o animación de llenado basada en el estado (`BUSY`).
  - Cuando la respuesta del polling cambia a `IDLE`, la animación concluye, se detiene el bucle, y se muestra una pantalla de éxito con la experiencia (XP) ganada.

### 4. Menú de Opciones (`Menu`)
Agrupa las vistas secundarias:
- **Mi Perfil:** Modificación de Avatar, tema de la interfaz (claro/oscuro) y color de acento.
- **Historial Completo:** Listado detallado, paginable y filtrable de todas las consumiciones del usuario.
- **Panel de Administración:** *(Solo visible si el rol es `admin`)*.
  - **Gestión de Usuarios:** Interfaz para crear, editar, asignar roles o eliminar usuarios del sistema.
  - **Gestión de Recetas:** Crear, editar o eliminar cócteles e ingredientes.
  - **CRUD de Vasos:** Configuración de contenedores (nombre, icono, capacidad y habilitación).
  - **Estado de la Máquina:**
    - Monitorización en tiempo real del hardware (estado del STM32, temperatura).
    - Gestión de los 4 Depósitos (asignación de contenido, nivel restante).
    - Botones de acción manual: Limpiar circuitos (`CLEAN`), Purgar depósito, y Parada de emergencia (`STOP`), configurar cada cuanto se envia un comando STATUS periódico (por defecto cada 20s) para actualizar información.

## Integración con la API
El frontend consume los siguientes endpoints del backend FastAPI:
- `/api/auth/*`: Login y gestión de tokens.
- `/api/drinks/*`: Cálculo de recetas, petición de servido (`make`).
- `/api/machine/*`: Estados, acciones UART y temperaturas.
- `/api/users/*`: Perfiles, historial, ranking y administración de usuarios.