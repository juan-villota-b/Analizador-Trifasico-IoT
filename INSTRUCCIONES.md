# INSTRUCCIONES — Diseño de la PCB en Altium Designer 26

**Proyecto:** Analizador Trifásico IoT  
**Placa:** cuadrada, **120 × 120 mm**, **2 capas**, **todos los componentes en la cara superior**.  
**Base:** netlist del **01/11/2026 14:28** y diagramas de `documentation/revision_v3/diagramas/`.  
**Regla de oro:** no empezar el ruteo hasta cerrar los bloqueantes de la §1. Varios son de seguridad y otros impiden que la placa funcione.

> Este archivo contiene primero **todas las instrucciones y reglas** y al final el **anexo gráfico** con las imágenes. Las imágenes no sustituyen las reglas: son la referencia visual de pines, colocación y corredores.

---

## 1. Bloqueantes que debes corregir en el esquemático antes de rutear

| # | Qué corregir | Dónde | Por qué |
|---|---|---|---|
| 1 | **U500-3 TXD ← IO17 (TX)** y **U500-4 RXD → IO18 (RX)** | `INTERFACES.SchDoc` | Hoy están cruzados: TXD (entrada) va a IO18/RXD y RXD (salida) va a IO17/TXD. El RS-485 no comunica y hay contención. |
| 2 | **MISO/DAT0**: separar el bus de la SD, poner un buffer 3-estado gobernado por CS_SD, o llevar EN1 del ISO7741 a un GPIO y tri-state durante el acceso a la SD | `MEASURES`/`MCU` | El OUTD del ISO7741 queda habilitado y empuja DAT0; el SDO del RN en alta impedancia no lo tri-statea. |
| 3 | **Cargador de supercaps**: reemplazar el TPS2553 por un cargador dedicado, o subir R201 a ≥100 kΩ (carga lenta 100–200 mA) | `POWER.SchDoc` | Con R201=20 kΩ el TPS2553 limita a ~1.3 A y disipa ~6 W; entra en thermal shutdown. |
| 4 | **D200/D201**: SMA/SMB de 3 A o ideal diode | `POWER.SchDoc` | MS2A40LWS SOD-323 a 1.4–1.9 A disipa ~0.9 W y supera 125 °C. |
| 5 | **PS201-3 (−Vo) = AGND**: decidir arquitectura. Si se acepta AFE a neutro, documentarlo y proteger; si se aísla, cambiar divisores y fuente | `POWER`/`THREE PHASES` | El HLK-5M03B pierde su aislamiento y el AFE queda a potencial de N. |
| 6 | **U301**: bornera de 600 V, borne de PE, etiquetas N/L1/L2/L3 y keying | `THREE PHASES` | 400 V L-L entre polos adyacentes; sin PE; sin etiquetas. |
| 7 | **CT**: bornera con cortocircuito o jack con contacto NC, burden en el conector y TVS/BAT54S en el RN | `THREE PHASES` | Un CT abierto con corriente genera cientos de voltios y daña el RN. |
| 8 | **F300**: 1 A/250 VAC slow-blow por HLK (≥500 V, ≥1.5 kA) o 1.5–2 A para ambos | `THREE PHASES` | 200 mA/250 V/50 A no cumple el datasheet ni la red 230/400 V. |
| 9 | **BOM**: reexportar CSV/XLSX desde el `.BomDoc` actual y verificar 144 líneas | Altium | El CSV del 31/10 coloca 15 pF, 165 kΩ, cristales y un SY6280. |
| 10 | **AVCC respaldado + power-fail** | `POWER`/`MCU` | Hoy el RN se apaga en el corte y el MCU no sabe cuándo empezó el respaldo. |
| 11 | **LDO/RC en AVCC** y **clamp/balancer en supercaps** | `POWER` | El ripple de 110 mVpp del HLK-5M03B llega al AFE; los supercaps pueden superar 2.7 V. |
| 12 | **C402 → R403** (10 kΩ), **1 µF en EN**, **R401/R402 Comment 5.1 kΩ**, **U100-21 a AGND**, **100 nF en 3v3_RS485** | `MCU`/`MEASURES`/`INTERFACES` | Errores de anotación/BOM y desacople. |

**No rutear con estos puntos abiertos.** Si alguno cambia el netlist, reexporta el `.NET` y vuelve a generar los diagramas.

---

## 2. Definición de la placa

