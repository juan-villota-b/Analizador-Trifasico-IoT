# REPORT — Revisión de esquemáticos del Analizador Trifásico IoT

**Fecha:** 31/10/2026  
**Alcance:** `MAIN.SchDoc`, `POWER.SchDoc`, `THREE PHASES.SchDoc`, `MEASURES.SchDoc`, `MCU.SchDoc`, `INTERFACES.SchDoc`, BOM y netlist.  
**Método:** revisión de conectividad con el netlist exportado (`Analizador_trifasico_IoT_pcb.NET`, 31/10/2026), contraste pin a pin contra los datasheets de `references/datasheets/`, y cálculos de alimentación, corriente, divisores y protección.  
**Limitación importante:** los `.SchDoc` son binarios OLE2 y no se abrieron en Altium. La conectividad se tomó del netlist; si el netlist está desactualizado respecto al `.SchDoc`, hay que reexportarlo y repetir la revisión. El layout de la PCB **no** se revisó (solo se listan los puntos críticos que debe verificar el layout).

> **No se modificó ningún archivo de hardware.** Solo se creó este `REPORT.md` y se descargaron datasheets en `references/datasheets/`. Las correcciones propuestas son para que las decida y ejecute el equipo en Altium.

---

## 1. Resumen ejecutivo

El diseño **no está listo para fabricar**. Hay errores que impiden el funcionamiento y errores de seguridad/aislamiento que pueden dañar componentes o al usuario:

| # | Criticidad | Hallazgo | Consecuencia |
|---|---|---|---|
| C1 | 🔴 Crítico | Los módulos AC/DC **HLK-10M05 y HLK-5M03B no tienen entrada de AC conectada**; sus pines AC1/AC2 forman una red flotante. | La placa no funciona desde la red; solo funciona por USB/header 200. |
| C2 | 🔴 Crítico | **RN8302B: REFV (pin 3) está conectado a AVCC_3v3 y AVCC (pin 9) está flotante.** | El AFE metrológico no arranca o mide mal; la referencia interna de 1.25 V queda cortocircuitada a 3.3 V. |
| C3 | 🔴 Crítico | **ISO7741: GND1 (2, 8) y GND2 (9, 15) están unidos al mismo GND.** | El aislamiento de 5000 Vrms queda anulado; el dominio analógico y el digital comparten tierra. |
| C4 | 🔴 Crítico | **RSM3485PCT: VCC (pin 1) está a GND y GND (pin 2) está a DVCC.** | El módulo RS-485 queda alimentado al revés; se daña. |
| C5 | 🔴 Crítico | **RSM3485PCT: RGND (pin 10), J500-1 y SM712-3 están al GND digital.** | Se anula el aislamiento de 2500 V del bus RS-485. |
| C6 | 🔴 Crítico | **HLK-10M05 y HLK-5M03B comparten el mismo GND** aunque son dos fuentes aisladas. | Se anula la separación analógica/digital que justifica el ISO7741. |
| C7 | 🔴 Crítico (seguridad) | **Ferritas 0603 (FB200/FB201) en serie con las líneas de 230 V AC de los HLK.** | Componente no apto para red; riesgo de arco/creepage y falla de aislamiento. |
| C8 | 🔴 Crítico (fabricación) | **BOM con MPN de capacitores equivocados:** 100 nF pedidos como 15 pF, 10 µF/22 µF pedidos como resistencia de 165 kΩ o cristal de 8.192 MHz. | El ensamblador coloca componentes incorrectos; la placa no funciona. |

> **Verificación descartada:** el bus SPI compartido RN8302B/microSD **es correcto** (ver §3.4.1). No es un hallazgo. La versión anterior de este informe lo marcaba por error como crítico.

**Altos:** falta la resistencia de 10 MΩ del cristal del RN8302B; D200/D202 SOD-323 con ~1.7 A y 0.8 W; límite de corriente del SY6280 (0.83 A) insuficiente para el respaldo a plena carga; USB-C de 500 mA insuficiente para la carga real; no hay señal de detección de caída de red para el *last gasp*; entradas de CT sin TVS; bornera U301 de 250 V para 400 V entre fases; resistencias de 0603 de 75 V en el divisor de 230 V; falta fusible/protección de AC para los HLK.

**Medios:** desacople del ESP32 después de FB400; desacople de VDD de la microSD; 0.1 µF del RSM3485 en el lado equivocado; falta capacitor de salida del SY6280; margen de sobretensión de los supercapacitores; descarga de 150 Ω del SY6280; precisión del divisor (1 kΩ 1 %, X7R); CT sin modelo definido; mapeo de fases sin documentar; pull-up de SCSN del RN; ausencia de bias en RS-485; backfeed USB/header 200; falta fusible de VBUS; ruido del HLK-5M03B en la alimentación analógica; etc.

---

## 2. Cómo se hizo la revisión

1. Se extrajeron los 139 componentes y 105 redes del netlist.
2. Se extrajeron los símbolos de `hardware/libraries/Schlib1.SchLib` para verificar que los números de pin del símbolo coinciden con el datasheet.
3. Se contrastó pin a pin cada IC/módulo contra su datasheet.
4. Se calcularon divisores, filtros, corrientes, potencias y márgenes.
5. Se auditó el BOM contra el netlist y los valores del esquemático.

**Fuentes de conectividad:**
- `hardware/altium/Project Outputs for Analizador_trifasico_IoT_pcb/Analizador_trifasico_IoT_pcb.NET`
- `hardware/altium/Project Outputs for Analizador_trifasico_IoT_pcb/Analizador_trifasico_IoT_pcb.csv`

El netlist y el BOM tienen fecha 31/10/2026 22:59, posterior a la última modificación de las hojas (22:37–22:39; `MAIN` 14:12). Por eso se consideran representativos del estado actual. Si se vuelve a editar un `.SchDoc`, hay que reexportarlos.

**Datasheets nuevos descargados en `references/datasheets/`:**

| Archivo | Componente | LCSC |
|---|---|---|
| `AP63203WU-7_Datasheet.pdf` | Buck 3.3 V 2 A | C780769 |
| `SY6280AAC_Datasheet.pdf` | Load switch 2 A | C55136 |
| `RSM3485PCT_Datasheet.pdf` | Módulo RS-485 aislado | C882105 |
| `HLK-10M05_Datasheet.pdf` | AC/DC 5 V 2 A | C52746092 |
| `HLK-5M03B_Datasheet.pdf` | AC/DC 3.3 V 1.5 A | C48935094 |
| `USBLC6-2SC6_Datasheet.pdf` | TVS USB | C7519 |
| `SM712_Datasheet.pdf` | TVS RS-485 | C908219 |
| `MOV-14D471K_Datasheet.pdf` | Varistor 470 V | C1527439 |
| `JFC2410-0200TS_Datasheet.pdf` | Fusible 200 mA 250 V | C55058769 |
| `HX-PJ-320A-3P_Datasheet.pdf` | Jack 3.5 mm | C19189087 |
| `TF-CARD-9P_Datasheet.pdf` | Conector microSD | C53144700 |
| `USB-C-16P_Datasheet.pdf` | Conector USB-C | C7507405 |
| `Crystal_8.192MHz_Datasheet.pdf` | Cristal 8.192 MHz | C19674267 |
| `MS2A40LWS_Datasheet.pdf` | Diodo Schottky 2 A 40 V | C7380001 |
| `SCBM160808U090T_Datasheet.pdf` | Ferrita 0603 6 A | C52205324 |

Ya existían: `RN8302B_Datasheet_v3.pdf`, `RN8302B_User_Manual_v1.1.pdf`, `ISO7741DWR_Datasheet.pdf`, `ESP32-S3-WROOM_Module.pdf`, `ESP32-S3_Datasheet_en.pdf`, `ESP32-S3_Technical_Reference_Manual_en.pdf`, `Supercapacitor_Datasheet.pdf`.

---

## 3. Checklist hoja por hoja

### 3.1 `POWER.SchDoc`

#### 3.1.1 Componentes y conexiones

| Componente | Valor / parte | Conexión netlist | Veredicto |
|---|---|---|---|
| PS200 | HLK-10M05T, 5 V 2 A, 10 W | 1→NetFB200_2, 2→NetPS200_2, 3→GND, 4→Vout_5V | 🔴 AC flotante |
| PS201 | HLK-5M03B, 3.3 V 1.5 A, 5 W | 1→NetPS200_2, 2→NetFB201_1, 3→GND, 4→AVCC_3v3 | 🔴 AC flotante |
| FB200 | Ferrita 0603 6 A | 1→NetFB200_1, 2→NetFB200_2 | 🔴 No apta para 230 V AC |
| FB201 | Ferrita 0603 6 A | 1→NetFB201_1, 2→NetFB200_1 | 🔴 No apta para 230 V AC |
| D200 | MS2A40LWS 2 A 40 V | 1(K)→Vin_buck_5V, 2(A)→Vout_5V | ✅ Orientación; ⚠️ térmica |
| D201 | MS2A40LWS 2 A 40 V | 1(K)→Vin_buck_5V, 2(A)→NetC201_1 | ✅ Respaldo |
| D202 | MS2A40LWS 2 A 40 V | 1(K)→NetC207_1, 2(A)→Net200_2 | ✅ OR USB; ⚠️ térmica |
| C200 | 10 µF 16 V X5R | Vin_buck_5V / GND | ✅ |
| C201, C202 | 30 F 2.7 V | Serie, midpoint NetC201_2 | ✅ |
| R200, R202 | 1 kΩ | Balanceo de supercaps | ✅ |
| U200 | SY6280AAC | 1 OUT→NetC201_1, 2 GND, 3 ISET→R201, 4 EN→Vin_buck_5V, 5 IN→Vin_buck_5V | ✅ pinout; ⚠️ límite 0.83 A |
| R201 | 8.2 kΩ | ISET→GND | ✅ Ilim = 6800/8200 = 0.83 A; ⚠️ respaldo |
| U201 | AP63203WU-7 | 1 FB→DVCC, 2 EN→VIN, 3 VIN, 4 GND, 5 SW→L200, 6 BST→C204 | ✅ |
| L200 | 3.9 µH 2.3 A | SW→DVCC | ✅ |
| C204 | 100 nF | BST→SW | ✅ |
| C205, C206 | 22 µF 10 V X5R | DVCC/GND | ✅ |
| C207 | 4.7 µF 25 V | VIN/GND | ✅ |
| C208 | 10 µF 16 V X5R | VIN/GND | ✅ |
| C400 | 22 µF 10 V X5R | DVCC/GND | ✅ |
| C401 | 100 nF 50 V Y5V | DVCC/GND | ✅ (Y5V pobre) |
| C203 | 4.7 µF 25 V | AVCC/GND | ✅ |
| FB202 | Ferrita 0603 6 A | Vin_buck_5V ↔ NetC207_1 | ✅ |
| 200 | Header 2x1 | 1→5V_USB, 2→D202 | ⚠️ backfeed USB/header |

#### 3.1.2 Pin a pin de los módulos HLK

