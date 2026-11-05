# Captura y gráficas del STPM33/STPM34 en el PC

Herramienta en Python para leer la tarjeta **EVALSTPM33/EVALSTPM34** por el
puerto USB-UART (CP210x), mostrar las medidas en vivo y guardar un CSV, sin
depender del **STPM3x GUI** de ST.

El programa habla directamente el protocolo UART del STPM3x:

- 9600 bps, 8N1, sin paridad (por defecto; también detecta 19200…115200),
- tramas de 4 bytes + CRC opcional (CRC8 poly 0x07 con inversión de bits),
- lectura *pipe-line*: la respuesta de una lectura llega en la transacción
  siguiente, tal como lo documenta ST en UM2066,
- activa el *auto-latch* del DSP para que las medidas se actualicen.

---

## 1. Archivos

| Archivo | Para qué |
|---|---|
| `stpm34_pc.py` | Programa principal: conexión, lectura, gráficas y CSV. |
| `test_stpm34_pc.py` | Pruebas del CRC, escalas y pipe-line (sin placa). |
| `requirements.txt` | Dependencias de Python. |
| `instalar.bat` | Instala las dependencias con `pip`. |
| `ejecutar.bat` | Abre la captura en vivo esperando la placa. |
| `ejecutar_auto.bat` | Igual, pero cierra el STPM3x GUI antes de conectar. |
| `capturas/` | Carpeta donde se guardan los CSV (se crea sola). |

---

## 2. Requisitos

- Windows con Python 3.9 o superior.
- Paquetes: `pyserial`, `matplotlib`, `numpy`.
- Tarjeta EVALSTPM33/34 con el **CP210x** y el conmutador **SW1 en UART**
  (todos los switches en ON, según el esquema de ST).
- Alimentación de la parte de metrología (J7, 3.3 V) y cable USB al PC.
- **Cerrar el STPM3x GUI** antes de ejecutar: el puerto COM es exclusivo y el
  GUI lo bloquea mientras está abierto. Si necesita cerrarlo desde el propio
  programa, use `--close-gui` (Windows).

> Seguridad: la tarjeta se conecta a la red eléctrica. No la toque mientras
> esté energizada. Use la alimentación y el aislamiento previstos por ST.

---

## 3. Instalación

Doble clic en `instalar.bat`, o desde PowerShell:

```powershell
cd "C:\Users\ASUS\Documents\Semestre_VIII\Analizador trifasico IoT\software\stpm34_pc"
python -m pip install -r requirements.txt
```

---

## 4. Uso rápido

### Ver los puertos

```powershell
python stpm34_pc.py --list
```

Debe aparecer algo como:

```
COM3  VID:PID=10C4:EA60  Silicon Labs CP210x USB to UART Bridge  <-- CP210x (EVALSTPM33/34)
```

### Captura con gráficas en vivo

```powershell
python stpm34_pc.py --port COM3 --plot
```

Si no se indica `--port`, el programa busca automáticamente el CP210x.

> A 9600 bps, leyendo 7 registros por muestra, la tasa real ronda 4–5 Hz.
> Si ve que no alcanza la tasa pedida, use `--rate 2` o `--rate 1`.

### Esperar a que aparezca la placa y capturar

```powershell
python stpm34_pc.py --wait --plot
```

Si el GUI de ST queda abierto y bloquea el puerto:

```powershell
python stpm34_pc.py --close-gui --wait --plot
```

Para captura desatendida puede usar `ejecutar_auto.bat`, que hace lo mismo.

Si la placa se desconecta, reintenta cada 2 s.

### Captura sin gráficas (para dejar corriendo)

```powershell
python stpm34_pc.py --wait --no-plot --duration 3600 --csv capturas\una_hora.csv
```

### Graficar un CSV ya guardado

```powershell
python stpm34_pc.py --plot-csv capturas\una_hora.csv --save capturas\una_hora.png
```

### Probar sin placa

```powershell
python stpm34_pc.py --demo --plot
```

Genera datos sintéticos (230 V, 5 A, 50 Hz) para verificar la instalación y la
interfaz.

---

## 5. Qué mide

| Magnitud | Registro | Escala por defecto |
|---|---|---|
| Tensión RMS V1 | `0x48` bits 14:0 | 35.484 mV/LSB |
| Corriente RMS C1 | `0x48` bits 31:15 | 2.1435 mA/LSB |
| Tensión RMS V2 | `0x4A` bits 14:0 | 35.484 mV/LSB |
| Corriente RMS C2 | `0x4A` bits 31:15 | 2.1435 mA/LSB |
| Potencia activa P1/P2 | `0x5C` / `0x74` | 1.217 mW/LSB |
| Energía activa E1/E2 | `0x54` / `0x6C` | 8.86 × 10⁻⁸ Wh/LSB |
| Frecuencia | `0x2E` | 125 kHz / período |

También calcula:

- potencia aparente `S = V · I`,
- potencia reactiva `Q = √(S² − P²)`,
- factor de potencia `PF = P / S`,
- energía integrada por software (columna `e1_int_wh` / `e2_int_wh`).

El CSV guarda además los registros crudos (`raw_48`, `raw_4a`, …) para poder
recalibrar sin repetir la captura.