| Parámetro | Valor |
|---|---|
| Forma | Cuadrada, 120 × 120 mm, esquinas R3 |
| Capas | 2 (Top / Bottom), 1.6 mm FR4, 1 oz Cu |
| Componentes | Todos en **Top**; Bottom solo cobre/ruteo auxiliar |
| Montaje | 4 agujeros M3 (3.2 mm drill) en (6,6), (114,6), (6,114), (114,114) mm; keepout 6 mm |
| Origen | Esquina inferior izquierda (0,0) |
| Unidades | mm, grid 0.1 mm; grid de ruteo 0.25 mm |
| Acabado | HASL lead-free; máscara verde; serigrafía blanca |
| Fiduciales | 3 (dos en diagonal + uno en el centro), 1 mm copper, 2 mm mask opening |
| Espesor de cobre | 35 µm (1 oz) |

**Si el creepage de 400 V no cabe en 120 × 120 mm**, sube a 130 × 130 mm. No reduzcas la barrera de aislamiento para mantener 120 mm.

---

## 3. Stackup y asignación de capas

```
TOP    : componentes + señal + potencia + planos locales
BOTTOM : plano AGND (zona analógica/primaria)
         plano DGND (zona digital)
         isla RGND (RS-485)
```

- **Top** es la capa de componentes y de la mayoría de las señales.
- **Bottom** es un plano de masa partido. No es una capa de señal libre: úsala solo para cruces cortos y para el retorno.
- **AGND** cubre la zona analógica/primaria (x < 71 mm). **DGND** cubre la zona digital (x > 71 mm). **RGND** es una isla bajo el RSM3485 (x 90–120, y 18–38 mm).
- La separación entre planos es **2 mm** bajo la barrera; no dejes cobre en la ranura.
- **No** pongas cobre en ninguna capa bajo la antena del ESP32 (keepout 15 × 10 mm).
- **No** pongas cobre bajo el cuerpo del ISO7741 en la franja de la barrera; el único puente es el propio ISO7741.

---

## 4. Preparación del proyecto en Altium

1. Cierra Altium antes de cualquier `git pull`.
2. Abre `hardware/altium/Analizador_trifasico_IoT_pcb.PrjPcb`.
3. `Project → Compile Project`. Revisa `Messages`: no debe haber pines de alimentación flotantes ni nets sin driver.
4. `Design → Netlist for Project → Protel` y confirma que el `.NET` nuevo tiene fecha/hora actual.
5. `Design → Board Shape → Define from selected objects` (o `Redefine Board Shape`) para 120 × 120 mm.
6. `Design → Layer Stack Manager`: 2 capas, 1.6 mm, 1 oz.
7. `Design → Classes`: crea las net classes de la §5.
8. `Design → Rules`: carga la matriz de clearances y anchuras de §6–§8.
9. `Place → Polygon Pour`: crea los planos AGND/DGND/RGND en Bottom.
10. `Tools → Design Rule Check`: ejecuta DRC después de cada bloque.

---

## 5. Net classes en Altium

Crea estas clases en `Design → Classes → Net Classes`. La lista completa de las 104 nets está en `documentation/revision_v3/NET_RULES.csv`; esta tabla es el resumen.

| Clase | Nets principales | Corriente máx. | Clearance | Capa |
|---|---|---:|---:|---|
| `HV_MAINS` | `NetF300_1/2`, `NetF301_1/2`, `NetF302_1/2`, pines 2-4 de U301, RV300-302, PS200-1/2, PS201-1/2 | 500 mA | 2.0 mm intra, 8.0 mm a SELV | Top |
| `AGND_ANALOG` | `AGND`, `PS201-3`, `AVCC_3v3`, `3v3_ENER_IC`, `REF`, `VO`, `XI`, `XO`, `NetC3xx`, `NetR3xx` | 50 mA | 0.5 mm a analógico; 2.0 mm a fases dentro de HV_AREA; 8.0 mm a DGND | Top/Bottom |
| `DGND_DIGITAL` | `DGND`, `DVCC_3v3`, `3v3_MCU`, `3v3_SD`, `3v3_RS485`, `SPI_*`, UART, USB, SD, `BOOT`, `EN`, `Net5xx` | 1 A | 0.3 mm | Top/Bottom |
| `POWER_5V` | `Vout_5V`, `Vin_buck_5V`, `NetC201_1/2`, `NetC207_1`, `NetC204_1/2`, `5V_USB`, `Net200_2`, `Net501_7` | 2 A | 0.3 mm | Top |
| `RS485_ISO` | `A`, `B`, `RGND` | 100 mA | 0.5 mm / 8 mm a DGND | Top/Bottom |
| `USB_DIFF` | `DP_USB`, `DN_USB`, `Netj400_A6`, `Netj400_A7` | 500 mA | 0.2 mm | Top |
| `CLOCK` | `XI`, `XO`, `SPI_CLK_RN`, `NetU101_5`, `SPI_*` | 20 mA | 0.3 mm | Top |
| `DEFAULT` | resto de señales | 100 mA | 0.2 mm | Top |