| Pin | Nombre | Netlist | Requisito datasheet | Veredicto |
|---|---|---|---|---|
| PS200-1 | AC1 | NetFB200_2 | Entrada AC 85–265 V | 🔴 Flotante |
| PS200-2 | AC2 | NetPS200_2 | Entrada AC 85–265 V | 🔴 Flotante |
| PS200-3 | −VO | GND | Salida negativa | ✅ |
| PS200-4 | +VO | Vout_5V | Salida +5 V 2 A | ✅ |
| PS201-1 | AC | NetPS200_2 | Entrada AC 85–265 V | 🔴 Flotante |
| PS201-2 | AC | NetFB201_1 | Entrada AC 85–265 V | 🔴 Flotante |
| PS201-3 | −VO | GND | Salida negativa | ✅ |
| PS201-4 | +VO | AVCC_3v3 | Salida +3.3 V 1.5 A | ✅ |

**Hallazgo C1 — La entrada AC está flotante.**  
Las redes `NetFB200_1` (FB200-1 + FB201-2) y `NetPS200_2` (PS200-2 + PS201-1) solo contienen esos pines. No hay conexión a `U301` (bornera de red), a `F300/F301/F302` ni a ningún conector de AC. La única entrada de energía real es `5V_USB` / header `200`. Los HLK nunca se energizan.

**Hallazgo C7 — Ferritas en AC.**  
`FB200` y `FB201` son `SCBM160808U090T`, una ferrita multicapa 0603 de 6 A y 10 mΩ. No tiene tensión de aislamiento para 230 V AC ni creepage. En serie con la red es un riesgo de arco. Además, la rama AC queda asimétrica: una línea pasa por dos ferritas en serie y la otra va directa. Debe eliminarse o reemplazarse por un inductor/choke apto para red.

**Hallazgo C6 — Un solo GND para dos fuentes aisladas.**  
`PS200-3` y `PS201-3` van a `GND`, y ese mismo `GND` es el de `U100`, `U101`, `U500`, `J500`, USB y microSD. Las dos fuentes HLK son aisladas (3000 VAC), pero al unir sus secundarios se pierde la separación analógica/digital. Es la misma causa raíz que C3/C5.

#### 3.1.3 Buck AP63203

| Pin | Nombre | Netlist | Requisito datasheet | Veredicto |
|---|---|---|---|---|
| 1 | FB | DVCC_3v3 | FB a VOUT en versión fija 3.3 V | ✅ |
| 2 | EN | NetC207_1 (VIN) | EN alto o a VIN | ✅ |
| 3 | VIN | NetC207_1 | 3.8–32 V; 5 V nominal | ✅ |
| 4 | GND | GND | GND | ✅ |
| 5 | SW | L200/C204 | Nodo de conmutación | ✅ |
| 6 | BST | C204 | 100 nF a SW | ✅ |

Cálculos:
- fsw = 1.1 MHz (AP63203, no 500 kHz).
- ΔIL = VOUT·(VIN−VOUT)/(VIN·L·fsw) = 3.3·1.7/(5·3.9 µH·1.1 MHz) ≈ 0.26 A.
- IL,pico a 2 A = 2.13 A < 2.3 A del inductor; a 1.2 A = 1.33 A. ✅
- Pérdidas estimadas a 1.2 A: ~0.4 W; θJA 89 °C/W → ~36 °C de subida. ✅
- Salida 3.3 V ±1.5 %; carga 1.2 A < 2 A. ✅

**Observación:** el layout debe manter C207/C208 pegados a VIN/GND, L200 cerca de SW y C205/C206/C400 cerca del inductor. No verificable desde el esquemático.

#### 3.1.4 Load switch SY6280

| Pin | Nombre | Netlist | Requisito datasheet | Veredicto |
|---|---|---|---|---|
| 1 | OUT | NetC201_1 (supercap) | Salida | ✅ |
| 2 | GND | GND | GND | ✅ |
| 3 | ISET | R201 8.2 kΩ a GND | Ilim = 6800/Rset | ✅ 0.83 A |
| 4 | EN | Vin_buck_5V | Activo alto; no dejar flotante | ✅ |
| 5 | IN | Vin_buck_5V | 2.4–5.5 V | ✅ |

**Hallazgo H3 — Límite de corriente vs respaldo.**  
Con R201 = 8.2 kΩ, Ilim(típ) = 0.83 A (mín 0.62 A, máx 1.04 A). El respaldo a plena carga (3.3 V × 1.19 A ≈ 3.93 W; entrada ≈ 4.37 W a 4.5 V ≈ 0.97 A) supera el límite. El *last gasp* solo funciona si el firmware apaga cargas (SD, HaLow, Wi-Fi) y deja una carga reducida. Si se quiere respaldar toda la carga, bajar R201 a ~6.8 kΩ (1 A) o menos, verificando el límite del HLK-10M05 y del USB.

**Hallazgo M4 — Falta capacitor de salida.**  
El datasheet del SY6280 recomienda un capacitor de salida (típ. 1 µF) para estabilidad/transitorios. Aquí la salida es el banco de supercapacitores, que está lejos y tiene ESR/ESL; agregar 1 µF + 10 µF cerámicos junto al pin OUT.

**Hallazgo M6 — Descarga de salida de 150 Ω.**  
El SY6280 descarga OUT con 150 Ω al apagarse. Con 15 F, eso es una fuga de ~31 mA a 4.7 V que consume parte del respaldo. Es aceptable (~3 % de la carga), pero debe tenerse en cuenta en el cálculo del *last gasp*.

#### 3.1.5 Supercapacitores y respaldo

- C201/C202: 30 F + 30 F en serie = 15 F, 5.4 V máx.
- Carga desde 5 V: cada capacitor ve ~2.45 V (margen 0.25 V a 2.7 V). Con USB 5.25 V: ~2.625 V (margen ~0.075 V). **Margen pequeño**; se recomienda un clamp de 5.1 V (zener/TVS) o resistencias de balanceo más fuertes.
- Balanceo: R200/R202 1 kΩ → 2.35 mA, 5.5 mW cada una. ✅
- Energía útil: 0.5·15·(4.9²−3.6²) ≈ 83 J. A 4.37 W → ~19 s teóricos; con límite 0.83 A y pérdidas, ~10–15 s a carga reducida. El README dice 9 s a 3.2 W: conservador y plausible solo con carga reducida.
- **Hallazgo H5 — No hay señal de detección de caída de red.** No hay comparador, ADC ni GPIO conectado a `Vin_buck_5V`/`Vout_5V`. El ESP32 no puede saber cuándo empieza el respaldo hasta que el riel de 3.3 V cae. Para un *last gasp* real, agregar un divisor + comparador a un GPIO (o monitorear el riel de 5 V con ADC) y una señal de "power fail".

#### 3.1.6 Presupuesto de corriente

**Riel DVCC 3.3 V (salida del AP63203):**

| Carga | Típico | Máximo | Nota |
|---|---:|---:|---|
| ESP32-S3-WROOM-1 | 250 mA | 500 mA | Pico Wi-Fi TX |
| microSD | 50 mA | 200 mA | Escritura |
| RSM3485PCT | 30 mA | 130 mA | Datasheet |
| ISO7741 lado 1 | 3 mA | 5.2 mA | 3.5 Mbps |
| USBLC6 | <1 mA | <1 mA | — |
| HaLow (futuro) | 200 mA | 350 mA | No colocado |
| **Total sin HaLow** | **~283 mA** | **~836 mA** | — |
| **Total con HaLow** | **~483 mA** | **~1 186 mA** | — |
| Capacidad AP63203 | — | 2 000 mA | — |
| Margen sin HaLow | — | 1 164 mA (58 %) | ✅ |
| Margen con HaLow | — | 814 mA (41 %) | ✅ |

**Riel AVCC 3.3 V (salida del HLK-5M03B):**

| Carga | Máximo | Nota |
|---|---:|---|
| RN8302B | 5 mA | EMM, datasheet |
| ISO7741 lado 2 | 5.7 mA | 3.5 Mbps |
| Divisores de tensión | 0.7 mA | 3 × 232 µA |
| **Total** | **~11.4 mA** | — |
| Capacidad HLK-5M03B | 1 500 mA | — |
| Margen | 1 488 mA (99 %) | ✅ |

**Riel de 5 V (salida del HLK-10M05 / USB):**

| Carga | Sin HaLow | Con HaLow |
|---|---:|---:|
| Entrada del buck (3.3 V/5 V, η=0.9) | 613 mA | 870 mA |
| Carga de supercaps (SY6280) | 830 mA | 830 mA |
| **Total** | **1 443 mA** | **1 700 mA** |
| Capacidad HLK-10M05 | 2 000 mA | 2 000 mA |
| Margen | 557 mA (28 %) | 300 mA (15 %) |

**Hallazgo H4 — USB-C no puede con la carga.**  
El USB-C está configurado como *sink* con R401/R402 = 5.11 kΩ, lo que solicita 5 V y el límite por defecto (500 mA / 900 mA según la fuente). Solo la entrada del buck ya consume 613–870 mA; si además carga los supercaps, 1.44–1.70 A. El riel de 5 V por USB se cae o el host limita. Si el USB es solo para programación, hay que **desconectar la carga** o limitar el buck cuando `5V_USB` esté presente; si se quiere operar por USB, usar un controlador PD que negocie 1.5–3 A o alimentar por el header 200.

**Hallazgo H2 — D200/D202 térmicos.**  
MS2A40LWS: 2 A, SOD-323, VF 0.37 V @1 A y 0.50 V @2 A, TJ máx 125 °C. A 1.7 A, P ≈ 0.8 W. El datasheet no da θJA, pero un SOD-323 a 0.8 W suele superar 125 °C. D200 (salida HLK) y D202 (USB + carga de supercaps) son los más exigidos. Usar SMA/SMB (2–3 A) o dos diodos en paralelo con reparto, y verificar la temperatura en placa.

---

### 3.2 `THREE PHASES.SchDoc`

#### 3.2.1 Entrada de red y protección

| Componente | Valor | Conexión | Veredicto |
|---|---|---|---|
| U301 | Bornera 4 pines, 18 A, **250 V** | 1→GND (N), 2→F302, 3→F301, 4→F300 | ⚠️ 250 V para 400 V entre fases |
| F300/F301/F302 | 200 mA, 250 V, 2410 | Fase → divisor/MOV | ⚠️ coordinación con MOV/HLK |
| RV300/RV301/RV302 | MOV-14D471K, 470 VAC | Fase ↔ GND | ✅ para 230 V fase-N |
| R303–R308 | 6 × 165 kΩ 0.1 % | Divisor fase A | ✅ ratio; ⚠️ 75 V por R |
| R314–R319 | 6 × 165 kΩ 0.1 % | Divisor fase B | ✅ ratio; ⚠️ 75 V por R |
| R326–R331 | 6 × 165 kΩ 0.1 % | Divisor fase C | ✅ ratio; ⚠️ 75 V por R |
| R310/R320/R332 | 1 kΩ 1 % | Bottom del divisor | ⚠️ 1 % limita precisión |
| C302/C306/C309 | 33 nF X7R 50 V | Filtro VAP/VBP/VCP | ⚠️ X7R para metrología |
| C303/C307/C311 | 33 nF X7R 50 V | Filtro VAN/VBN/VCN | ⚠️ X7R |
| R300/R309, R311/R322, R324/R334, R336/R339 | 1 kΩ 1 % | Serie a IAP/IAN, etc. | ✅ |
| R301/R302, R313/R321, R325/R333, R337/R338 | 10 Ω 1 % 333 mW | Burden de CT | ✅ potencia; ⚠️ CT indefinido |
| C300/C301, C304/C305, C308/C310, C312/C313 | 33 nF X7R 50 V | Filtro de corriente | ✅ |
| U300/U302/U303/U304 | HX PJ-320A-3P | CT fase A/B/C y neutro | ⚠️ pinout ring/sleeve; sin TVS |