> Este programa grafica valores RMS, potencia, energía y frecuencia. El UART a
> 9600 bps no permite capturar la forma de onda de 7.8 kHz; para eso se necesita
> SPI o el firmware de muestreo STPM32F407.

---

## 6. Escalas y calibración

Los valores por defecto corresponden a la **EVALSTPM33/34 V3**:

| Parámetro | Valor | Dónde |
|---|---|---|
| Divisor de tensión | R1 = 810 kΩ (3 × 270 k), R2 = 470 Ω | R12+R13+R14, R15 |
| CT | 4626-X002, 2500:1, carga 6 Ω → 2.4 mV/A | T2, R21 |
| Shunt | 0.3 mΩ → 0.3 mV/A | RS1 |
| Vref | 1.18 V típica (nominal 1.2 V) | interna |
| Ganancia de tensión | Av = 2 | fija |

El programa **lee** las ganancias (`DFE_CR1`, `DFE_CR2`) y los calibradores
(`CHV1`, `CHC1`, `CHV2`, `CHC2`), de modo que respeta los ajustes que haya
dejado el STPM3x GUI.

Si su placa o su calibración son distintas, puede sobrescribir:

```powershell
python stpm34_pc.py --plot `
  --vref 1.20 `
  --r1 810000 --r2 470 `
  --ks-ct 2.4 --ks-shunt 0.3 `
  --sensor1 shunt --sensor2 ct
```

- `--ks-ct` y `--ks-shunt` se expresan en **mV/A**.
- `--sensor1 auto|ct|shunt` y `--sensor2 auto|ct|shunt` eligen la sensibilidad.
  En `auto`, el programa usa la ganancia leída: x16 → shunt, x2 → CT.
- Para una EVALSTPM34 con dos CT, use `--sensor1 ct --sensor2 ct`.
- Para una EVALSTPM33 con shunt en el canal 1 y CT en el canal 2, use
  `--sensor1 shunt --sensor2 ct`; así no depende de la ganancia que haya
  quedado configurada.

> La exactitud absoluta depende de la calibración de la tarjeta y de la Vref
> real. Para un ajuste fino, compare con un patrón y ajuste `--vref`, `--r1`,
> `--r2` o `--ks-*`.

---

## 7. Columnas del CSV

```
timestamp, elapsed_s,
v1_rms_v, c1_rms_a, v2_rms_v, c2_rms_a,
p1_w, p2_w, q1_var, q2_var, s1_va, s2_va,
pf1, pf2, f1_hz, f2_hz,
e1_reg_wh, e2_reg_wh, e1_int_wh, e2_int_wh,
raw_48, raw_4a, raw_5c, raw_74, raw_2e, raw_54, raw_6c
```

- `timestamp`: fecha/hora local ISO 8601.
- `elapsed_s`: segundos desde el inicio de la captura.
- `e*_reg_wh`: energía leída del registro del STPM3x.
- `e*_int_wh`: energía integrada por el programa (P × dt).
- `raw_*`: valor de 32 bits del registro, en hexadecimal.

---

## 8. Problemas frecuentes

### “No se encontró el CP210x”

- Revise el cable USB y la alimentación de la placa.
- Ejecute `python stpm34_pc.py --list`.
- Si aparece otro COM, use `--port COMx`.
- Si el STPM3x GUI está abierto, ciérrelo.

### “could not open port … PermissionError”

El puerto está ocupado. Cierre el **STPM3x GUI** o cualquier terminal serie que
lo esté usando.

### “No hubo respuesta válida”

- Confirme que **SW1** está en UART (todos los switches ON).
- Pruebe `--baud 9600` y `--no-crc`.
- Pruebe `--verbose` para ver las tramas TX/RX.
- Si la placa quedó en modo SPI, desconéctela, ponga SW1 en UART y vuelva a
  alimentarla.

### Los valores no coinciden con el GUI

- El GUI puede usar Vref = 1.2 V y otra calibración. Pruebe `--vref 1.2`.
- Revise el sensor asignado a cada canal (`--sensor1`, `--sensor2`).
- Compare los registros crudos del CSV con los del GUI; si los crudos
  coinciden, el problema es solo de escala.

### La gráfica no abre

Use `--no-plot` y genere el PNG después con `--plot-csv`. En servidores sin
pantalla, matplotlib necesita un backend no interactivo.

---

## 9. Pruebas

Sin placa:

```powershell
python -m unittest -v test_stpm34_pc.py
python stpm34_pc.py --demo --no-plot --duration 3 --csv demo.csv
python stpm34_pc.py --plot-csv demo.csv --save demo.png
```

Las pruebas verifican:

- CRC UART contra los ejemplos de UM2066 (`0xA0 00 00 04 75` y `0xFF08FAF7 → 0xFC`),
- escalas de tensión, corriente, potencia y energía,
- decodificación de una muestra sintética,
- orden del pipe-line de lectura.

---

## 10. Referencias

- STPM32/33/34 datasheet, DS10272.
- UM2066 — *Getting started with the STPM3x* (protocolo UART, CRC, pipe-line).
- UM1719 — *The STPM3x evaluation software*.
- Esquema EVALSTPM33-34 V3 (`Schematic EVALSTPM33-34 V3.pdf`).
- VAC 4626-X002, relación 2500:1.