**Regla:** no asignes nets a mano en el PCB; asigna clases en el esquemático o en `Design → Classes`. Así el DRC aplica las reglas automáticamente.

---

## 6. Matriz de clearances (Design → Rules → Electrical → Clearance)

Crea una regla por par de clases. El orden importa: las reglas más específicas van arriba.

| Desde \ Hasta | HV_MAINS | AGND_ANALOG | DGND_DIGITAL | POWER_5V | RS485_ISO | USB_DIFF | CLOCK | DEFAULT |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **HV_MAINS** | 2.0 | 8.0 | 8.0 | 8.0 | 8.0 | 8.0 | 8.0 | 8.0 |
| **AGND_ANALOG** | 8.0 | 0.5 | 8.0 | 0.5 | 8.0 | 8.0 | 0.5 | 0.5 |
| **DGND_DIGITAL** | 8.0 | 8.0 | 0.3 | 0.3 | 8.0 | 0.2 | 0.3 | 0.3 |
| **POWER_5V** | 8.0 | 0.5 | 0.3 | 0.3 | 8.0 | 0.3 | 0.3 | 0.3 |
| **RS485_ISO** | 8.0 | 8.0 | 8.0 | 8.0 | 0.5 | 8.0 | 8.0 | 8.0 |
| **USB_DIFF** | 8.0 | 8.0 | 0.2 | 0.3 | 8.0 | 0.2 | 0.3 | 0.2 |
| **CLOCK** | 8.0 | 0.5 | 0.3 | 0.3 | 8.0 | 0.3 | 0.3 | 0.3 |
| **DEFAULT** | 8.0 | 0.5 | 0.3 | 0.3 | 8.0 | 0.2 | 0.3 | 0.2 |

**Notas:**
- **AGND no va en `HV_MAINS`.** AGND está en `AGND_ANALOG`; dentro de la zona de red se aplica una **regla de room** (`HV_AREA`, x 0–116, y 88–120) que exige 2.0 mm entre fases y AGND. Fuera de esa zona, AGND mantiene 0.5 mm con lo analógico y 8.0 mm con DGND. No dejes AGND en dos clases: el DRC aplicaría la regla más estricta en toda la placa.
- 8.0 mm es **creepage** entre primario/AGND y SELV/DGND. Para clearance en aire usa ≥6.0 mm y una **ranura de 2 mm** para aumentar el creepage.
- Entre fases L1/L2/L3 usa 2.0 mm; entre fase y N/AGND usa 2.0 mm.
- Entre AGND y DGND, la barrera es de 8.0 mm; el ISO7741 es el único puente.
- Entre DGND y RGND, 8.0 mm; el RSM3485 es el único puente.
- No reduzcas estas reglas por “falta de espacio”. Si no caben, la placa debe crecer.

---

## 7. Anchuras de pista (Design → Rules → Routing → Width)

| Clase / net | Corriente | Anchura mínima | Anchura recomendada | Notas |
|---|---:|---:|---:|---|
| `HV_MAINS` | 0.5 A | 1.0 mm | 1.5–2.0 mm | Red 230/400 V; 2 mm entre fases. |
| `Vout_5V` | 2.0 A | 1.0 mm | 1.5 mm | HLK-10M05 a D200. |
| `Vin_buck_5V` | 2.0 A | 0.8 mm | 1.2 mm | D200/D201/D202 a U200/U201. |
| `NetC201_1/2` | 1.3 A | 0.8 mm | 1.2 mm | Supercaps; trazas cortas y anchas. |
| `DVCC_3v3` | 1.0 A | 0.4 mm | 0.6 mm | Buck a ferritas. |
| `3v3_MCU` | 0.6 A | 0.3 mm | 0.5 mm | ESP32 + ISO lado 1. |
| `3v3_SD` | 0.25 A | 0.25 mm | 0.4 mm | microSD. |
| `3v3_RS485` | 0.15 A | 0.25 mm | 0.4 mm | RSM3485. |
| `AVCC_3v3`, `3v3_ENER_IC` | 50 mA | 0.25 mm | 0.5 mm | RN/ISO lado 2. |
| `AGND` | retorno | 0.5 mm | plano | Plano AGND; estrella en U301-1. |
| `DGND` | retorno | 0.5 mm | plano | Plano DGND continuo bajo digital. |
| `CT` (`NetC3xx`, `NetR3xx`) | 41.5 mA pico | 0.2 mm | 0.25 mm | Par diferencial; guard. |
| `SPI_*` | 20 mA | 0.15 mm | 0.2 mm | <50 mm, sin stubs. |
| `USB_DIFF` | 0.5 A | 0.15 mm | 0.2 mm | 90 Ω diferencial; gap 0.2 mm. |
| `A/B` | 100 mA | 0.2 mm | 0.3 mm | Par RS-485. |
| `RGND` | retorno | 0.3 mm | 0.5 mm | Isla RGND. |
| `DEFAULT` | 100 mA | 0.15 mm | 0.2 mm | Señal genérica. |