#### 3.2.2 Divisor de tensión — cálculos

- Rtop = 6 × 165 kΩ = 990 kΩ; Rbottom = 1 kΩ.
- Ratio = 1 kΩ / (990 kΩ + 1 kΩ) = 1.009 × 10⁻³.
- A 230 Vrms: 232 mVrms = **0.656 Vpp** (dentro de 800 mVpp).
- A 277 Vrms: 280 mVrms = **0.790 Vpp** (cerca del límite).
- A 300 Vrms: 303 mVrms = **0.856 Vpp** (clipea).
- Máximo medible: 0.8 Vpp / (2√2) = 283 mVrms → **280 Vrms**.
- Corriente: 230 V / 991 kΩ = **232 µA**.
- Potencia por 165 kΩ: (232 µA)² × 165 kΩ = **8.9 mW** (<100 mW). ✅
- Potencia en 1 kΩ: **54 µW**. ✅
- Filtro: fc = 1/(2π·(990 kΩ || 1 kΩ)·33 nF) ≈ **4.8 kHz**; desfase a 50 Hz ≈ **0.6°**. ✅
- **Hallazgo M7:** el resistor de 1 kΩ es 1 % y 100 ppm/°C; el de 165 kΩ es 0.1 % y 25 ppm/°C. La calibración de ganancia del RN puede compensar el error inicial, pero la deriva térmica del 1 kΩ domina. Para clase 0.5S, usar 0.1 % y bajo TCR también en el de 1 kΩ.
- **Hallazgo M7b:** los capacitores de 33 nF son X7R. Su coeficiente de tensión/temperatura y su distorsión dieléctrica afectan la fase/gain. Para metrología, C0G/NP0.
- **Hallazgo H10:** los resistores de 165 kΩ son 0603, typically 75 V de working voltage. En operación normal cada uno ve ~38 V (OK), pero con el MOV clampando a ~775 V cada uno ve ~129 V. Verificar la tensión de trabajo/pulso del resistor o usar 0805/1206 o más resistencias en serie.

#### 3.2.3 Entradas de corriente — cálculos

- Burden diferencial = 10 Ω + 10 Ω = **20 Ω**.
- Vmax = 0.8 Vpp → Ipk = 40 mA → **28.3 mA rms**.
- Para un CT 100 A / 20 mA: a 100 A, 20 mA × 20 Ω = 0.4 Vrms = **1.13 Vpp** → excede el RN.
- Para un CT 100 A / 10 mA: 0.2 Vrms = **0.566 Vpp** → OK.
- Para un CT 100 A / 5 A: imposible; se requiere CT de baja corriente o Rogowski con integrador.
- Potencia en cada burden a 20 mA: (20 mA)² × 10 Ω = **4 mW** (<333 mW). ✅
- Filtro: fc ≈ 1/(2π·(1 kΩ+10 Ω)·33 nF) ≈ **4.8 kHz**; desfase a 50 Hz ≈ **0.6°**. ✅
- **Hallazgo M8:** el modelo de CT/Rogowski no está definido. Sin la relación de transformación y la corriente máxima, no se puede verificar que la señal no exceda 800 mVpp ni que el burden de 10 Ω sea el correcto. Definir CT (relación, clase, carga) y calcular el burden.
- **Hallazgo H6:** no hay TVS/clamp en las entradas de CT. Si se desconecta un CT con corriente, el secundario puede generar una tensión alta y dañar el RN (abs. max diferencial ±2 V). Agregar BAT54S/TVS y/o un cortocircuitador de CT.
- **Hallazgo M18:** el jack HX PJ-320A-3P se usa con los pines 2 y 3. Si el pinout del jack es el habitual (1 = tip, 2 = ring, 3 = sleeve, 4 = switch), el CT queda entre ring y sleeve; con un plug TS (mono) ring y sleeve se cortocircuitan y el CT se corta. Verificar el pinout real del símbolo/footprint contra el datasheet y documentar el cableado (plug TRS, o usar tip/sleeve).

#### 3.2.4 Mapeo de fases

- Tensión A: F300 ← U301-4.
- Tensión B: F301 ← U301-3.
- Tensión C: F302 ← U301-2.
- Corriente A: U300; B: U302; C: U303; neutro: U304.
- **Hallazgo M9:** no hay etiquetas de fase (L1/L2/L3) ni correspondencia explícita entre U300/U302/U303 y las tensiones A/B/C. Si se cruza una fase de tensión con una de corriente, la potencia/energía sale mal. Documentar y verificar en el layout.

#### 3.2.5 Protección y seguridad

- **Hallazgo H7 — U301 250 V para 400 V entre fases.** La bornera es de 250 V; en un sistema 3P4W de 400 V entre fases, la tensión entre pines adyacentes es 400 V. Usar una bornera de 600 V o separar fases con mayor creepage.
- **Hallazgo H9 — Fusibles de 200 mA.** El HLK-10M05/5M03B no están conectados; si se conectan, el fusible de 200 mA es probable que se abra con el inrush del HLK. Dimensionar el fusible para el HLK (p. ej. 1 A) y usar otro fusible para el divisor (p. ej. 50 mA), o coordinar con el MOV.
- **Hallazgo M17 — MOV después del fusible.** Un pico de 4.5 kA a través del MOV pasa por el fusible de 200 mA y puede abrirlo. Coordinar MOV/fusible: MOV antes del fusible, o fusible con capacidad de pulso adecuada.
- **Hallazgo M15 — Sin etiqueta de neutro/fase.** U301-1 = GND = neutro. Si el usuario invierte L/N, el GND queda vivo. Marcar claramente N/L1/L2/L3 y usar un conector/keying.

---

### 3.3 `MEASURES.SchDoc`

#### 3.3.1 RN8302B — pin a pin (U100, LQFP-44)

Datasheet: `RN8302B_User_Manual_v1.1.pdf`, Table 1-1, y `RN8302B_Datasheet_v3.pdf`.

| Pin | Nombre | Netlist | Requisito datasheet | Veredicto |
|---:|---|---|---|---|
| 1 | NC | — | No conectar | ✅ |
| 2 | NC | — | No conectar | ✅ |
| 3 | **REFV** | **AVCC_3v3** | Salida de referencia 1.25 V; desacoplar a AGND con 10 µF + 0.1 µF (REFSEL=0) | 🔴 **Mal** |
| 4 | IAP | NetC300_2 (R300/C300) | Entrada diferencial de corriente A, ≤800 mVpp | ✅ |
| 5 | IAN | NetC301_1 (R309/C301) | Entrada diferencial de corriente A | ✅ |
| 6 | AGND | GND | AGND | ✅ (dentro de un solo GND) |
| 7 | IBP | NetC304_2 (R311/C304) | Corriente B | ✅ |
| 8 | IBN | NetC305_1 (R322/C305) | Corriente B | ✅ |
| 9 | **AVCC** | **— (flotante)** | Alimentación analógica 3.0–3.6 V; 10 µF + 0.1 µF a AGND | 🔴 **Mal** |
| 10 | ICP | NetC308_2 (R324/C308) | Corriente C | ✅ |
| 11 | ICN | NetC310_1 (R334/C310) | Corriente C | ✅ |
| 12 | VAP | NetC302_2 (R308/R310/C302) | Tensión A | ✅ |
| 13 | VAN | NetC303_1 (R312/C303) | Tensión A | ✅ |
| 14 | VBP | NetC306_2 (R319/R320/C306) | Tensión B | ✅ |
| 15 | VBN | NetC307_1 (R323/C307) | Tensión B | ✅ |
| 16 | VCP | NetC309_2 (R331/R332/C309) | Tensión C | ✅ |
| 17 | VCN | NetC311_1 (R335/C311) | Tensión C | ✅ |
| 18 | INP | NetC312_2 (R336/C312) | Corriente de neutro | ✅ |
| 19 | INN | NetC313_1 (R339/C313) | Corriente de neutro | ✅ |
| 20 | RA | GND | Reservado; conectar a AGND | ✅ |
| 21 | NC | — | No conectar | ✅ |
| 22 | CTT (símbolo dice CF5) | — | Salida de detección de CT; no usada | ✅ (símbolo mal nombrado) |
| 23 | CF4 | — | Salida de calibración; no usada | ✅ |
| 24 | CF3 | — | No usada | ✅ |
| 25 | CF2 | — | No usada | ✅ |
| 26 | CF1 | — | No usada | ✅ |
| 27 | RSTN | R103 1 kΩ a AVCC | Pull-up 1 kΩ o a VCC | ✅ |
| 28 | DVCC | AVCC_3v3 | 3.3 V digital; 10 µF + 0.1 µF | ✅ (misma rail) |
| 29 | DGND | GND | DGND | ✅ (dentro de un solo GND) |
| 30 | NC | — | No conectar | ✅ |
| 31 | INTN | R102 10 kΩ a AVCC | Salida de interrupción; no conectada al ESP32 | ⚠️ No se usa |
| 32 | SDO | SPI_MISO_RN → U101-11 | Salida SPI | ✅ |
| 33 | SCLK | SPI_CLK_RN → U101-13 | Entrada SPI | ✅ |
| 34 | SCSN | SPI_CS_RN → U101-12 | Entrada SPI; pull-up recomendado | ⚠️ Sin pull-up |
| 35 | SDI | SPI_MOSI_RN → U101-14 | Entrada SPI | ✅ |
| 36 | XO | X100-2 / C108 | Cristal 8.192 MHz | ✅ |
| 37 | XI | X100-1 / C100 | Cristal; **10 MΩ entre XI y XO** | 🔴 **Falta 10 MΩ** |
| 38 | VO | C106 10 µF + C107 100 nF | Salida del regulador interno; 10 µF + 0.1 µF, sin carga | ✅ |
| 39 | DGND | GND | DGND | ✅ |
| 40 | DVCC | AVCC_3v3 | 3.3 V digital | ✅ |
| 41 | RB | AVCC_3v3 | Conectar a DVCC | ✅ |
| 42 | PM | GND | PM=0 → EMM | ✅ |
| 43 | RC | GND | Conectar a DGND | ✅ |
| 44 | NC | — | No conectar | ✅ |

**Hallazgo C2 — REFV/AVCC.**  
El pin 3 es la salida de la referencia interna de 1.25 V (REFSEL=0). Está conectado a `AVCC_3v3` (3.3 V). Eso cortocircuita la referencia a 3.3 V; el ADC pierde la referencia de 1.25 V y la precisión. El pin 9 (AVCC) está flotante; el bloque analógico no tiene alimentación. La corrección es:
- Pin 9 → `AVCC_3v3`, con 10 µF + 0.1 µF a AGND.
- Pin 3 → solo 10 µF + 0.1 µF a AGND (no a AVCC).
- Verificar que el bit REFSEL quede en 0 (referencia interna).

