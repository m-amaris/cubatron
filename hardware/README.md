hardware/README.md

# Protocolo de Comunicación UART (Raspberry Pi ↔ STM32)

Este documento describe el protocolo de comunicación serie utilizado para controlar la máquina Cubatron desde el backend.El STM32 actúa como fuente de la verdad para el estado de las bombas, temperatura y nivel de los depósitos.

## Formato del Mensaje
La comunicación se realiza en texto plano. Todas las tramas utilizan el carácter `|` (pipe) como delimitador de inicio y fin, y el carácter `;` (punto y coma) para separar los argumentos.

**Estructura base (Envío):** `|COMANDO;arg1;arg2|`
**Estructura base (Respuesta):** `|INFO;dato1;dato2|`

## Lista de Comandos Implementados

### 1. `MAKE` (Preparar bebida)
Ordena a las bombas dispensar los mililitros especificados para cada uno de los 4 depósitos.Al recibir esto, el STM32 pasa su estado interno a `BUSY`.
- **Sintaxis:** `|MAKE;ml_tank1;ml_tank2;ml_tank3;ml_tank4|`
- **Ejemplo:** `|MAKE;20;15;0;0|` (Sirve 20ml del depósito 1, 15ml del depósito 2 y nada del 3 y 4).

### 2. `CLEAN` (Limpieza / Purgado)
Inicia el ciclo de limpieza de las bombas. Puede ser general o específico de un depósito.El STM32 pasa su estado a `BUSY`.
- **Sintaxis (Específico):** `|CLEAN;slot|`
- **Ejemplo:** `|CLEAN;2|` (Limpia solo el depósito 2).
- **Sintaxis (General):** `|CLEAN|` (Limpia todos los circuitos).

### 3. `STOP` (Parada de emergencia)
Detiene inmediatamente cualquier operación en curso. El STM32 pasa su estado a `IDLE`
- **Sintaxis:** `|STOP|`

### 4. `STATUS` (Estado de la máquina y telemetría)
Solicita al STM32 que devuelva su estado actual. Es el comando más crítico, ya que informa al backend y frontend si la máquina está libre, cuántos mililitros quedan en las botellas y la temperatura del refrigerador.
- **Sintaxis Envío:** `|STATUS|`
- **Respuesta Esperada del STM32:** `|INFO;estado;nivel1;nivel2;nivel3;nivel4;temperatura|`
- **Ejemplo de Respuesta:** `|INFO;BUSY;650;420;1000;150;6.5|`
  - `estado`: `IDLE`, `BUSY` o `ERROR`.
  - `nivelX`: Mililitros restantes estimados/medidos en cada depósito.
  - `temperatura`: Temperatura actual en °C.

### 5. `TEMP` (Control de Temperatura)
Establece el *setpoint* de temperatura objetivo para el sistema de refrigeración.
- **Sintaxis:** `|TEMP;setpoint|`
- **Ejemplo:** `|TEMP;6.5|` (Establece la temperatura objetivo a 6.5 °C).

---
*Nota sobre el mapeo:* El backend (API `/api/drinks/make`) calcula automáticamente el reparto de mililitros comparando los ingredientes de la receta con los nombres asignados a los 4 depósitos lógicos en la base de datos.