**Regla de oro:** una pista de 1 oz y 1 mm soporta ~2 A con 10 °C de aumento. Para 2 A usa 1.2–1.5 mm; para 1.3 A usa 1.0–1.2 mm. No pongas una pista de 0.2 mm en el camino de 5 V.

---

## 8. Vías, polígonos y otras reglas

### 8.1 Vías (Design → Rules → Routing → Routing Via Style)

| Uso | Drill | Pad | Anillo |
|---|---:|---:|---:|
| Señal | 0.3 mm | 0.6 mm | 0.15 mm |
| Potencia | 0.5 mm | 1.0 mm | 0.25 mm |
| Térmica (U200/U201/D200) | 0.3 mm | 0.6 mm | 0.15 mm |

- Usa **4×4 vías** en el pad térmico de U200 y bajo U201/D200.
- No pongas vías en el keepout de antena ni en la ranura de aislamiento.
- Evita vías en las trazas de CT y del cristal.

### 8.2 Polígonos (Place → Polygon Pour)

- AGND: `Net = AGND`, capa Bottom, prioridad 1, clearance 0.3 mm, thermal relief 0.5 mm, min island 0.3 mm.
- DGND: `Net = DGND`, capa Bottom, prioridad 2, clearance 0.3 mm.
- RGND: `Net = RGND`, capa Bottom, prioridad 3, clearance 0.5 mm.
- No viertas cobre en la ranura de 2 mm entre planos.
- No viertas cobre bajo la antena.
- Repara islas huérfanas con `Tools → Polygon Pours → Repour All` y revisa `Design → Rules → Plane → Power Plane Connect Style`.

### 8.3 Pares diferenciales

- `Design → Rules → High Speed → Differential Pairs Routing`:
  - USB: 90 Ω ±20 %, ancho 0.2 mm, gap 0.2 mm, longitud igualada ≤5 mm.
  - RS-485: no es crítico a 9.6 kbps; rutea A/B como par, ancho 0.3 mm, gap 0.3 mm.
- `Place → Directives → Differential Pair Directive` sobre las nets `DP_USB`/`DN_USB` y `A`/`B`.
- No pongas stubs ni vías innecesarias en USB.

### 8.4 Keepouts

- **Antena**: 15 × 10 mm, sin cobre en Top/Bottom, sin componentes, sin vías. `Place → Keepout → Solid Region` o `Design → Rules → Placement → Keepout`.
- **Barrera AGND/DGND**: ranura de 2 mm, sin cobre; el ISO7741 la cruza.
- **Barrera PS200**: 8 mm entre pines AC y DC; ranura si es necesario.
- **RGND**: isla separada 8 mm de DGND; el RSM3485 la cruza.
- **Montaje**: 6 mm alrededor de cada agujero M3.
- **HV**: 8 mm alrededor de U301, fusibles, MOVs y pines AC de los HLK.

### 8.5 Reglas de fabricación

- `Design → Rules → Manufacturing → Hole Size`: mínimo 0.3 mm, máximo 3.2 mm.
- `Design → Rules → Manufacturing → Silk To Solder Mask`: 0.1 mm.
- `Design → Rules → Solder Mask Expansion`: 0.05–0.1 mm.
- `Design → Rules → Placement → Component Clearance`: 0.5 mm courtyard; 1 mm entre dominios; 2 mm alrededor de HV.
- `Design → Rules → Testpoint`: 1.0 mm mínimo; agrega test points en 5V, DVCC, AVCC, AGND, DGND, REF, VO, SPI, UART, EN, BOOT, RN reset.