**Hallazgo H1 — Falta 10 MΩ en el cristal.**  
El datasheet dice: "it is necessary to connect with the 10 MΩ resistor between this pin [XI] and the XO pin". No hay ninguna resistencia entre `XI` y `XO`; solo X100 y C100/C108. Agregar 10 MΩ 1 % entre pin 37 y pin 36. Sin esto, el oscilador puede no arrancar o ser inestable.

**Hallazgo M10 — SCSN sin pull-up.**  
El datasheet recomienda pull-up externo en SCSN. El ISO7741 tiene salida push-pull y fail-safe high, pero durante el arranque (ISO7741 sin VCC2) el pin 34 queda flotante. Agregar 10 kΩ de SCSN a AVCC en el lado del RN.

**Hallazgo L1 — Símbolo pin 22.**  
El símbolo del RN8302B llama `CF5` al pin 22; el datasheet lo llama `CTT` (detección de circuito abierto/cortocircuito de CT). No afecta porque está sin conectar, pero corregir la librería.

**Hallazgo L9 — INTN no conectado.**  
El pin 31 está pull-up a AVCC y no llega al ESP32. El README promete "2 GPIO" entre RN y ESP32; el diseño solo usa los 4 canales SPI. Si se quiere interrupción (fin de conversión, alarmas), conectar INTN a un GPIO libre o a otro canal del ISO7741 (no hay canales libres; habría que usar un ISO7741 + ISO7721 o similar).

#### 3.3.2 ISO7741 — pin a pin (U101, SOIC-16)

Datasheet: `ISO7741DWR_Datasheet.pdf`, Table 6-1.

| Pin | Nombre | Netlist | Requisito datasheet | Veredicto |
|---:|---|---|---|---|
| 1 | VCC1 | DVCC_3v3 | 2.25–5.5 V; 0.1 µF a GND1 | ✅ |
| 2 | GND1 | GND | GND1 (lado digital) | 🔴 **Debe ser DGND, no GND común** |
| 3 | INA | IO14 (U401-22) | Entrada canal A | ✅ |
| 4 | INB | IO21 (U401-23) | Entrada canal B | ✅ |
| 5 | INC | IO47 (U401-24) | Entrada canal C | ✅ |
| 6 | OUTD | IO48 (U401-25) | Salida canal D | ✅ |
| 7 | EN1 | R101 10 kΩ a DVCC | Alto = habilitado | ✅ |
| 8 | GND1 | GND | GND1 | 🔴 **Debe ser DGND** |
| 9 | GND2 | GND | GND2 (lado analógico) | 🔴 **Debe ser AGND** |
| 10 | EN2 | R100 10 kΩ a AVCC | Alto = habilitado | ✅ |
| 11 | IND | SPI_MISO_RN (U100-32) | Entrada canal D | ✅ |
| 12 | OUTC | SPI_CS_RN (U100-34) | Salida canal C | ✅ |
| 13 | OUTB | SPI_CLK_RN (U100-33) | Salida canal B | ✅ |
| 14 | OUTA | SPI_MOSI_RN (U100-35) | Salida canal A | ✅ |
| 15 | GND2 | GND | GND2 | 🔴 **Debe ser AGND** |
| 16 | VCC2 | AVCC_3v3 | 2.25–5.5 V; 0.1 µF a GND2 | ✅ |

**Verificación SPI (correcto):** los canales del ISO7741 están bien asignados:
- Canal A: `INA` (3) = `SPI3_MOSI_MCU` → `OUTA` (14) = `SPI_MOSI_RN` → RN SDI (35).
- Canal B: `INB` (4) = `SPI3_CS_MCU_RN` → `OUTB` (13) = `SPI_CS_RN` → RN SCSN (34).
- Canal C: `INC` (5) = `SPI3_CLK_MCU` → `OUTC` (12) = `SPI_CLK_RN` → RN SCLK (33).
- Canal D: `IND` (11) = `SPI_MISO_RN` ← RN SDO (32); `OUTD` (6) = `SPI3_MISO_MCU` → ESP32.
No hay cruce de CLK/CS. Ver §3.4.1 para la verificación completa.

**Hallazgo C3 — Aislamiento anulado.**  
Los cuatro pines de ground (2, 8, 9, 15) están en el mismo net `GND` **según el netlist del 31/10 22:59**. El ISO7741 no puede aislar nada; la barrera de 5000 Vrms está cortocircuitada. La corrección es separar `DGND` (ESP32, USB, microSD, RSM3485 lado lógico, HLK-10M05) de `AGND` (RN8302B, divisores, CTs, ISO7741 lado 2, HLK-5M03B). El ISO7741 es el único puente entre ambos; no debe haber otra conexión (ni un net tie, ni un 0 Ω, ni un capacitor Y salvo decisión EMI).

> **Nota (01/11):** las imágenes más recientes compartidas por el usuario muestran `GND1` (pines 2, 8) → `DGND` y `GND2` (pines 9, 15) → `AGND`. Si esa es la versión actual, **C3 ya está corregido** y el netlist del 31/10 está desactualizado. Reexportar el netlist/BOM para confirmar.

**Hallazgo M24 — Decoupling del ISO7741.**  
El datasheet pide 0.1 µF en cada VCC. El diseño tiene C400/C401 en `DVCC` (lado ESP32) y C203/C101-C105 en `AVCC` (lado RN), pero no hay un 0.1 µF dedicado junto a U101-1 y U101-16. Verificar en el layout; agregar si falta.

#### 3.3.3 Cristal X100

| Parámetro | Valor | Requisito RN8302B | Veredicto |
|---|---|---|---|
| Frecuencia | 8.192 MHz | 8.192 MHz típico | ✅ |
| Carga | 12 pF | 15 pF típico | ✅ |
| C100/C108 | 15 pF NP0 | 15 pF típico | ✅ |
| ESR | 60 Ω máx | No especificado | ⚠️ verificar arranque |
| R feedback | **No instalada** | 10 MΩ entre XI y XO | 🔴 **Falta** |

#### 3.3.4 Desacople del RN8302B

| Rail | Capacitores | Requisito | Veredicto |
|---|---|---|---|
| AVCC | C203 4.7 µF + FB100 + C101 1 µF + C102 100 nF + C103 10 µF + C104 100 nF + C105 100 nF | 10 µF + 0.1 µF | ✅ (buen margen) |
| DVCC | Igual rail AVCC (pines 28/40) | 10 µF + 0.1 µF | ✅ (misma rail) |
| REFV | **Ninguno** (pin 3 a AVCC) | 10 µF + 0.1 µF a AGND | 🔴 **Mal** |
| VO | C106 10 µF + C107 100 nF | 10 µF + 0.1 µF a DGND | ✅ |

---

### 3.4 `MCU.SchDoc`

#### 3.4.1 ESP32-S3-WROOM-1 — pin a pin (U401, 41 pines)

Datasheet: `ESP32-S3-WROOM_Module.pdf`, Table 3-1.

| Pin | Nombre | Netlist | Veredicto |
|---:|---|---|---|
| 1 | GND | GND | ✅ |
| 2 | 3V3 | FB400 → DVCC | ✅ (⚠️ desacople) |
| 3 | EN | EN (R400 10k, C402 1µF, C403 100nF, SW400) | ✅ |
| 4 | IO4 | — | ✅ |
| 5 | IO5 | Header 500-1 | ✅ |
| 6 | IO6 | Header 500-2 | ✅ |
| 7 | IO7 | Header 500-3 | ✅ |
| 8 | IO15 | — | ✅ |
| 9 | IO16 | R500 10k + U500-5 (CON RS485) | ✅ |
| 10 | IO17 | U500-4 (RXD) | ✅ |
| 11 | IO18 | U500-3 (TXD) | ✅ |
| 12 | IO8 | — | ✅ |
| 13 | IO19 | DN_USB (U400-4) | ✅ |
| 14 | IO20 | DP_USB (U400-6) | ✅ |
| 15 | IO3 | — | ✅ strapping |
| 16 | IO46 | — | ✅ strapping |
| 17 | IO9 | U501-9 (CD microSD) | ✅ |
| 18 | IO10 | Header 500-4 | ✅ |
| 19 | IO11 | Header 501-4 | ✅ |
| 20 | IO12 | Header 501-2 | ✅ |
| 21 | IO13 | Header 501-3 | ✅ |
| 22 | IO14 | U101-3 INA (MOSI RN) + U501-3 CMD (MOSI SD) | ✅ MOSI compartido |
| 23 | IO21 | U101-4 INB (CS RN) | ✅ CS del RN |
| 24 | IO47 | U101-5 INC (CLK RN) + U501-5 CLK (SD) | ✅ CLK compartido |
| 25 | IO48 | U101-6 OUTD (MISO RN) + U501-7 DAT0 (MISO SD) | ✅ MISO compartido |
| 26 | IO45 | — | ✅ strapping |
| 27 | IO0 | — | ✅ strapping |
| 28 | IO35 | — | ✅ (N4 sin PSRAM) |
| 29 | IO36 | — | ✅ |
| 30 | IO37 | — | ✅ |
| 31 | IO38 | U501-2 (CS SD) | ✅ |
| 32 | IO39 | — | ✅ |
| 33 | IO40 | — | ✅ |
| 34 | IO41 | — | ✅ |
| 35 | IO42 | — | ✅ |
| 36 | RXD0 | — | ✅ (USB-JTAG) |
| 37 | TXD0 | — | ✅ |
| 38 | IO2 | — | ✅ |
| 39 | IO1 | — | ✅ |
| 40 | GND | GND | ✅ |
| 41 | EPAD/GND | GND | ✅ |

**Verificación del bus SPI compartido — correcto.**  
El diseño usa un bus SPI3 compartido entre el RN8302B y la microSD, con CS separados. La asignación es:

| Señal | RN8302B (vía ISO7741) | microSD | GPIO ESP32 | Puerto | Veredicto |
|---|---|---|---|---|---|
| MOSI | `INA` (3) → `OUTA` (14) → RN SDI (35) ← IO14 | U501-3 CMD ← IO14 | IO14 (pin 22) | `SPI3_MOSI_MCU` | ✅ compartido |
| CLK | `INC` (5) → `OUTC` (12) → RN SCLK (33) ← IO47 | U501-5 CLK ← IO47 | IO47 (pin 24) | `SPI3_CLK_MCU` | ✅ compartido |
| CS RN | `INB` (4) → `OUTB` (13) → RN SCSN (34) ← IO21 | — | IO21 (pin 23) | `SPI3_CS_MCU_RN` | ✅ separado |
| MISO | RN SDO (32) → `IND` (11); `OUTD` (6) → IO48 | U501-7 DAT0 → IO48 | IO48 (pin 25) | `SPI3_MISO_MCU` | ✅ compartido |
| CS SD | — | U501-2 CD/DAT3 ← IO38 | IO38 (pin 31) | `SPI3_CS_MCU_SD` | ✅ separado |

