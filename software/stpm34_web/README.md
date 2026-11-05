# STPM34 · Página de formas de onda

Página web para visualizar tensión y corriente de los dos canales del STPM34,
con vista separada o combinada, desfase, factor de potencia, tabla de datos y
escala de amplitud ajustable.

Está pensada para correr a **60 FPS** con Canvas 2D y un buffer circular. La
tabla de datos se actualiza a **5 Hz** para no gastar tiempo de CPU en el DOM.

---

## 1. Qué incluye

| Archivo | Para qué |
|---|---|
| `index.html` | Estructura de la página. |
| `styles.css` | Tema oscuro, layout y controles. |
| `app.js` | Canvas, buffer circular, demo, WebSocket, UART, estadísticas y controles. |
| `stpm34_uart.py` | Protocolo UART del STPM34, escalas y decodificación de registros. |
| `server.py` | Servidor web con demo de 7.8125 kS/s y modo UART real por WebSocket. |
| `requirements.txt` | Dependencias del servidor (`aiohttp`, `pyserial`). |
| `servir.bat` | Sirve la página estática en `http://localhost:8080` (solo demo). |
| `servidor.bat` | Sirve la página + demo + UART en `http://localhost:8000`. |
| `servidor_uart.bat` | Igual, pero cierra el STPM3x GUI antes de arrancar. |

La página **no necesita servidor para funcionar en modo demo**: si la abre
directamente o con cualquier servidor HTTP, arranca con datos sintéticos.

---

## 2. Cómo abrirla

### Opción A: demo sin WebSocket

Doble clic en `servir.bat`, o:

```powershell
cd "C:\Users\ASUS\Documents\Semestre_VIII\Analizador trifasico IoT\software\stpm34_web"
python -m http.server 8080
```

Abra:

```text
http://localhost:8080/
```

La página arranca en modo **Demo 7.8125 kS/s** y muestra una onda de 50/60 Hz
con dos canales, desfase y tabla de datos.

### Opción B: servidor con demo y UART

Doble clic en `servidor.bat`, o:

```powershell
python server.py
```

Abra:

```text
http://localhost:8000/
```

El servidor sirve tres fuentes:

- **Demo**: `/ws/demo` y `/ws` (onda sintética de 7.8125 kS/s).
- **UART real**: `/ws/uart` (STPM34 por CP210x).
- **WebSocket personalizado**: cualquier URL que usted indique.

Para entrar directo al demo por WebSocket:

```text
http://localhost:8000/?source=ws&ws=ws://localhost:8000/ws
```

### Opción C: UART real del STPM34

Conecte la EVALSTPM33/34, cierre el STPM3x GUI y levante el servidor:

```powershell
python server.py --close-gui
```

Abra la página y en **Fuente de datos** elija **UART real (STPM34)**:

- Puerto: `COM3`, o déjelo vacío para que detecte el CP210x.
- Baudios: `Auto` (prueba 9600–115200) o el valor que tenga configurado el STPM34.
- CRC: activo por defecto.
- Presione **Conectar**.

También puede entrar directo con:

```text
http://localhost:8000/?source=uart&port=COM3&baud=auto&crc=1
```

El servidor abre el UART en el puerto indicado, activa el auto-latch, lee las
muestras instantáneas y publica por WebSocket:

- muestras de tensión/corriente de los dos canales,
- métricas de RMS, P, Q, S, FP, desfase y frecuencia.

La tabla usa las métricas del chip. La onda muestra solamente las muestras que
el UART alcanza a entregar; por eso el UART no se ve tan suave como el demo.

Si el GUI de ST está abierto y bloquea el puerto, use `--close-gui` o ciérrelo
a mano.

Si abre la página desde otro equipo de la red local, cambie `localhost` por la
IP del PC donde corre el servidor, por ejemplo `ws://192.168.1.20:8000/ws`.

Por defecto el servidor demo genera **60 Hz**. Para 50 Hz:

```powershell
python server.py --line 50
```

---

## 3. Controles

- **Canal 1 / Canal 2**: cada pestaña tiene su propio buffer, su tabla y su
  escala. Los dos canales se siguen adquiriendo aunque esté mirando uno.
- **Separadas / Combinada**: dos gráficas independientes o una sola con tensión
  en el eje izquierdo y corriente en el eje derecho. En la vista combinada se
  ven los cruces por cero `V₀` e `I₀` y el desfase.
- **Ciclos**: 2, 4 o 6 ciclos completos. Por defecto 2.
- **Línea**: 50 o 60 Hz (por defecto **60 Hz**); ajusta la ventana de tiempo y
  la escala de fase.
- **Trigger**:
  - **Auto V**: fija el inicio de la ventana en un cruce ascendente de la
    tensión. La onda queda **estática** en el eje.
  - **Libre**: usa una ventana deslizante; la onda se desplaza hacia la derecha.
  Por defecto está en **Auto V**.