---

## 9. Colocación

### 9.1 Zonas

| Zona | Rango (mm) | Contenido |
|---|---|---|
| **Primario / red + AGND** | x 0–116, y 88–120 | U301, F300-302, RV300-302, PS201, PS200 (primario), entrada AC. |
| **Analógico / AGND** | x 0–71, y 18–88 | Jacks CT, divisores, RN8302B, cristal, desacople, ISO7741 (lado AGND). |
| **Digital / SELV** | x 71–120, y 0–88 | ESP32, USB-C, microSD, RSM3485 (lado DGND), buck, supercaps, headers. |
| **RGND aislada** | x 90–120, y 18–38 | RSM3485 salida, D500, J500, R501. |
| **Antena** | x 84–114, y 78–90 | Keepout total, sin cobre. |

### 9.2 Componentes principales (coordenadas en `PLACEMENT.csv`)

| Componente | X | Y | Rotación | Pin 1 |
|---|---:|---:|---:|---|
| U301 | 3 | 100 | 0 | abajo-izquierda |
| F300/F301/F302 | 23.5 | 110/106/102 | 0 | izquierda |
| RV300/RV301/RV302 | 4 | 92/86/80 | 0 | arriba |
| PS201 | 30 | 94 | 0 | arriba-izquierda |
| PS200 | 71 | 94 | 0 | arriba-izquierda |
| U300/U302/U303/U304 | 0 | 72/64/56/48 | 0 | pin 2 arriba |
| U100 | 50 | 48 | 0 | arriba-izquierda |
| U101 | 66 | 48 | **180°** | **abajo-derecha** |
| X100 | 50 | 60 | 0 | izquierda |
| U401 | 86 | 60 | 0 | arriba-izquierda |
| j400 | 111 | 52 | 0 | A1 arriba-izquierda |
| U400 | 107.5 | 52 | 0 | arriba-izquierda |
| U501 | 94 | 36 | 0 | abajo-izquierda |
| U500 | 90 | 18 | 0 | abajo-izquierda |
| J500 | 112 | 20 | 0 | — |
| D500 | 112 | 29 | 0 | abajo-izquierda |
| U201 | 92 | 12 | 0 | arriba-izquierda |
| L200 | 97 | 12 | 0 | izquierda |
| U200 | 103 | 12 | 0 | arriba-izquierda |
| C201/C202 | 72 | 8/28 | 0 | + arriba |
| 200 | 110 | 4 | 0 | — |
| 500/501 | 70/90 | 2 | 0 | izquierda |

**La orientación de los ICs en el diagrama coincide con esta tabla.** Los puntos negros de `S6_PLACEMENT` marcan el pin 1. No rotes un IC sin actualizar el diagrama y el CSV.

### 9.3 Criterios de colocación

- **Conectores en el borde:** U301 a la izquierda/arriba; jacks CT a la izquierda; USB-C a la derecha; microSD a la derecha; RS-485 a la derecha/abajo; headers HaLow abajo; antena arriba-derecha.
- **Antena:** el módulo ESP32 va en el borde superior, con la antena hacia afuera. Keepout 15 × 10 mm sin cobre en ninguna capa. No pongas supercaps, buck ni componentes altos cerca de la antena.
- **Aislamiento:** U101 centrado en la barrera (x=71). El lado AGND (pines 9-16) mira a U100; el lado DGND (pines 1-8) mira al ESP32. La barrera pasa por debajo del cuerpo.
- **Térmica:** D200/D201/D202 con cobre de 1 cm² y vías; U200 con pad térmico y 4×4 vías; U201 con cobre en SW/VIN; supercaps lejos de los HLK y de las resistencias disipadoras.
- **CT:** jacks y burden juntos; trazas diferenciales cortas; guard ring a AGND; lejos del buck y del SPI.
- **Cristal:** X100 y C100/C108 junto a U100-36/37; sin trazas debajo; guard ring; lejos del SPI.
- **Buck:** C207/C208 junto a VIN/GND; L200 junto a SW; C205/C206 junto a la salida; lazo <10 mm.
- **Supercaps:** trazas anchas y cortas; R200/R202 junto a los caps; no rutear debajo.
- **RS-485:** RSM3485 en la isla RGND; D500 y J500 junto al conector; R501 al final del bus.

---

## 10. Ruteo por bloque

### 10.1 Entrada AC y primario