- **CLK compartido:** IO47 → `INC` (5) → `OUTC` (12) → RN SCLK; y IO47 → SD CLK (pin 5). Correcto.
- **CS RN independiente:** IO21 → `INB` (4) → `OUTB` (13) → RN SCSN. Correcto.
- **CS SD independiente:** IO38 → SD CS (pin 2). Correcto.
- **MOSI/MISO compartidos:** el RN SDO y el SD DAT0 quedan en alta impedancia cuando su CS está alto; solo hay que garantizar que nunca estén seleccionados a la vez. Correcto.
- El netlist coincide con las imágenes: `NetU101_5` (U101-5 + U401-24 + U501-5) es el **CLK compartido**; `NetU101_4` (U101-4 + U401-23) es el **CS del RN**. La revisión anterior confundió los canales B/C del ISO7741 (B = CS, C = CLK); las imágenes y el netlist lo confirman.

**Conclusión:** **no hay error en el SPI**. El bus compartido con CS separados es correcto. Verificar solo el retardo del ISO7741 (~10.7 ns) a la velocidad de SD elegida; a 3.5 Mbps es despreciable.

**Hallazgo M1 — Desacople del módulo.**  
El pin 2 (3V3) va por FB400 a `DVCC`; C400 22 µF y C401 100 nF están en `DVCC`, no en el pin del módulo. El datasheet del ESP32-S3-WROOM recomienda 22 µF + 0.1 µF junto al pin 3V3. Agregar 10 µF + 0.1 µF en `NetFB400_1` (lado módulo) o eliminar FB400.

**Hallazgo H4 (repetido) — USB-C 500 mA.**  
R401/R402 = 5.11 kΩ a GND: correcto para *sink* USB-C. Pero el límite de 500 mA no alcanza para la carga. Ver §3.1.6.

**Hallazgo M13 — Backfeed header 200 / USB.**  
`5V_USB` une el VBUS del USB-C y el pin 1 del header 200. Si se conecta una fuente externa de 5 V en el header 200 y también un cable USB, las dos fuentes quedan en paralelo. Poner un diodo OR-ing (otro MS2A40LWS) o un jumper, y marcar el header como entrada/salida.

#### 3.4.2 USB-C y protección

| Pin | Nombre | Netlist | Veredicto |
|---|---|---|---|
| A5 | CC1 | R401 5.11 kΩ a GND | ✅ |
| B5 | CC2 | R402 5.11 kΩ a GND | ✅ |
| A6/B6 | DP | U400-1 / U400-6 → DP_USB | ✅ |
| A7/B7 | DN | U400-3 / U400-4 → DN_USB | ✅ |
| A4/B9, B4/A9 | VBUS | 5V_USB | ✅ |
| A1/B12, B1/A12 | GND | GND | ✅ |
| A8, B8 | SBU | — | ✅ |
| SHLD | Shield | GND | ✅ |

- U400 USBLC6-2SC6: pin 1/6 = I/O1, pin 3/4 = I/O2, pin 2 = GND, pin 5 = VBUS. El diseño coincide. ✅
- **M14:** no hay fusible/PTC en VBUS. El USB-C source limita, pero para protección de la placa agregar un fusible rearmable de 1 A.

---

### 3.5 `INTERFACES.SchDoc`

#### 3.5.1 RSM3485PCT — pin a pin (U500, 10 pines)

Datasheet: `RSM3485PCT_Datasheet.pdf`, tabla de pines.

| Pin | Nombre | Netlist | Requisito datasheet | Veredicto |
|---:|---|---|---|---|
| 1 | **VCC** | **GND** | 3.15–3.45 V | 🔴 **Invertido** |
| 2 | **GND** | **DVCC (vía FB500)** | GND | 🔴 **Invertido** |
| 3 | TXD | IO18 (U401-11) | Entrada UART | ✅ |
| 4 | RXD | IO17 (U401-10) | Salida UART | ✅ |
| 5 | CON | R500 10 kΩ a DVCC + IO16 | Control de dirección | ✅ (reposo = receive) |
| 6 | — | — | NC | ✅ |
| 7 | VO | — | Salida aislada 5 V, 100 mA | ✅ (no usada) |
| 8 | B | J500-2, D500-2, R501-1 | Bus B | ✅ |
| 9 | A | J500-3, D500-1, R501-2 | Bus A | ✅ |
| 10 | **RGND** | **GND** | Tierra aislada del bus | 🔴 **Mal** |

**Hallazgo C4 — VCC/GND invertidos.**  
El pin 1 (VCC) está a `GND` y el pin 2 (GND) está a `DVCC` a través de FB500. El módulo queda alimentado al revés. Corregir: pin 1 → `DVCC` (con FB500 y C502), pin 2 → `DGND`.

**Hallazgo C5 — RGND al GND digital.**  
El pin 10 es la tierra aislada del lado del bus. Está unido a `GND`, igual que J500-1 y D500-3. El aislamiento de 2500 VDC del módulo queda anulado. Corregir: crear `BUS_GND` (aislada) y conectar ahí U500-10, J500-1, D500-3 y el capacitor de desacople del lado del bus. No unir `BUS_GND` a `DGND` ni a `AGND`.

**Observaciones:**
- CON: el datasheet indica CON=0 → transmisión, CON=1 → recepción (tabla 6.5). R500 10 kΩ a DVCC deja el módulo en recepción al arrancar. ✅
- TXD tiene pull-up interno de 10 kΩ; el ESP32 lo maneja. ✅
- A/B: la terminación de 120 Ω (R501) está permanente. Si el medidor no está en un extremo del bus, la terminación carga el bus. Hacerla seleccionable con jumper. ⚠️
- **M12:** no hay resistencias de bias (pull-up en A, pull-down en B). El receptor del RSM3485 tiene umbral ±10 mV; con el bus idle (A−B=0) el estado es indeterminado. Verificar si el módulo tiene bias interno; si no, agregar 4.7 kΩ.
- **M3:** C501 100 nF está en `DVCC` (antes de FB500); C502 10 µF está en el lado del módulo. El 0.1 µF debe estar junto al pin VCC del módulo. Mover/agregar.

#### 3.5.2 microSD — pin a pin (U501)

| Pin | Nombre | Netlist | Veredicto |
|---:|---|---|---|
| 1 | DAT2 | R504 10 kΩ a DVCC | ✅ |
| 2 | CD/DAT3 | R503 10 kΩ + IO38 (CS) | ✅ |
| 3 | CMD | R502 10 kΩ + IO14 (MOSI) | ✅ MOSI compartido (correcto) |
| 4 | VDD | FB501 → DVCC | ✅ (⚠️ sin desacople local) |
| 5 | CLK (símbolo CLX) | IO47 | ✅ CLK compartido con el RN |
| 6 | VSS | GND | ✅ |
| 7 | DAT0 | R505 10 kΩ + IO48 (MISO) | ✅ MISO compartido (correcto) |
| 8 | DAT1 | R506 10 kΩ a DVCC | ✅ |
| 9 | CD | R507 10 kΩ + IO9 | ✅ |
| 10 | GND/shell | GND | ✅ |

**SPI (verificado):** el pin 5 (CLK) de U501 está en `NetU101_5` con U101-5 (`INC` → `OUTC` → RN SCLK) y U401-24 (IO47); es el **CLK compartido**. El CS del RN está en `NetU101_4` (U101-4 `INB` → `OUTB` → RN SCSN + U401-23 IO21) y el CS de la SD en `NetR503_1` (U401-31 IO38 + U501-2). Los pines 3 (CMD/MOSI) y 7 (DAT0/MISO) están correctamente compartidos. **No hay error.**

**Hallazgo M2 — Desacople de VDD.**  
`NetFB501_1` (pin 4) no tiene capacitor local; C500/C501 están en `DVCC`. Agregar 10 µF + 0.1 µF junto al conector.

**Hallazgo L2 — Símbolo CLX.**  
El símbolo llama `CLX` al pin 5; el datasheet y el estándar dicen `CLK`. Corregir la librería.

#### 3.5.3 Headers 500/501 (HaLow)

| Header | Pin | Netlist | Observación |
|---|---:|---|---|
| 500 | 1 | IO5 | — |
| 500 | 2 | IO6 | — |
| 500 | 3 | IO7 | — |
| 500 | 4 | IO10 | — |
| 500 | 5-7 | — | Sin conectar |
| 501 | 1 | — | Sin conectar |
| 501 | 2 | IO12 | — |
| 501 | 3 | IO13 | — |
| 501 | 4 | IO11 | — |
| 501 | 5 | FB503 → DVCC (3.3 V) | ✅ 3.3 V |
| 501 | 6 | GND | ✅ |
| 501 | 7 | FB502 → Vin_buck_5V (5 V) | ✅ 5 V |

- El módulo Seeed Wio-WM6108 para XIAO **requiere 3.3 V y 5 V**; el diseño provee ambos. ✅
- **M19 / abierto:** el mapeo de señales no coincide con el header XIAO estándar (XIAO usa D0-D10 = GPIO1-GPIO11; aquí se usan IO12/IO13, que no están en el header XIAO). Si el módulo es un XIAO, el pinout no encaja. Si es un carrier propio para el FGH100M, falta documentar el pinout. El README dice que el FGH100M no está en `MCU.SchDoc`; los headers son provisionales. Definir antes de fabricar.
- **M25:** el header 500 tiene 7 pines pero solo 4 conectados; el 501 tiene 6/7. Confirmar que los pines no usados no queden flotantes en el módulo.

---

### 3.6 `MAIN.SchDoc`

- `MAIN.SchDoc` contiene 5 sheet symbols (`THREE PHASES`, `POWER`, `MEASURES`, `MCU`, `INTERFACES`) pero **no tiene sheet entries** (RECORD=16). La jerarquía no está cableada; la conexión entre hojas depende de etiquetas globales/power ports.
- **Hallazgo M20:** la hoja raíz no conecta nada. Si se usan etiquetas globales, funciona; pero es frágil y ya produjo el problema de la entrada AC flotante. Recomendación: agregar sheet entries/ports para las señales inter-hoja (AC_L/AC_N, SPI, UART, etc.) o documentar explícitamente que se usan etiquetas globales.
- **Hallazgo de proyecto:** `hardware/libraries/Library_Analizador.IntLib` no está en la raíz de `hardware/libraries/`; solo existe en `Project Outputs for Library_Analizador/`. Los `.SchDoc` referencian `Library_Analizador.IntLib`. Sin esa IntLib, `Tools → Update from Library` no funciona. Es la decisión pendiente A/B del `AGENTS.md` §9; **no se tocó**.

---

### 3.7 Checklist de máximos por IC/módulo

Esta tabla resume los criterios máximos del datasheet contra lo implementado. El detalle pin a pin está en §3.1–§3.5.

#### RN8302B (U100)

| Criterio | Requisito datasheet | Diseño | Veredicto |
|---|---|---|---|
| AVCC / DVCC | 3.0–3.6 V | 3.3 V (AVCC_3v3) | ✅ (excepto pin 9 flotante) |
| Consumo EMM | 5 mA típico | Rail AVCC 1.5 A | ✅ |
| REFV | 1.25 V ±4 %, 10 µF + 0.1 µF a AGND | Pin 3 a AVCC 3.3 V | 🔴 |
| Entradas analógicas | 800 mVpp máx | 0.656 Vpp a 230 V; 0.790 Vpp a 277 V | ✅ / ⚠️ |
| SPI | 3.5 Mbps máx | 3.5 Mbps (ISO7741) | ✅ |
| Cristal | 8.192 MHz, 10 MΩ entre XI/XO | 8.192 MHz, sin 10 MΩ | 🔴 |
| Temperatura | −40 a +85 °C | — | ✅ |
| Desacople | 10 µF + 0.1 µF en AVCC, DVCC, REFV, VO | AVCC/DVCC/VO sí; REFV no | 🔴 |