- **Pausar / Reanudar**: congela la visualización sin cerrar la fuente.
- **Limpiar**: vacía los buffers y la tabla.
- **Escala de amplitud**: Auto o manual, para tensión y corriente. La escala es
  **solo visual**; no modifica los datos ni la medición.
- **Fuente de datos**: Demo, UART real o WebSocket personalizado. En UART se
  eligen puerto, baudios y CRC; el WebSocket personalizado usa la URL indicada.

La tabla muestra, por canal:

- V RMS, I RMS
- V pico, I pico
- V pico-pico, I pico-pico
- Frecuencia
- Desfase (positivo = corriente atrasa)
- Factor de potencia
- P activa, S aparente, Q reactiva
- Número de muestras en la ventana

---

## 4. Formato del WebSocket

La página acepta mensajes JSON como este:

```json
{
  "type": "samples",
  "fs": 7812.5,
  "ch1": { "v": [0.0, 1.2, ...], "i": [0.0, 0.1, ...] },
  "ch2": { "v": [0.0, 1.1, ...], "i": [0.0, 0.2, ...] }
}
```

- `fs` es la tasa de muestreo en muestras por segundo.
- `v` e `i` son arrays de la misma longitud, en voltios y amperios.
- Se recomienda enviar lotes a 60 Hz; por ejemplo, 130 muestras por lote a
  7.8125 kS/s.
- El servidor demo envía exactamente ese formato.

El modo UART agrega mensajes de métricas del chip:

```json
{
  "type": "metrics",
  "ch1": {
    "vrms": 230.0, "irms": 5.0, "p": 1043.0, "q": 486.0,
    "s": 1150.0, "pf": 0.907, "phase": 25.0, "f": 60.0
  },
  "ch2": { "...": "..." }
}
```

- En UART las muestras llegan de a una por canal, no en lotes de 130.
- La tabla usa `metrics` cuando está disponible; si no, calcula desde la onda.
- Para un ESP32-S3 o un backend SPI, publique `samples` y, si quiere, `metrics`.

---

## 5. Sobre el UART del STPM34

El servidor `server.py` ya tiene un modo UART real en `/ws/uart`. Abre el
CP210x, detecta la configuración, activa el auto-latch y lee:

- muestras instantáneas de V/I de los dos canales (`0x30`–`0x36`),
- RMS de V/I (`0x48`, `0x4A`),
- potencias activa y reactiva (`0x5C`, `0x74`, `0x60`, `0x78`),
- frecuencia (`0x2E`).

La tabla usa las métricas del chip. La onda muestra las muestras instantáneas
que el UART alcanza a entregar.

**El UART del STPM34 no puede entregar 7.8125 kS/s.** A 9600 bps, leer las
muestras instantáneas una por una da del orden de decenas de muestras por
segundo; a 115200 mejora, pero sigue lejos de 7.8 kS/s. Por eso:

- el modo **Demo** usa 7.8125 kS/s para mostrar la capacidad de la página;
- el modo **UART** muestra los datos reales, aunque la onda tenga pocos puntos;
- para forma de onda suave se recomienda **SPI** (STEVAL-IPE023V1 o un
  ESP32-S3 que lea el STPM34 por SPI y publique por WebSocket).

La página no “inventa” datos en modo UART: dibuja exactamente lo que llega.

---

## 6. Rendimiento

- Canvas 2D con `requestAnimationFrame` limitado a ~60 FPS.
- Buffer circular por canal; no se reasigna memoria en cada muestra.
- La tabla se actualiza a 5 Hz, no a 60.
- La escala automática se recalcula a 5 Hz para evitar saltos.
- No hay frameworks ni librerías de gráficas: menos dependencias y menos CPU.
- El modo demo genera 4 arrays de ~130 muestras por frame; es muy liviano.
- En UART cada mensaje trae una muestra por canal; la tabla usa las métricas
  del chip y la onda muestra solo esas muestras.
- Si el origen entrega muchos más puntos, el dibujo decima la línea cuando hay
  más de ~2 muestras por píxel.

---

## 7. Requisitos

- Un navegador moderno (Chrome, Edge, Firefox).
- Para el servidor web + UART: Python 3.9+, `aiohttp` y `pyserial`.
- Para la página sola: ningún requisito de Python.

Instalación del servidor:

```powershell
python -m pip install -r requirements.txt
```

Instalación del servidor demo:

```powershell
python -m pip install -r requirements.txt
```

---

## 8. Notas

- La escala de amplitud no altera los datos; solo cambia el dibujo.
- Si la onda se sigue desplazando, revise que **Línea** coincida con la
  frecuencia real de la fuente y que **Trigger** esté en **Auto V**. En
  **Libre** el desplazamiento es intencional.
- El desfase se calcula con los fasores fundamentales de V e I en la ventana.
- La frecuencia se calcula con los cruces por cero de la tensión; si no hay
  suficientes, usa la frecuencia de línea seleccionada.
- El factor de potencia se calcula como `P / (Vrms · Irms)`.
- Para una visualización más “de instrumento”, la vista combinada con los
  marcadores `V₀` e `I₀` muestra directamente el desplazamiento entre ambas.