- U301-4 (L1) → F300 → `NetF300_2` → PS200-1, PS201-2, R303, RV300.
- U301-3 (L2) → F301 → `NetF301_2` → R314, RV301.
- U301-2 (L3) → F302 → `NetF302_2` → R326, RV302.
- U301-1 (N) → AGND → PS200-2, PS201-1, PS201-3, RV300-302.
- Ancho 1.5–2.0 mm; clearance 2.0 mm entre fases; 8.0 mm a SELV.
- **Punto estrella en U301-1:** separa el retorno de potencia (HLK, MOV) del AGND del AFE. No hagas daisy-chain por el plano del RN.
- No pases trazas por debajo de los HLK ni de los jacks de CT.
- Los MOV deben estar antes del fusible o coordinados; si se quedan después, usa fusible de surge con I²t alto.

### 10.2 AGND y retorno analógico

- Plano AGND bajo la zona analógica/primaria (x < 71).
- U100-6 es el punto de unión de AGND del RN; los caps de AVCC/DVCC y el RC deben volver a ese punto.
- Los retornos de los divisores y CT van al plano AGND, no al DGND.
- El retorno de los HLK/MOV va por una traza ancha separada al punto estrella de U301-1; no lo metas por el plano del RN.
- No cortes el plano AGND con trazas de la barrera.

### 10.3 5 V y respaldo

- PS200-4 → D200 → `Vin_buck_5V` → U200-6/U201-3 → D201 → supercaps.
- `Vout_5V` 1.5 mm; `Vin_buck_5V` 1.2 mm; `NetC201_1/2` 1.2 mm.
- C200 10 µF junto a `Vin_buck_5V`; C207/C208 junto a U201 VIN/GND; C205/C206 junto a L200/salida.
- Lazo del buck: C207/C208 → U201 VIN/GND → L200 → C205/C206 → retorno. <10 mm.
- Supercaps: trazas de 1.2 mm, cortas; R200/R202 junto a los caps; no rutear debajo.
- D200/D201/D202 con cobre y vías térmicas.
- U200: pad térmico al plano DGND con 4×4 vías; C200 + 0.1 µF junto a IN; 0.1 µF + 10 µF junto a OUT.

### 10.4 3.3 V digital y ferritas

- DVCC_3v3 → FB400 → 3v3_MCU; FB500 → 3v3_RS485; FB501 → 3v3_SD; FB503 → 501-5; FB502 → 501-7.
- Ancho 0.6 mm para DVCC; 0.5 mm para 3v3_MCU; 0.4 mm para SD/RS485.
- C400/C401/C113 junto a U401-2; C500/C501 junto a U501-4; C502 junto a U500-1; C112 junto a U101-16.
- No pases 3.3 V digital por la zona AGND.

### 10.5 CT y divisores

- Cada canal CT: jack pin 2 → R serie 1 kΩ → nodo IAP; jack pin 3 → R serie 1 kΩ → nodo IAN; C 33 nF y R burden 10 Ω a AGND en cada nodo.
- Trazas diferenciales cortas, mismo largo, guard ring a AGND; no cruces la zona de los HLK.
- Burden junto al jack; TVS/BAT54S junto al RN.
- Divisores: cadenas verticales de 6 resistencias; nodo VAP con Rbottom 1 kΩ y C 33 nF a AGND; VAN con R 1 kΩ y C 33 nF a AGND.
- Mantén los divisores lejos del buck, del SPI y de la antena.
- No pongas trazas de fase entre las trazas de CT.

### 10.6 Cristal y RN

- X100 y C100/C108 junto a U100-36/37; trazas <5 mm; guard ring a AGND; sin trazas debajo.
- No pases SPI, USB ni 5 V cerca del cristal.
- U100-21 a AGND con traza corta al pin 6.
- U100-43 (RC) al plano DGND del lado del ISO7741, no al AGND del AFE.
- C101-C105/C109/C112 junto a U100-9/28/40; C110/C111 junto a U100-3; C106/C107 junto a U100-38.

### 10.7 SPI aislado

- U401-22/23/24/25 → U101-3/4/5/6; U101-11/12/13/14 → U100-32/33/34/35.
- Trazas <50 mm, sin stubs, 0.2 mm; serie 22–33 Ω si hay ringing.
- El único cruce de la barrera es U101. No pases SPI por debajo del cuerpo del ISO7741 fuera de sus pines.
- Mantén DGND continuo bajo el SPI del lado digital; AGND bajo el SPI del lado RN.

### 10.8 USB