#### ISO7741 (U101)

| Criterio | Requisito datasheet | Diseño | Veredicto |
|---|---|---|---|
| VCC1 / VCC2 | 2.25–5.5 V | 3.3 V | ✅ |
| ICC1 / ICC2 | 5.2 / 5.7 mA máx a 10 Mbps | 3.5 Mbps, <5 mA | ✅ |
| Data rate | 100 Mbps máx | 3.5 Mbps | ✅ |
| Aislamiento | 5000 Vrms | GND1/GND2 unidos | 🔴 |
| CMTI | 100 kV/µs | — | ✅ (si layout) |
| EN1 / EN2 | Alto = habilitado | 10 kΩ a VCC | ✅ |
| Desacople | 0.1 µF en cada VCC | Verificar layout | ⚠️ |

#### ESP32-S3-WROOM-1 (U401)

| Criterio | Requisito datasheet | Diseño | Veredicto |
|---|---|---|---|
| Alimentación | 3.0–3.6 V | 3.3 V (DVCC) | ✅ |
| Corriente | 500 mA máx | Buck 2 A | ✅ |
| EN | 10 kΩ + 1 µF | 10 kΩ + 1 µF + 0.1 µF | ✅ |
| USB | D− = IO19, D+ = IO20 | IO19/IO20 | ✅ |
| Strapping | IO0/3/45/46 | No conectados; pulls internos | ✅ |
| Desacople | 22 µF + 0.1 µF en 3V3 | C400/C401 antes de FB400 | ⚠️ |
| Antena | Keepout | Verificar layout | ⚠️ |

#### RSM3485PCT (U500)

| Criterio | Requisito datasheet | Diseño | Veredicto |
|---|---|---|---|
| VCC | 3.15–3.45 V | Pin 1 a GND, pin 2 a DVCC | 🔴 |
| Consumo | 30 mA típ / 130 mA máx | Buck 2 A | ✅ |
| Aislamiento | 2500 VDC | RGND a GND | 🔴 |
| Data rate | 9600 bps | 9600 bps | ✅ |
| Nodos | 64 | — | ✅ |
| CON | 0 = TX, 1 = RX | 10 kΩ a DVCC (RX) | ✅ |
| Temperatura | −40 a +85 °C | — | ✅ |

#### AP63203WU-7 (U201)

| Criterio | Requisito datasheet | Diseño | Veredicto |
|---|---|---|---|
| VIN | 3.8–32 V | 5 V | ✅ |
| IOUT | 2 A | 1.2 A máx | ✅ |
| VOUT | 3.3 V fijo | 3.3 V | ✅ |
| fsw | 1.1 MHz | 1.1 MHz | ✅ |
| Inductor | 3.9–4.7 µH, >2.3 A | 3.9 µH, 2.3 A | ✅ |
| Temperatura | −40 a +85 °C | — | ✅ |

#### SY6280AAC (U200)

| Criterio | Requisito datasheet | Diseño | Veredicto |
|---|---|---|---|
| VIN | 2.4–5.5 V | 5 V | ✅ |
| IOUT | 2 A máx | 0.83 A limitado | ✅ |
| Ilim | 6800/Rset | R201 8.2 kΩ → 0.83 A | ⚠️ respaldo |
| Rds(on) | 80 mΩ | — | ✅ |
| EN | Activo alto, no flotar | a VIN | ✅ |
| Reverse blocking | Bloquea en shutdown | D201 + switch | ✅ (verificar) |

#### USBLC6-2SC6 (U400)

| Criterio | Requisito datasheet | Diseño | Veredicto |
|---|---|---|---|
| Líneas | 2 | D+/D− | ✅ |
| VBUS | 5.25 V standoff | 5 V | ✅ |
| Capacitancia | 3.5 pF máx | — | ✅ |
| ESD | IEC 61000-4-2 | — | ✅ |

#### SM712 (D500)

| Criterio | Requisito datasheet | Diseño | Veredicto |
|---|---|---|---|
| Canales | 2 | A/B | ✅ |
| Vrwm | 7 V | RS-485 | ✅ |
| Ipp | 18 A | — | ✅ |
| Tierra | GND del bus | GND digital | 🔴 (por C5) |

#### HLK-10M05 / HLK-5M03B

| Criterio | Requisito datasheet | Diseño | Veredicto |
|---|---|---|---|
| Entrada AC | 85–265 VAC | Flotante | 🔴 |
| Salida 10M05 | 5 V / 2 A / 10 W | 1.7 A máx | ✅ |
| Salida 5M03B | 3.3 V / 1.5 A / 5 W | 11 mA | ✅ |
| Aislamiento | 3000 VAC | GND común | 🔴 |
| No-load | <0.1 W | — | ✅ |
| Temperatura | −40 a +85 °C | — | ✅ |

### 3.8 Checklist de protecciones

| Bloque | Protección requerida | Implementado | Veredicto |
|---|---|---|---|
| Entrada AC | Fusible + MOV + creepage | Fusible 200 mA + MOV (solo divisor); HLK sin fusible; sin conector AC | 🔴/🟠 |
| Entrada DC 5 V | OR-ing + PTC + reversa | D200/D202 OR; sin PTC; header 200 directo | ⚠️ |
| Buck | OCP, OTP, UVLO | AP63203 integra OCP/OTP/UVLO | ✅ |
| Supercap | Clamp de sobretensión + balanceo | Balanceo 1 kΩ; sin clamp | ⚠️ |
| RS-485 | TVS + terminación + bias + aislamiento | SM712 + 120 Ω; sin bias; aislamiento anulado | 🔴 |
| USB | ESD + CC + fusible | USBLC6 + 5.11 kΩ; sin fusible | ⚠️ |
| CT | TVS/clamp + burden + cortocircuito | Burden 10 Ω; sin TVS | 🟠 |
| Divisor de tensión | Resistores de alta tensión + MOV | MOV; resistores 0603 75 V | 🟠 |
| Térmica | D200/D202, AP63203, SY6280 | Sin verificación | 🟠 |

## 4. Auditoría del BOM

### 4.1 MPN que no coinciden con el valor (críticos)

El BOM exportado tiene la columna `Name` (comentario de librería) y `Description` (valor). La columna `Manufacturer Part Number 1` es la que usa el ensamblador. Varias líneas tienen un MPN que no corresponde al valor:

| Designador(es) | Valor según descripción | MPN en el BOM | Qué se colocaría realmente | Criticidad |
|---|---|---|---|---|
| C102, C104, C105, C107, C204 | 100 nF | `HGC0603G0150J500NTHJ` | 15 pF | 🔴 Crítico |
| C103, C106, C200, C208 | 10 µF | `RT0603BRD07165KL` | Resistencia 165 kΩ | 🔴 Crítico |
| C500, C502 | 10 µF | `1RC0603F1002` | Resistencia 10 kΩ | 🔴 Crítico |
| C501 | 100 nF | `1RC0603F1002` | Resistencia 10 kΩ | 🔴 Crítico |
| C205, C206, C400 | 22 µF | `049SS2-8.192F12DZLAL` | Cristal 8.192 MHz | 🔴 Crítico |

**Consecuencia:** el desacople de los rieles, el bootstrap del buck (C204), el filtro de AVCC y los capacitores de salida del buck quedarían con componentes incorrectos. La placa no funcionaría o sería inestable.

**Corrección:** regenerar el BOM desde Altium después de corregir los part numbers en la librería, o corregir manualmente la columna MPN. Verificar cada línea contra el valor del esquemático y el stock de LCSC.

### 4.2 Inconsistencias de comentario/valor (no críticas)

| Designador(es) | Comentario (`Name`) | Valor real (`Description`/MPN) | Observación |
|---|---|---|---|
| R201 | `UNI-ROYAL HP05W3F100JT5E` (10 Ω) | 8.2 kΩ (`FRC0603F8201TS`) | El comentario está viejo; el MPN es 8.2 kΩ. |
| R401, R402 | `UNI-ROYAL HP05W3F100JT5E` (10 Ω) | 5.11 kΩ (`HRC0603F5111ENTN`) | El comentario está viejo; el MPN es 5.11 kΩ (correcto para USB-C). |
| R303–R308, R314–R319, R326–R331 | Bourns `CR0603-FX-1653ELF` | Yageo `RT0603BRD07165KL` | Ambos 165 kΩ 0.1 %; el MPN real es Yageo. Documentar. |
| C101, C402 | Samsung `CL10B105KB8NQNC` | Mismo | El proveedor dice "LSCS" (typo); corregir. |

### 4.3 Observaciones generaes del BOM

- El BOM es "plano" (una fila por designador), no agrupado por valor. Para comprar, agrupar y sumar cantidades.
- Faltan precios/proveedor en muchas líneas; no es bloqueante, pero complica la compra.
- Los conectores 200/500/501 están en stock (según `AGENTS.md`); no requieren MPN.
- La bornera U301 (`C49291885`, 4 pines, 250 V) y J500 (`MX126-5.0-03P`, 3 pines, 300 V) son piezas distintas; el BOM las lista por separado. ✅ (pero ver H7 por la tensión de U301).
- Varios capacitores de 0805 usan la huella llamada `R0805` (C103/C106/C200/C208/C500/C502 y C205/C206/C400). El tamaño es 0805, pero el nombre es de resistor; verificar el land pattern y renombrar a `C0805` para evitar errores de ensamblaje.

---

## 5. Lista de novedades ordenada por criticidad

> **Criterio:** Crítico = no funciona, daña un componente o viola seguridad/aislamiento. Alto = funciona mal o margen insuficiente. Medio = degrada precisión/robustez. Bajo = documentación/mejora.

### 🔴 Críticos

| ID | Hallazgo | Ubicación | Corrección propuesta |
|---|---|---|---|
| C1 | Entrada AC de PS200/PS201 flotante | `NetFB200_1`, `NetPS200_2`, `NetFB200_2`, `NetFB201_1` | Conectar PS200-1/PS201-1 a fase y PS200-2/PS201-2 a neutro, con fusible/MOV y conector AC. |
| C2 | RN8302B REFV a AVCC y AVCC pin 9 flotante | U100-3, U100-9 | Pin 9 → AVCC con 10 µF+0.1 µF; pin 3 → 10 µF+0.1 µF a AGND. |
| C3 | ISO7741 GND1/GND2 unidos | U101-2/8/9/15 | Separar DGND/AGND; ISO7741 es el único puente. |
| C4 | RSM3485PCT VCC/GND invertidos | U500-1, U500-2 | Pin 1 → DVCC; pin 2 → DGND. |
| C5 | RSM3485PCT RGND/J500/SM712 al GND digital | U500-10, J500-1, D500-3 | Crear BUS_GND aislada; conectar ahí RGND, J500-1 y D500-3. |
| C6 | HLK-10M05 y HLK-5M03B comparten GND | PS200-3, PS201-3, GND | Separar AGND (PS201) y DGND (PS200); unir solo en el ISO7741. |
| C7 | Ferritas 0603 en líneas AC | FB200, FB201 | Eliminar o reemplazar por choke/inductor apto para 230 V AC. |
| C8 | BOM con MPN de capacitores incorrectos | C102/C103/C104/C105/C106/C107/C200/C204/C205/C206/C208/C400/C500/C501/C502 | Corregir MPN y regenerar BOM. |