- j400 A6/B6 (D+) → U400-1/6 → U401-14; A7/B7 (D−) → U400-3/4 → U401-13.
- Par diferencial 90 Ω, 0.2/0.2 mm, longitud igualada ≤5 mm, sin stubs.
- U400 junto al conector; VBUS con PTC y 100 nF + 10 µF; CC1/CC2 con 5.1 kΩ a DGND; SBU no usados.
- Shield a DGND con 1 MΩ || 4.7 nF (o directo si el gabinete está a PE).

### 10.9 microSD

- U401-22/24/25/31 → U501-3/5/7/2; U401-17 → U501-9.
- Trazas <30 mm, 0.2 mm; serie 22–33 Ω en CLK y 10–22 Ω en CMD/DAT0; ESD junto al conector.
- Pull-ups R502-R507 junto a U501; C500/C501 junto a U501-4.
- No pases SD cerca del cristal ni de la antena.

### 10.10 RS-485

- U401-10/11 → U500-4/3 (después de corregir el cruce); U401-9 → U500-5 (CON).
- U500-8/9 → D500-2/1 → J500-2/3; U500-10 → RGND → D500-3/J500-1.
- A/B como par diferencial, 0.3 mm; R501 120 Ω al final del bus; D500 junto al conector.
- RGND es isla; 8 mm a DGND; no la unas al plano digital.
- Agrega CM choke/GDT y shield/PE si el entorno es industrial.

### 10.11 Antena

- U401 en el borde superior, antena hacia afuera; keepout 15 × 10 mm sin cobre en Top/Bottom.
- No pongas supercaps, buck, cristal ni trazas debajo.
- No pongas un plano de masa bajo la antena.
- Verifica el keepout con `Design → Rules → Placement → Keepout` y con una región de cobre vacía.

---

## 11. Seguridad y creepage

- **AGND = N no es SELV.** Trata todo el dominio analógico/primario como vivo. No toques los jacks de CT ni el AFE durante la operación.
- **U301:** 600 V, PE, etiquetas N/L1/L2/L3/PE, keying. No unas N y PE en la placa.
- **Barrera AGND/DGND:** 8 mm creepage, 6 mm clearance, ranura de 2 mm. El ISO7741 es el único puente.
- **Barrera PS200:** 8 mm entre pines AC y DC; el módulo es la barrera SELV principal.
- **Barrera RGND:** 8 mm; el RSM3485 es el único puente.
- **CT:** jack/bornera con cortocircuito, TVS, burden en el conector; si el jack es metálico, conéctalo a AGND/PE en un solo punto.
- **Hipot:** prueba primario-secundario según los ratings de PS200 (2500–3000 VAC), ISO7741 (5000 Vrms) y RSM3485 (2500 VDC). No apliques hipot a los supercaps ni al ESP32.
- **Gabinete:** Clase I (PE) o Clase II (doble aislamiento). No dejes el gabinete flotante.

---

## 12. Térmica

| Componente | Potencia | Acción |
|---|---:|---|
| D200 | ~0.9 W | SMA/SMB 3 A o ideal diode; cobre 1 cm² + vías. |
| D201 | ~0.32 W | SMA/SMB o ideal diode; cobre. |
| D202 | ~0.20 W | SOD-323 aceptable; cobre. |
| U200 | ~6 W al cargar | No usar como cargador; si se mantiene, R201≥100 kΩ y pad térmico con 4×4 vías. |
| U201 | ~0.3 W | Cobre en SW/VIN; lazo corto. |
| Supercaps | — | Lejos de HLK y resistencias; vida útil cae con temperatura. |
| HLK-10M05 | ~7 W | Ventilación; no encerrar; separar de supercaps. |

---

## 13. Fabricación

1. **BOM:** reexportar desde el `.BomDoc`; verificar 144 líneas; borrar el ítem duplicado `RES_10kohms`; confirmar U200 TPS2553DRVR, C112/C113, SW401, R104, R505-R507.
2. **Gerbers:** `File → Fabrication Outputs → Gerbers`; 2 capas, NC drill, solder mask, silkscreen, assembly.
3. **Test points:** 5V, DVCC, AVCC, AGND, DGND, REF, VO, SPI (CLK/MOSI/MISO/CS), UART, EN, BOOT, RN reset, power-fail.
4. **Fiduciales:** 3; no en el keepout de antena.
5. **Panelización:** 120 × 120 mm; si el fabricante lo permite, 2×2 en 250 × 250 mm; respeta el keepout de antena.
6. **Impedancia:** USB 90 Ω ±20 %; confirma con el fabricante.
7. **Acabado:** HASL lead-free; máscara verde; serigrafía blanca.
8. **Silkscreen:** N/L1/L2/L3/PE, pin 1 de cada IC, polaridad de diodos/caps, “NO DESCONECTAR CT CON CORRIENTE”, “AGND = N, no SELV”.
9. **Assembly:** envía el CSV nuevo, no el del 31/10.