### 🟠 Altos

| ID | Hallazgo | Ubicación | Corrección |
|---|---|---|---|
| H1 | Falta 10 MΩ entre XI y XO | U100-36/37 | Agregar 10 MΩ 1 % entre X100-1 y X100-2. |
| H2 | D200/D202 SOD-323 a ~1.7 A / 0.8 W | D200, D202 | Usar SMA/SMB 3 A o dos diodos; verificar temperatura. |
| H3 | SY6280 Ilim 0.83 A vs respaldo ~0.9–1.0 A | R201 | Bajar R201 a ~6.8 kΩ (1 A) o reducir carga de respaldo. |
| H4 | USB-C 500 mA vs carga >600 mA | R401/R402, D202, buck | Limitar carga en USB o negociar PD; usar header 200 para operación. |
| H5 | Sin detección de caída de red | `Vin_buck_5V` / `Vout_5V` | Divisor + comparador a GPIO, o ADC de 5 V. |
| H6 | CT sin TVS/clamp | U300/U302/U303/U304 | BAT54S/TVS en las entradas; cortocircuitador de CT. |
| H7 | U301 250 V para 400 V entre fases | U301 | Bornera 600 V o mayor creepage. |
| H8 | Resistencias 0603 de 75 V en divisor de 230 V | R303–R308, R314–R319, R326–R331 | 0805/1206 o más en serie; verificar tensión de pulso. |
| H9 | Sin fusible/protección AC dedicada para HLK | PS200/PS201 | Fusible 1 A + MOV/choke para los HLK; separar del fusible del divisor. |
| H10 | Margen 5 V 15 % con carga máxima + carga de supercaps | D200, HLK-10M05 | Verificar térmica; limitar carga de supercaps o usar HLK de mayor potencia. |

### 🟡 Medios

| ID | Hallazgo | Ubicación | Corrección |
|---|---|---|---|
| M1 | ESP32 sin 22 µF/0.1 µF después de FB400 | U401-2, FB400 | Agregar 10 µF+0.1 µF en el lado módulo o quitar FB400. |
| M2 | microSD sin desacople local en VDD | U501-4, FB501 | Agregar 10 µF+0.1 µF junto al conector. |
| M3 | RSM3485 0.1 µF en el lado equivocado | C501/C502 | Mover 0.1 µF al pin VCC del módulo. |
| M4 | SY6280 sin capacitor de salida | U200-1 | Agregar 1 µF+10 µF junto al OUT. |
| M5 | Supercaps con solo ~0.08 V de margen a 5.25 V | C201/C202 | Clamp 5.1 V o balanceo más fuerte. |
| M6 | Descarga de 150 Ω del SY6280 consume respaldo | U200 | Considerar load switch sin descarga o aceptar ~3 %. |
| M7 | 1 kΩ 1 % y X7R en divisor de precisión | R310/R320/R332, C302/C306/C309 | 0.1 % bajo TCR y C0G. |
| M8 | CT/Rogowski sin modelo definido | U300/U302/U303/U304 | Definir relación, carga y burden. |
| M9 | Mapeo de fases sin documentar | U300/U302/U303, F300/F301/F302 | Etiquetar L1/L2/L3 y verificar en layout. |
| M10 | SCSN del RN sin pull-up | U100-34 | 10 kΩ a AVCC. |
| M11 | Sin resistencias serie en SPI | U101/U100 | 22–33 Ω en las líneas, si la longitud lo requiere. |
| M12 | RS-485 sin bias | A/B | 4.7 kΩ pull-up A / pull-down B si el módulo no trae fail-safe. |
| M13 | Backfeed USB/header 200 | 200-1, 5V_USB | Diodo OR-ing o jumper. |
| M14 | Sin fusible en VBUS | j400 | PTC 1 A. |
| M15 | HLK-5M03B conmutado alimenta el AFE | PS201 | Verificar ripple; mantener FB100 y el banco de caps. |
| M16 | U301 sin etiquetas N/L1/L2/L3 | U301 | Marcar y usar keying. |
| M17 | MOV después del fusible | RV300–RV302 | Coordinar MOV/fusible. |
| M18 | Jack CT usa pines 2/3 (posible ring/sleeve) | U300/U302/U303/U304 | Verificar pinout; documentar plug TRS o usar tip/sleeve. |
| M19 | Headers HaLow no coincide con XIAO | 500/501 | Definir pinout del módulo antes de fabricar. |
| M20 | MAIN sin sheet entries | MAIN.SchDoc | Agregar ports/sheet entries o documentar etiquetas globales. |
| M21 | Comentarios obsoletos en BOM (R201/R401/R402) | BOM | Actualizar comentarios/valores. |
| M22 | README con arquitectura desactualizada | README.md | Corregir puente rectificador, conectores y GPIO. |
| M23 | Huellas `R0805` usadas para capacitores de 0805 | C103/C106/C200/C208/C500/C502, C205/C206/C400 | Verificar que el land pattern 0805 sea el correcto; renombrar la huella a `C0805`. |
| M24 | Sin 0.1 µF dedicado en VCC1/VCC2 del ISO7741 | U101-1, U101-16 | Agregar 0.1 µF junto a cada pin. |
| M25 | Headers 500/501 con pines no usados | 500, 501 | Confirmar que no queden flotantes en el módulo HaLow. |

### 🟢 Bajos

| ID | Hallazgo | Ubicación | Corrección |
|---|---|---|---|
| L1 | Símbolo RN8302B pin 22 = CF5 (debe ser CTT) | Schlib1.SchLib | Corregir nombre. |
| L2 | Símbolo TF card pin 5 = CLX (debe ser CLK) | Schlib1.SchLib | Corregir nombre. |
| L3 | Símbolo ISO6742DWR sin usar | Schlib1.SchLib | Eliminar o marcar obsoleto. |
| L4 | `Library_Analizador.IntLib` ausente en `hardware/libraries/` | `hardware/libraries/` | Decidir A/B del AGENTS.md §9. |
| L5 | C401/C403 Y5V | C401/C403 | Usar X7R/X5R. |
| L6 | Sin test points en rieles/SPI | PCB | Agregar TP para 5V, 3.3V, AVCC, GND, SPI. |
| L7 | Sin ESD en jacks de CT | U300/U302/U303/U304 | TVS/ESD. |
| L8 | Sin protección de polaridad inversa en header 200 | 200 | D202 ya protege; documentar. |
| L9 | INTN del RN8302B no llega al ESP32 | U100-31 | Conectar a GPIO o dejar documentado que no se usa. |

---

## 6. Verificación recomendada antes de fabricar

### 6.1 En Altium (lo debe hacer el humano)

1. Corregir C1–C8 en los `.SchDoc` (idealmente en una rama `fix/revision-esquematicos`).
2. Recompilar el proyecto (`Project → Compile Project`) y revisar `Messages` (ERC).
3. Reexportar el netlist y el BOM; comparar contra este informe.
4. Ejecutar `Tools → Update from Library` después de corregir la librería.
5. Revisar el layout:
   - Creepage/clearance de 230 V/400 V: U301, F300–F302, RV300–RV302, divisores, HLK, primario.
   - Barrera de aislamiento del ISO7741: >8 mm, sin cobre cruzando.
   - Separación AGND/DGND; ISO7741 como único puente.
   - Keepout de antena del ESP32-S3.
   - Pares diferenciales USB 90 Ω.
   - Nodo SW del buck corto; C207/C208 junto a VIN; L200 junto a SW.
   - Térmica de D200/D202, AP63203, SY6280, HLK.
   - Trazas de CT diferenciales y alejadas de la conmutación.

### 6.2 En laboratorio (con fuente limitada)

1. **No conectar 230 V todavía.** Alimentar con 5 V limitada a 1 A por el header 200 o USB.
2. Medir DVCC = 3.3 V, AVCC = 3.3 V, REFV = 1.25 V, VO = 1.8 V (si aplica).
3. Verificar que U500-1 = 3.3 V y U500-2 = 0 V (después de corregir C4).
4. Verificar aislamiento: resistencia entre AGND y DGND > 1 GΩ (después de C3/C6).
5. Comunicar con el RN8302B por SPI a 1 MHz y luego 3.5 MHz; leer `DeviceID` (0x830200).
6. Leer/escribir la microSD con el RN deseleccionado; verificar que no haya contención en MISO.
7. Probar RS-485 a 9600 bps con el bus terminado y el CON en receive/transmit.
8. Verificar USB-C: enumeración, D+/D−, y que el riel de 5 V no caiga al transmitir Wi-Fi.
9. Calibrar tensión/corriente con un patrón; verificar 0.5S si es el objetivo.
10. Probar el respaldo: cortar 5 V, medir el tiempo hasta que DVCC caiga, con la carga de *last gasp* definida.
11. Medir temperatura de D200, D202, U201 y HLK a plena carga 30 min.

---

## Anexo A — Matriz de conexiones de pasivos y conectores

> El netlist de Altium no exporta las redes de un solo pin. Por eso, si un pin no aparece en esta matriz, está **sin conectar** en el esquemático. Los ICs y módulos ya están pin a pin en las secciones 3.1–3.5.

### A.1 — Pasivos y diodos de 2 pines