---

## 14. Checklist final antes de fabricar

- [ ] ERC/DRC sin violaciones.
- [ ] 0 nets sin rutear.
- [ ] 0 pines de alimentación flotantes.
- [ ] U401-2 en 3v3_MCU y verificado en el pad 2.
- [ ] U500-3/U500-4 corregidos.
- [ ] MISO/DAT0 sin contención.
- [ ] TPS2553/cargador y D200 térmicamente verificados.
- [ ] U301 600 V + PE + etiquetas.
- [ ] CT con cortocircuito/TVS.
- [ ] F300/F301/F302 con rating correcto.
- [ ] BOM 144 líneas, MPN verificados.
- [ ] AVCC respaldado y power-fail probado.
- [ ] Supercaps con clamp/balancer.
- [ ] Antena con keepout total.
- [ ] Barreras AGND/DGND y RGND con creepage/ranura.
- [ ] Hipot primario-secundario.
- [ ] Test points y fiduciales.
- [ ] Gerbers/NC drill/assembly revisados.

---

# Anexo gráfico

> Las imágenes siguientes son la referencia visual. Los archivos SVG/PDF de alta resolución están en `documentation/revision_v3/diagramas/`; el PDF combinado es `ESQUEMATICO_COMPLETO.pdf`.  
> **S2_FP, S3_FP, S4_FP y S5_FP son vistas de footprint**: los pines están en la posición física del encapsulado, con el pin 1 marcado y la misma rotación que en `S6_PLACEMENT`. **S1** es funcional (entrada AC, CT y divisores); la posición física de U301 y los jacks está en `S6_PLACEMENT` y `PLACEMENT.csv`.

## Figura 1 — Diagrama de bloques del sistema

![Diagrama de bloques](documentation/revision_v3/diagramas/S0_BLOCK.png)

## Figura 2 — Entrada trifásica, CT y divisores

![THREE PHASES](documentation/revision_v3/diagramas/S1_THREE_PHASES.png)

## Figura 3 — MEASURES en vista de footprint (RN8302B LQFP-44 + ISO7741 SOIC-16)

![MEASURES footprint](documentation/revision_v3/diagramas/S2_MEASURES_FP.png)

## Figura 4 — POWER en vista de footprint (HLK, TPS2553, AP63203, respaldo)

![POWER footprint](documentation/revision_v3/diagramas/S3_POWER_FP.png)

## Figura 5 — MCU en vista de footprint (ESP32-S3-WROOM-1, USB-C, USBLC6)

![MCU footprint](documentation/revision_v3/diagramas/S4_MCU_FP.png)

## Figura 6 — INTERFACES en vista de footprint (RSM3485PCT, microSD, headers)

![INTERFACES footprint](documentation/revision_v3/diagramas/S5_INTERFACES_FP.png)

## Figura 7 — Colocación 120 × 120 mm, 2 capas

![Colocación PCB](documentation/revision_v3/diagramas/S6_PLACEMENT.png)

## Figura 8 — Plan de ruteo por corredores

![Plan de ruteo](documentation/revision_v3/diagramas/S7_ROUTING.png)

## Figura 9 — Índice completo de redes (104 nets, 405 pines)

![Índice de redes](documentation/revision_v3/diagramas/S8_NETINDEX.png)

---

**Archivos de apoyo:**

- `documentation/revision_v3/PLACEMENT.csv` — coordenadas de los 144 componentes.
- `documentation/revision_v3/NET_RULES.csv` — clase, corriente, anchura y clearance de las 104 nets.
- `documentation/revision_v3/diagramas/ESQUEMATICO_COMPLETO.pdf` — todas las hojas en un PDF.
- `REPORT_v3.md` — auditoría completa con evidencia y cálculos.

**Nota final:** no se abrió Altium. La verificación en Altium (ERC, DRC, huellas, netlist reexportado) la debe hacer el humano. Los diagramas reflejan el netlist del 01/11/2026 14:28; si el esquemático cambia, reexporta el `.NET` y regenera las imágenes.