| Designador | Huella | Pin 1 | Pin 2 |
|---|---|---|---|
| 200 | H_2x1_TH_100mil | `5V_USB` | `Net200_2` |
| C100 | C0603 | `GND` | `XI` |
| C101 | C0603 | `GND` | `NetC101_2` |
| C102 | C0603 | `GND` | `NetC101_2` |
| C103 | R0805 | `GND` | `NetC101_2` |
| C104 | C0603 | `GND` | `NetC101_2` |
| C105 | C0603 | `GND` | `NetC101_2` |
| C106 | R0805 | `GND` | `VO` |
| C107 | C0603 | `GND` | `VO` |
| C108 | C0603 | `GND` | `XO` |
| C200 | R0805 | `GND` | `Vin_buck_5V` |
| C201 | CAP-TH_BD18.0-P7.50-D0.8-FD-H26.0 | `NetC201_1` | `NetC201_2` |
| C202 | CAP-TH_BD18.0-P7.50-D0.8-FD-H26.0 | `NetC201_2` | `GND` |
| C203 | CAP-SMD_BD4.0-L4.3-W4.3-FD | `AVCC_3v3` | `GND` |
| C204 | C0603 | `NetC204_1` | `NetC204_2` |
| C205 | R0805 | `GND` | `DVCC_3v3` |
| C206 | R0805 | `GND` | `DVCC_3v3` |
| C207 | CAP-SMD_BD4.0-L4.3-W4.3-FD | `NetC207_1` | `GND` |
| C208 | R0805 | `GND` | `NetC207_1` |
| C300 | C0603 | `GND` | `NetC300_2` |
| C301 | C0603 | `NetC301_1` | `GND` |
| C302 | C0603 | `GND` | `NetC302_2` |
| C303 | C0603 | `NetC303_1` | `GND` |
| C304 | C0603 | `GND` | `NetC304_2` |
| C305 | C0603 | `NetC305_1` | `GND` |
| C306 | C0603 | `GND` | `NetC306_2` |
| C307 | C0603 | `NetC307_1` | `GND` |
| C308 | C0603 | `GND` | `NetC308_2` |
| C309 | C0603 | `GND` | `NetC309_2` |
| C310 | C0603 | `NetC310_1` | `GND` |
| C311 | C0603 | `NetC311_1` | `GND` |
| C312 | C0603 | `GND` | `NetC312_2` |
| C313 | C0603 | `NetC313_1` | `GND` |
| C400 | R0805 | `GND` | `DVCC_3v3` |
| C401 | C0603 | `GND` | `DVCC_3v3` |
| C402 | C0603 | `GND` | `EN` |
| C403 | C0603 | `EN` | `GND` |
| C500 | R0805 | `GND` | `DVCC_3v3` |
| C501 | C0603 | `GND` | `DVCC_3v3` |
| C502 | R0805 | `GND` | `NetC502_2` |
| D200 | SOD-323 | `Vin_buck_5V` (K) | `Vout_5V` (A) |
| D201 | SOD-323 | `Vin_buck_5V` (K) | `NetC201_1` (A) |
| D202 | SOD-323 | `NetC207_1` (K) | `Net200_2` (A) |
| FB100 | C0603 | `NetC101_2` | `AVCC_3v3` |
| FB200 | C0603 | `NetFB200_1` | `NetFB200_2` |
| FB201 | C0603 | `NetFB201_1` | `NetFB200_1` |
| FB202 | C0603 | `NetC207_1` | `Vin_buck_5V` |
| F300 | FUSE-SMD_L6.1-W2.7 | `NetF300_1` | `NetF300_2` |
| F301 | FUSE-SMD_L6.1-W2.7 | `NetF301_1` | `NetF301_2` |
| F302 | FUSE-SMD_L6.1-W2.7 | `NetF302_1` | `NetF302_2` |
| FB400 | C0603 | `NetFB400_1` | `DVCC_3v3` |
| FB500 | C0603 | `NetC502_2` | `DVCC_3v3` |
| FB501 | C0603 | `NetFB501_1` | `DVCC_3v3` |
| FB502 | C0603 | `Vin_buck_5V` | `Net501_7` |
| FB503 | C0603 | `DVCC_3v3` | `Net501_5` |
| L200 | IND-SMD_L4.0-W4.0_VLCF4028T | `NetC204_1` | `DVCC_3v3` |
| R100 | C0603 | `NetR100_1` | `AVCC_3v3` |
| R101 | C0603 | `NetR101_1` | `DVCC_3v3` |
| R102 | C0603 | `AVCC_3v3` | `NetR102_2` |
| R103 | C0603 | `NetR103_1` | `AVCC_3v3` |
| R200 | C0603 | `NetC201_2` | `NetC201_1` |
| R201 | 0603_RES | `GND` | `NetR201_2` |
| R202 | C0603 | `GND` | `NetC201_2` |
| R300 | C0603 | `NetC300_2` | `NetR300_2` |
| RV300 | MOV14D471K | `NetF300_2` | `GND` |
| R301 | R0805 | `GND` | `NetR300_2` |
| RV301 | MOV14D471K | `NetF301_2` | `GND` |
| R302 | R0805 | `NetR302_1` | `GND` |
| RV302 | MOV14D471K | `NetF302_2` | `GND` |
| R303 | 0603_RES | `NetR303_1` | `NetF300_2` |
| R304 | 0603_RES | `NetR304_1` | `NetR303_1` |
| R305 | 0603_RES | `NetR305_1` | `NetR304_1` |
| R306 | 0603_RES | `NetR306_1` | `NetR305_1` |
| R307 | 0603_RES | `NetR307_1` | `NetR306_1` |
| R308 | 0603_RES | `NetC302_2` | `NetR307_1` |
| R309 | C0603 | `NetC301_1` | `NetR302_1` |
| R310 | C0603 | `GND` | `NetC302_2` |
| R311 | C0603 | `NetC304_2` | `NetR311_2` |
| R312 | C0603 | `NetC303_1` | `GND` |
| R313 | R0805 | `GND` | `NetR311_2` |
| R314 | 0603_RES | `NetR314_1` | `NetF301_2` |
| R315 | 0603_RES | `NetR315_1` | `NetR314_1` |
| R316 | 0603_RES | `NetR316_1` | `NetR315_1` |
| R317 | 0603_RES | `NetR317_1` | `NetR316_1` |
| R318 | 0603_RES | `NetR318_1` | `NetR317_1` |
| R319 | 0603_RES | `NetC306_2` | `NetR318_1` |
| R320 | C0603 | `GND` | `NetC306_2` |
| R321 | R0805 | `NetR321_1` | `GND` |
| R322 | C0603 | `NetC305_1` | `NetR321_1` |
| R323 | C0603 | `NetC307_1` | `GND` |
| R324 | C0603 | `NetC308_2` | `NetR324_2` |
| R325 | R0805 | `GND` | `NetR324_2` |
| R326 | 0603_RES | `NetR326_1` | `NetF302_2` |
| R327 | 0603_RES | `NetR327_1` | `NetR326_1` |
| R328 | 0603_RES | `NetR328_1` | `NetR327_1` |
| R329 | 0603_RES | `NetR329_1` | `NetR328_1` |
| R330 | 0603_RES | `NetR330_1` | `NetR329_1` |
| R331 | 0603_RES | `NetC309_2` | `NetR330_1` |
| R332 | C0603 | `GND` | `NetC309_2` |
| R333 | R0805 | `NetR333_1` | `GND` |
| R334 | C0603 | `NetC310_1` | `NetR333_1` |
| R335 | C0603 | `NetC311_1` | `GND` |
| R336 | C0603 | `NetC312_2` | `NetR336_2` |
| R337 | R0805 | `GND` | `NetR336_2` |
| R338 | R0805 | `NetR338_1` | `GND` |
| R339 | C0603 | `NetC313_1` | `NetR338_1` |
| R400 | C0603 | `EN` | `DVCC_3v3` |
| R401 | 0603_RES | `A5` | `GND` |
| R402 | 0603_RES | `B5` | `GND` |
| R500 | C0603 | `DVCC_3v3` | `NetR500_2` |
| R501 | C0603 | `B` | `A` |
| R502 | C0603 | `NetR502_1` | `DVCC_3v3` |
| R503 | C0603 | `NetR503_1` | `DVCC_3v3` |
| R504 | C0603 | `NetR504_1` | `DVCC_3v3` |
| R505 | C0603 | `DVCC_3v3` | `NetR505_2` |
| R506 | C0603 | `DVCC_3v3` | `NetR506_2` |
| R507 | C0603 | `DVCC_3v3` | `NetR507_2` |
| SW400 | Sw_PUSH_4.5x4.5x5mm | `GND` | `EN` |
| X100 | HC-49S_L11.4-W4.7-LS12.7 | `XI` | `XO` |

### A.2 — Conectores y jacks

| Designador | Huella | Pin 1 | Pin 2 | Pin 3 | Pin 4 |
|---|---|---|---|---|---|
| 500 | H_7x1_TH_100mil | `Net500_1` | `Net500_2` | `Net500_3` | `Net500_4` |
| 501 | H_7x1_TH_100mil | — | `Net501_2` | `Net501_3` | `Net501_4` |
| J500 | CON_3x1_TH_5mm | `GND` | `B` | `A` | — |
| U301 | CONN-TH_C50126V-4P0G56 | `GND` | `NetF302_1` | `NetF301_1` | `NetF300_1` |
| U300 | HX PJ-320A-3P DIP | — (no conectado) | `NetR300_2` | `NetR302_1` | — (no conectado) |
| U302 | HX PJ-320A-3P DIP | — (no conectado) | `NetR311_2` | `NetR321_1` | — (no conectado) |
| U303 | HX PJ-320A-3P DIP | — (no conectado) | `NetR324_2` | `NetR333_1` | — (no conectado) |
| U304 | HX PJ-320A-3P DIP | — (no conectado) | `NetR336_2` | `NetR338_1` | — (no conectado) |

> Nota: 501 tiene 7 pines; la tabla muestra 1–4. Los pines 5, 6 y 7 van a `FB503` (3.3 V), `GND` y `FB502` (5 V), respectivamente. 500 tiene 7 pines; 5–7 no conectados.

## Anexo B — Causa del falso positivo SPI (C6)

El netlist y las imágenes **siempre fueron coherentes**. El error fue de interpretación en la revisión, no del esquemático.

**Netlist (extracto literal):**

```
( SPI_CLK_RN   U100-33  U101-12 )
( SPI_CS_RN    U100-34  U101-13 )
( SPI_MOSI_RN  U100-35  U101-14 )
( SPI_MISO_RN  U100-32  U101-11 )
( NetU101_5    U101-5   U401-24  U501-5 )
( NetU101_4    U101-4   U401-23 )
```

**Pinout del ISO7741:**

| Canal | Entrada (lado MCU) | Salida (lado RN) | Señal |
|---|---|---|---|
| A | `INA` (3) | `OUTA` (14) | MOSI |
| B | `INB` (4) | `OUTB` (13) | CS del RN |
| C | `INC` (5) | `OUTC` (12) | CLK |
| D | `IND` (11) | `OUTD` (6) | MISO |

**Causa del error:** al leer el netlist se intercambiaron mentalmente `U101-12` y `U101-13`. Se asignó `OUTB` (13) a CLK y `OUTC` (12) a CS, invirtiendo los canales B y C. Con eso, `NetU101_5` (que en realidad es CLK) parecía el CS del RN, y `NetU101_4` (que en realidad es CS) parecía el CLK. De ahí salió la falsa conclusión de que IO47 era el CS del RN y el CLK de la SD estaba en el net equivocado.

**Realidad:** `U101-5` (`INC`) → `U101-12` (`OUTC`) → RN SCLK; por eso `NetU101_5` con IO47 y U501-5 es el **CLK compartido**. `U101-4` (`INB`) → `U101-13` (`OUTB`) → RN SCSN; por eso `NetU101_4` con IO21 es el **CS del RN**. Los nombres `NetU101_5` y `NetU101_4` son autogenerados por Altium y no indican la señal; hay que cruzarlos con los nets `SPI_*_RN` y los puertos `SPI3_*_MCU`.

## 7. Conclusión

El diseño tiene una arquitectura conceptual correcta (dos dominios aislados, AFE RN8302B, ISO7741, ESP32-S3, RS-485 aislado, microSD, respaldo con supercaps), pero la implementación tiene **errores de conexión que impiden funcionar** y **varios puntos donde el aislamiento se anula**. Los más graves son la entrada AC flotante, el REFV/AVCC del RN, los GND del ISO7741, el VCC/GND invertido del RSM3485 y los GND comunes de las dos fuentes HLK. El bus SPI compartido RN8302B/microSD se verificó y **es correcto**.

Ninguno de estos hallazgos se corrigió automáticamente: el equipo debe decidir y ejecutar los cambios en Altium, recompilar la librería, reexportar el netlist/BOM y verificar en placa. Este informe deja el checklist completo para hacerlo.

---

*Fin del informe.*
