# REPORT v3 — Auditoría pin a pin y preparación de PCB

**Fecha:** 01/11/2026  
**Proyecto:** Analizador Trifásico IoT — Universidad Nacional de Colombia  
**Alcance:** `MAIN`, `POWER`, `THREE PHASES`, `MEASURES`, `MCU`, `INTERFACES`, netlist, BOM y preparación del layout.  
**Fuente de conectividad:** `hardware/altium/Project Outputs for Analizador_trifasico_IoT_pcb/Analizador_trifasico_IoT_pcb.NET`, generado el **01/11/2026 a las 14:28:14** (posterior a `MCU.SchDoc` de las 14:26).  
**Método:** extracción de pines y parámetros desde los `.SchDoc` (OLE2) + netlist + contraste pin a pin con los datasheets de `references/datasheets/` + auditoría independiente con subagentes por IC.  
**Limitación:** no se abrió Altium Designer. El layout no está ruteado; las condiciones de creepage, térmicas y de ruteo son checklist para el layout, no verificadas en cobre.

> Este documento reemplaza a `REPORT.md` (Revisión 2). La Revisión 2 se conserva como historial. Los identificadores `C1…` de esta revisión no son los mismos de la Rev2.

---

## 0. Veredicto rápido

**Lo que ya está corregido y verificado en el netlist de las 14:28:**

- **U401-2 (3V3 del ESP32)** ya está en `3v3_MCU`. Era la regresión crítica de la Rev3; el netlist nuevo la confirma.
- **C6 de la Rev2** (banco de desacople del RN desconectado) está resuelto: `3v3_ENER_IC` incluye C101-C105/C109/C112 y U100-9/28/40/41, con FB100 entre `AVCC_3v3` y el RN.
- **H5/H6 de la Rev2** (0.1 µF locales del ISO7741, desacople del ESP32 y microSD) están resueltos topológicamente con C112/C113 y con C400/C401/C500/C501 en los rieles correctos.
- **BOOT** ya existe (SW401 + C402), aunque C402 tiene un problema de designador/valor (ver A1).

**Lo que sigue bloqueando la fabricación:** hay **13 críticos** nuevos o abiertos. Los más importantes:

| # | Criticidad | Hallazgo | Consecuencia |
|---|---|---|---|
| C1 | 🔴 | **TXD/RXD del RSM3485PCT cruzados**: U500-3 (TXD, entrada) va a IO18/RXD; U500-4 (RXD, salida) va a IO17/TXD. | El enlace RS-485 no comunica y hay contención de salidas. |
| C2 | 🔴 | **MISO/DAT0 en contención**: U101-6 (OUTD del ISO7741) queda habilitado y maneja DAT0 de la microSD; el SDO del RN en alta impedancia no tri-statea el aislador. | Lecturas/escrituras de SD corruptas y estrés del ISO7741/SD. |
| C3 | 🔴 | **TPS2553 no es cargador**: R201=20 kΩ fija ~1.3 A; al cargar 15 F desde 0 V disipa ~6 W y entra en thermal shutdown. | El banco de supercaps no se carga de forma fiable; el *last gasp* no está garantizado. |
| C4 | 🔴 | **D200 SOD-323 a ~1.4–1.9 A**: ~0.9 W, Tj >125 °C. | El OR-ing de 5 V se sobrecalienta; riesgo de fallo. |
| C5 | 🔴 | **PS201-3 (−Vo) = AGND**: el HLK-5M03B pierde su aislamiento; el AFE queda referenciado a N. | Si N se abre o se invierte L/N, AGND, RN y jacks de CT quedan a 230 V. No es SELV. |
| C6 | 🔴 | **U301 de 250 V, sin PE ni etiquetas**: 400 V L-L entre polos adyacentes. | La bornera no está calificada; riesgo de arco/choque. |
| C7 | 🔴 | **Jacks de CT de 30 V/0.5 A, sin cortocircuito ni TVS**: burden en la placa. | Un CT abierto con corriente genera cientos de voltios y daña el RN; riesgo para el usuario. |
| C8 | 🔴 | **F300 de 200 mA/250 V/50 A** alimenta los dos HLK; los datasheets piden 1 A/250 VAC slow-blow. | Inrush o baja línea abren F300; la placa queda muerta. |
| C9 | 🔴 | **BOM CSV/XLSX del 31/10 22:59**, 133 filas, MPN equivocados y sin C112/C113/SW401/TPS2553. | El ensamblador coloca 15 pF, 165 kΩ, cristales y un SY6280 en huella WSON. |
| C10 | 🔴 | **AVCC no está respaldado**: los supercaps sostienen DVCC, no el RN. | En un corte, el MCU sigue ~8 s pero el RN se apaga de inmediato; no se leen los registros finales. |
| C11 | 🔴 | **No hay señal de power-fail**. | El MCU no sabe cuándo empieza el respaldo; puede escribir en SD cuando el riel cae. |
| C12 | 🔴 | **HLK-5M03B (ripple ≤110 mVpp) alimenta AVCC/DVCC sin LDO ni RC**; FB100 no filtra a 65 kHz. | Ripple de conmutación en el AFE; se degrada la precisión 0.5S. |
| C13 | 🔴 | **Supercaps 30 F 2.7 V con tolerancia 0 %/+30 % y balanceo 1 kΩ**: a 4.6–4.9 V una celda puede llegar a 2.59–2.76 V. | Sobretensión y vida reducida; riesgo de fallo del banco. |

**Altos:** C402 es una resistencia de 10 kΩ con designador de capacitor y Comment de 1 µF; el EN del ESP32 perdió el 1 µF; R401/R402 tienen Comment de 10 Ω; VBUS sin PTC; header 200 es un jumper sin GND; 3P4W solamente; ambos HLK en L1; 165 kΩ 0603 de 75 V; MOV después del fusible; sin filtro EMI; faltan 100–220 µF en las salidas de los HLK; UVLO del AP63203; U100-21 flotante; RC a AGND; INTN1/RSTN sin GPIO; VCC2 del ISO en el riel del RN; falta 100 nF en 3v3_RS485; R501 permanente; J500 con orden distinto al datasheet; 501-5 y 501-7 alimentados a la vez; el FGH100M no está en el esquemático; falta serie/ESD en SD; falta ESD en CC/SBU; D201 marginal; C207 electrolítico; sin protección de tensión inversa en supercaps; huellas `3`, `R0805`, `- duplicate`; IntLib ausente; sin test points.

---

## 1. Qué cambió desde la Revisión 2

### 1.1 Corregido y verificado

| Hallazgo Rev2 | Estado | Evidencia en el netlist 14:28 |
|---|---|---|
| **C6** — banco del RN desconectado por FB100 | ✅ Resuelto | `3v3_ENER_IC` = C101-C105, C109, C112, FB100-1, R100/R102/R103/R104, U100-9/28/40/41, U101-16. |
| **H5** — falta 0.1 µF en VCC1/VCC2 del ISO7741 | ✅ Resuelto | C113 en `3v3_MCU`; C112 en `3v3_ENER_IC`. |
| **H6** — desacople del ESP32/microSD del lado equivocado | ✅ Resuelto | C400/C401 en `3v3_MCU`; C500/C501 en `3v3_SD`; U401-2 ya en `3v3_MCU`. |
| **M8** — sin botón BOOT | ✅ Resuelto | SW401 + C402 en `BOOT` (IO0). |
| **U401-2 flotante** (regresión Rev3) | ✅ Resuelto | `3v3_MCU` incluye U401-2 desde el netlist 14:28. |

### 1.2 Abierto o agravado

| Hallazgo Rev2 | Estado | Comentario |
|---|---|---|
| **C1** — AGND=N / HLK-5M03B sin aislamiento | 🔴 Abierto | PS201-1 y PS201-3 siguen en AGND. |
| **C2** — CT por jack 3.5 mm, sin TVS | 🔴 Abierto | U300-U304 sin cambios. |
| **C3** — 3P4W solamente | 🔴 Abierto | README sigue prometiendo 3P3W. |
| **C4** — U301 de 250 V, sin PE | 🔴 Abierto | U301 y BOM sin cambios. |
| **C5** — F300 de 200 mA | 🔴 Abierto | F300-F302 siguen siendo JFC2410-0200TS. |
| **C7** — SY6280 como cargador | 🔴 Agravado | Ahora TPS2553 con R201=20 kΩ; más corriente y ~6 W. |
| **C8** — BOM viejo | 🔴 Abierto | CSV/XLSX del 31/10. |
| **H1** — D200/D201/D202 térmicos | 🔴 Abierto | MS2A40LWS SOD-323. |
| **H2** — energía real del respaldo | ⚠️ Parcial | El cálculo correcto es ~26 J útiles, ~8 s a 3.2 W; el README dice 9 s. |
| **H4** — ambos HLK en L1 | 🔴 Abierto | PS200-1 y PS201-2 en `NetF300_2`. |

### 1.3 Nuevos hallazgos de esta revisión

- **C1**: TXD/RXD del RSM3485PCT cruzados (la Rev2 los dio por correctos).
- **C2**: contención MISO/DAT0 por el OUTD del ISO7741 (la Rev2 dio el SPI compartido por seguro).
- **C10/C11**: AVCC sin respaldo y sin power-fail.
- **C12**: ripple del HLK-5M03B en AVCC/DVCC.
- **C13**: sobretensión de supercaps por tolerancia.
- **A1**: C402 es una resistencia de 10 kΩ con designador de capacitor.
- **A2**: el EN del ESP32 perdió el 1 µF.
- **A3**: R401/R402 con Comment de 10 Ω.
- **A4**: VBUS sin PTC ni desacople.
- **A5**: header 200 es un jumper, no una entrada.
- **A6**: 501-5 y 501-7 alimentados a la vez; 501-7 es ~4.6 V, no 5 V.
- **A7**: el pinout del jack HX no es verificable con el datasheet.
- **A8**: el FGH100M no está en el esquemático; headers provisionales.

---

## 2. Metodología, conteo y limitaciones

### 2.1 Fuentes

1. Netlist Protel del **01/11/2026 14:28:14** (12 647 bytes).
2. Registros `RECORD=1/2/34/41` de los `.SchDoc` para designador, `LibReference`, pines, nombres y parámetros.
3. Datasheets de `references/datasheets/`, en particular:
   - `RN8302B_Datasheet_v3.pdf` y `RN8302B_User_Manual_v1.1.pdf`.
   - `ESP32-S3-WROOM_Module.pdf` y `ESP32-S3_Datasheet_en.pdf`.
   - `ISO7741DWR_Datasheet.pdf`.
   - `RSM3485PCT_Datasheet.pdf`.
   - `HLK-10M05_Datasheet.pdf` y `HLK-5M03B_Datasheet.pdf`.
   - `AP63203WU-7_Datasheet.pdf`, `TI TPS2553DRVR.pdf`, `MS2A40LWS_Datasheet.pdf`.
   - `USBLC6-2SC6_Datasheet.pdf`, `SM712_Datasheet.pdf`, `TF-CARD-9P_Datasheet.pdf`.
   - `JFC2410-0200TS_Datasheet.pdf`, `MOV-14D471K_Datasheet.pdf`, `Supercapacitor_Datasheet.pdf`.
4. Auditoría independiente con subagentes por IC (RN8302B, ESP32-S3, TPS2553/AP63203, ISO7741/RSM3485, HLK/entrada AC, microSD/BOM) y una auditoría cruzada de todas las redes.

### 2.2 Conteo del netlist actual

| Métrica | Valor |
|---|---:|
| Componentes | **144** |
| Redes | **104** |
| Pines con red | **405** |
| Pines sin red | **39** |
| Redes de un solo pin | **0** |
| Redes sin ningún IC (solo pasivos) | 23 (divisores, CT, supercaps, headers) |

### 2.3 Los 39 pines sin red

| Componente | Pines sin red | Clasificación |
|---|---|---|
| `U100` RN8302B | 1, 2, 30, 44 | `NC` del datasheet; flotar es correcto. |
| `U100` | **21** | `NC` que el datasheet V3 pide **conectar a AGND**. → **A9** |
| `U100` | 22-26 | `CF5…CF1`; no se usan. Correcto. |
| `U200` | 3 | `FAULT#` open-drain; puede quedar flotante, pero se pierde telemetría. → **M1** |
| `U401` | 4, 8, 12, 28-30, 32-35, 38, 39 | GPIO libres. Correcto. |
| `U401` | 15, 16, 26 | Strapping IO3/IO46/IO45; defaults internos. → **M2** |
| `U401` | 36, 37 | RXD0/TXD0; no traídos a header. → **M3** |
| `U300/U302/U303/U304` | 4 | Sleeve/switch del jack; verificar pinout. → **A7** |
| `U500` | 7 | `VO` (salida aislada 5 V) no usada; flotante es correcto. |
| `j400` USB-C | A8, B8 | SBU1/SBU2; no usados. Correcto. |
| `500` | 5, 6, 7 | Sin conectar; documentar. |
| `501` | 1 | Sin conectar; documentar. |

**Conclusión:** no hay pines de alimentación flotantes. Los únicos que requieren acción son **U100-21** (AGND), **U401-15/16/26** (pulls externos recomendados) y **U200-3** (pull-up/test point si se quiere telemetría).

### 2.4 Limitaciones

- No se abrió Altium; la conectividad es la del netlist exportado. Si el netlist no se reexporta después de un cambio, este informe queda desactualizado.
- El layout no está ruteado; no se puede verificar creepage, térmica real, ni el keepout de antena en cobre.
- El modelo de CT/Rogowski sigue sin definirse; sin relación, clase y saturación no se puede cerrar el burden.
- No se midió ningún prototipo; los cálculos son analíticos.

---

## 3. Auditoría pin a pin por IC

> Las tablas completas de pines y redes están en `documentation/revision_v3/diagramas/S8_NETINDEX.svg` y en las hojas de footprint `S2_MEASURES_FP`, `S3_POWER_FP`, `S4_MCU_FP`, `S5_INTERFACES_FP`. Aquí se resumen los veredictos.

### 3.1 U100 — RN8302B V3 (LQFP-44)

| Pin | Nombre | Red | Veredicto |
|---:|---|---|---|
| 1, 2 | NC | — | ✅ |
| 3 | REFV | `REF` (C110 10 µF + C111 100 nF) | ⚠️ 10 µF vs 1 µF (M4) |
| 4-5 | IAP/IAN | `NetC300_2` / `NetC301_1` | ✅ topología; ver CT (C7/A10) |
| 6 | AGND | `AGND` | ✅ |
| 7-8 | IBP/IBN | `NetC304_2` / `NetC305_1` | ✅ |
| 9 | AVCC | `3v3_ENER_IC` | ✅ (C101-C112) |
| 10-11 | ICP/ICN | `NetC308_2` / `NetC310_1` | ✅ |
| 12-17 | VAP…VCN | `NetC302_2`…`NetC311_1` | ✅ (3P4W) |
| 18-19 | INP/INN | `NetC312_2` / `NetC313_1` | ✅ |
| 20 | RA | `AGND` | ✅ |
| 21 | NC | — | ❌ **debe ir a AGND** (A9) |
| 22-26 | CF5…CF1 | — | ✅ no usadas |
| 27 | RSTN | `NetR103_1` (R103 1 kΩ) | ✅ |
| 28 | DVCC | `3v3_ENER_IC` | ✅ |
| 29 | DGND | `AGND` | ⚠️ misma red; estrella (M5) |
| 30 | NC | — | ✅ |
| 31 | INTN1 | `NetR102_2` (R102 10 kΩ) | ⚠️ no llega al ESP32 (A11) |
| 32 | SDO | `SPI_MISO_RN` → U101-11 | ✅ |
| 33 | SCLK | `SPI_CLK_RN` → U101-12 | ✅ |
| 34 | SCSN | `SPI_CS_RN` → U101-13 + R104 | ✅ |
| 35 | SDI | `SPI_MOSI_RN` → U101-14 | ✅ |
| 36-37 | XO/XI | X100 + C108/C100 | ✅ |
| 38 | VO | C106 10 µF + C107 100 nF | ✅/⚠️ 10 µF vs 4.7 µF |
| 39 | DGND | `AGND` | ⚠️ misma red |
| 40 | DVCC | `3v3_ENER_IC` | ✅ |
| 41 | RB | `3v3_ENER_IC` | ✅ (DVCC permitido) |
| 42 | PM | `AGND` | ✅ (EMM) |
| 43 | RC | `AGND` | ⚠️ datasheet pide DGND (M5) |
| 44 | NC | — | ✅ |

**Conclusión RN8302B:** pinout funcional correcto salvo **pin 21**. El banco de desacople está bien conectado. La referencia, AVCC, DVCC, VO, RSTN, RB y PM están correctos. El cristal no necesita 10 MΩ externo.

### 3.2 U101 — ISO7741DWR (SOIC-16)

| Pin | Nombre | Red | Veredicto |
|---:|---|---|---|
| 1 | VCC1 | `3v3_MCU` + C113 | ✅ |
| 2, 8 | GND1 | `DGND` | ✅ |
| 3 | INA | `NetR502_1` (MOSI) | ✅ |
| 4 | INB | `NetU101_4` (CS RN) | ✅ |
| 5 | INC | `NetU101_5` (CLK) | ✅ |
| 6 | OUTD | `NetR505_2` (MISO/DAT0) | 🔴 **contención** (C2) |
| 7 | EN1 | `NetR101_1` (10 kΩ a 3v3_MCU) | ⚠️ siempre habilitado (C2) |
| 9, 15 | GND2 | `AGND` | ✅ |
| 10 | EN2 | `NetR100_1` (10 kΩ a 3v3_ENER_IC) | ✅ |
| 11 | IND | `SPI_MISO_RN` (RN SDO) | ✅ |
| 12 | OUTC | `SPI_CLK_RN` | ✅ |
| 13 | OUTB | `SPI_CS_RN` | ✅ |
| 14 | OUTA | `SPI_MOSI_RN` | ✅ |
| 16 | VCC2 | `3v3_ENER_IC` + C112 | ✅/⚠️ comparte riel con RN (M6) |

**Conclusión ISO7741:** direcciones y mapa A/B/C/D correctos. El problema no es el pinout: es que **EN1 está fijo en alto** y el OUTD no se tri-statea cuando la microSD usa DAT0.

### 3.3 U200 — TPS2553DRVR (WSON-6 + EP)

| Pin | Nombre | Red | Veredicto |
|---:|---|---|---|
| 1 | OUT | `NetC201_1` | ✅ |
| 2 | ILIM | `NetR201_2` (R201 20 kΩ) | ✅ pinout; ⚠️ fija ~1.3 A (C3) |
| 3 | FAULT | — | ⚠️ flotante; agregar pull-up/test point (M1) |
| 4 | EN | `Vin_buck_5V` | ✅ |
| 5 | GND | `DGND` | ✅ |
| 6 | IN | `Vin_buck_5V` | ✅ |
| 7 | PAD | `DGND` | ✅ (soldar al plano con vías) |

**Conclusión TPS2553:** pinout correcto. El problema es la arquitectura: **no es un cargador**. Con R201=20 kΩ, IOS ≈ 1.2–1.4 A y la disipación inicial es ~6 W; el WSON (θJA 72 °C/W) entra en thermal shutdown a 135 °C.

### 3.4 U201 — AP63203WU-7 (TSOT-26)

| Pin | Nombre | Red | Veredicto |
|---:|---|---|---|
| 1 | FB | `DVCC_3v3` | ✅ |
| 2 | EN | `NetC207_1` | ✅/⚠️ EN=VIN, UVLO ~3.1 V (A12) |
| 3 | VIN | `NetC207_1` | ✅ |
| 4 | GND | `DGND` | ✅ |
| 5 | SW | `NetC204_1` | ✅ |
| 6 | BST | `NetC204_2` | ✅ |

**Conclusión AP63203:** pinout y pasivos correctos (L200 3.9 µH, C204 100 nF, C205/C206 22 µF). Falta UVLO programado y power-fail.

### 3.5 U400 — USBLC6-2SC6 (SOT-23-6)

| Pin | Nombre | Red | Veredicto |
|---:|---|---|---|
| 1 | I/O1 | `Netj400_A6` (D+) | ✅ |
| 2 | GND | `DGND` | ✅ |
| 3 | I/O2 | `Netj400_A7` (D−) | ✅ |
| 4 | I/O2 | `DN_USB` | ✅ |
| 5 | VBUS | `5V_USB` | ⚠️ sin PTC/desacople (A4) |
| 6 | I/O1 | `DP_USB` | ✅ |

**Conclusión USBLC6:** canales y polaridad correctos.

### 3.6 U401 — ESP32-S3-WROOM-1-N4 (41 pines)

| Pin | Nombre | Red | Veredicto |
|---:|---|---|---|
| 1, 40, 41 | GND | `DGND` | ✅ |
| **2** | **3V3** | **`3v3_MCU`** | ✅ **corregido en netlist 14:28** |
| 3 | EN | `EN` (R400/C403/SW400) | ⚠️ RC 1 ms vs 1 µF recomendado (A2) |
| 4, 8, 12, 28-30, 32-35, 38, 39 | GPIO libres | — | ✅ |
| 5-7 | IO5/IO6/IO7 | `Net500_1..3` | ✅ |
| 9 | IO16 | `NetR500_2` (CON RS485) | ✅ |
| 10 | IO17 | `NetU401_10` | 🔴 **TXD del ESP32 va a RXD del RSM** (C1) |
| 11 | IO18 | `NetU401_11` | 🔴 **RXD del ESP32 va a TXD del RSM** (C1) |
| 13-14 | IO19/IO20 | `DN_USB`/`DP_USB` | ✅ |
| 15 | IO3 | — | ⚠️ strapping JTAG flotante (M2) |
| 16 | IO46 | — | ⚠️ pull-down interno; agregar 10 kΩ (M2) |
| 17 | IO9 | `NetR507_2` | ✅ |
| 18 | IO10 | `Net500_4` | ✅ |
| 19-21 | IO11/IO12/IO13 | `Net501_4/2/3` | ✅ |
| 22 | IO14 | `NetR502_1` (MOSI) | ✅ |
| 23 | IO21 | `NetU101_4` (CS RN) | ✅ |
| 24 | IO47 | `NetU101_5` (CLK) | ✅ |
| 25 | IO48 | `NetR505_2` (MISO) | 🔴 **contención** (C2) |
| 26 | IO45 | — | ⚠️ strapping VDD_SPI; pull-down interno (M2) |
| 27 | IO0 | `BOOT` | ✅/⚠️ C402 mal anotado (A1) |
| 31 | IO38 | `NetR503_1` (CS SD) | ✅ |
| 36-37 | RXD0/TXD0 | — | ⚠️ sin test points (M3) |

**Conclusión ESP32:** alimentación corregida. El resto del conexionado es correcto salvo el cruce UART, el RC de EN, los strapping sin pulls externos y C402.

### 3.7 U500 — RSM3485PCT (módulo de 10 pines; el símbolo tiene 9)

| Pin | Nombre | Red | Veredicto |
|---:|---|---|---|
| 1 | VCC | `3v3_RS485` (C502 10 µF) | ⚠️ falta 0.1 µF (A13) |
| 2 | GND | `DGND` | ✅ |
| 3 | TXD (entrada) | `NetU401_11` = IO18/RXD | 🔴 **cruzado** (C1) |
| 4 | RXD (salida) | `NetU401_10` = IO17/TXD | 🔴 **cruzado** (C1) |
| 5 | CON | `NetR500_2` (R500 10 kΩ + IO16) | ✅ reposo = RX |
| 6 | — | no existe | ✅ símbolo de 9 pines correcto |
| 7 | VO | — | ✅ flotante permitido |
| 8 | B | `B` (D500-2, J500-2, R501-1) | ✅ |
| 9 | A | `A` (D500-1, J500-3, R501-2) | ✅ |
| 10 | RGND | `RGND` (D500-3, J500-1) | ✅ aislada |

**Conclusión RSM3485:** pinout correcto, pero **TXD/RXD están cruzados** según la asignación documentada IO17=TXD, IO18=RXD. El datasheet (fig. 4, p. 4) dibuja MCU-TXD → pin 3 y MCU-RXD → pin 4, sin cruce.

### 3.8 U501 — microSD TF-CARD-9P

| Pin | Nombre | Red | Veredicto |
|---:|---|---|---|
| 1 | DAT2 | `NetR504_1` (R504 10 kΩ) | ✅ |
| 2 | CD/DAT3 | `NetR503_1` (R503 10 kΩ + IO38) | ✅ CS con pull-up |
| 3 | CMD | `NetR502_1` (R502 10 kΩ + IO14) | ✅ |
| 4 | VDD | `3v3_SD` (C500 10 µF + C501 100 nF) | ✅ lado conector |
| 5 | CLX/CLK | `NetU101_5` (IO47 + ISO INC) | ✅ (nombre `CLX` cosmético) |
| 6 | VSS | `DGND` | ✅ |
| 7 | DAT0 | `NetR505_2` (R505 10 kΩ + IO48 + ISO OUTD) | 🔴 **contención** (C2) |
| 8 | DAT1 | `NetR506_2` (R506 10 kΩ) | ✅ |
| 9 | CD | `NetR507_2` (R507 10 kΩ + IO9) | ✅ |
| 10 | GND/shell | `DGND` | ✅ |

**Conclusión microSD:** pinout y pull-ups correctos. El problema es el MISO compartido con el ISO7741. Faltan serie/ESD en CLK/CMD/DAT0.

### 3.9 PS200 / PS201 — HLK-10M05 / HLK-5M03B

| Pin | Nombre | Red | Veredicto |
|---:|---|---|---|
| PS200-1 | AC1 | `NetF300_2` (L1) | ✅ si U301-4=L1 |
| PS200-2 | AC2 | `AGND` (N) | ✅ N; comparte ground con AFE |
| PS200-3 | −VO | `DGND` | ✅ salida aislada |
| PS200-4 | +VO | `Vout_5V` | ⚠️ falta 100–220 µF en el pin (A14) |
| PS201-1 | AC | `AGND` (N) | ⚠️ N |
| PS201-2 | AC | `NetF300_2` (L1) | ✅ L1 |
| PS201-3 | −VO | `AGND` (N) | 🔴 **anula el aislamiento** (C5) |
| PS201-4 | +VO | `AVCC_3v3` | ⚠️ C203 4.7 µF; falta 10 µF + 0.1 µF (A14) |

**Conclusión HLK:** pinout correcto. El HLK-5M03B **es aislado**, pero su pin 3 (−Vo) está en AGND, igual que su pin 1 (AC); eso anula la barrera. El HLK-10M05 sí mantiene la barrera SELV.

### 3.10 U301 — bornera 1×4P

| Pin | Red | Veredicto |
|---:|---|---|
| 1 | `AGND` (N) | ⚠️ sin etiqueta/keying |
| 2 | `NetF302_1` (L3) | 🔴 400 V respecto a 3 |
| 3 | `NetF301_1` (L2) | 🔴 400 V respecto a 2/4 |
| 4 | `NetF300_1` (L1) | ✅ L1 |

**Conclusión U301:** es una bornera de 250 V, no un puente rectificador. No hay PE ni etiquetas N/L1/L2/L3. Cambiar a 600 V, agregar PE y keying.

---

## 4. Hallazgos críticos

### C1 — TXD/RXD del RSM3485PCT cruzados

**Evidencia:** `U500-3` (TXD) = `NetU401_11` = U401-11 = **IO18/RXD**; `U500-4` (RXD) = `NetU401_10` = U401-10 = **IO17/TXD**. El datasheet del RSM3485PCT (fig. 4, p. 4) muestra MCU-TXD → pin 3 y MCU-RXD → pin 4, sin cruce. La tabla §6.2 confirma que TXD es entrada (VIH/VIL, pull-up 10 kΩ) y RXD es salida (VOH/VOL con IRXD=4 mA).

**Consecuencia:** el TXD del módulo queda en una entrada (nunca recibe, se queda en mark por el pull-up) y el RXD (salida) pelea contra el TX del ESP32. El enlace RS-485 no comunica y hay contención.

**Corrección:** `U500-3` ← IO17 (TX) y `U500-4` → IO18 (RX). Etiquetar las redes `U1TXD`/`U1RXD` y verificar en el símbolo que TXD/RXD no estén invertidos.

### C2 — MISO/DAT0 en contención

**Evidencia:** `NetR505_2` = `R505-2`, `U101-6` (OUTD), `U401-25` (IO48), `U501-7` (DAT0). El RN8302B deja SDO en alta impedancia cuando SCSN=1 (datasheet V3, p. 13). El ISO7741 sin sufijo F tiene **salida por defecto alta** cuando INx queda abierto (tabla 2, p. 27) y EN1 está fijo en alto por R101. Por tanto, OUTD sigue manejando DAT0 en alto aunque el RN esté deseleccionado.

**Consecuencia:** cuando la microSD transmite, DAT0 y OUTD compiten en push-pull. Lecturas/escrituras corruptas, corriente de conflicto de 20–30 mA (por encima del absoluto ±15 mA del ISO7741) y estrés de ambos.

**Corrección:** una de:
- Bus SPI dedicado para la microSD (el ESP32-S3 tiene controladores de sobra).
- Tri-state de OUTD gobernado por el CS del RN (EN1 a GPIO; pull-down en SDI del RN).
- Buffer 74LVC1G125 habilitado por CS_SD.
No basta con el argumento “el SDO del RN es alta impedancia”.

### C3 — El TPS2553 no es un cargador de supercaps

**Evidencia:** U200-1=OUT, U200-2=ILIM (R201=20 kΩ), U200-4=EN, U200-6=IN, U200-5/7=GND/EP. Datasheet TPS2553, p. 15: `IOSnom(mA) = 23950 / R_ILIM^0.977`; con 20 kΩ → **1.28 A** (rango 1.20–1.38 A). θJA WSON = 72 °C/W; thermal shutdown 135 °C. Al cargar 15 F desde 0 V: `P = (4.6 − 0) × 1.295 ≈ 5.96 W`; `ΔT ≈ 429 °C`; el dispositivo cicla térmicamente.

**Consecuencia:** la carga de 15 F no es fiable; el banco puede tardar minutos u horas en alcanzar la tensión de respaldo. El *last gasp* no está garantizado. Además, 1.3 A de carga + ~0.6 A del buck + 0.3–0.5 A del header 501-7 supera los 2 A del HLK-10M05.

**Corrección:** usar un cargador de supercaps dedicado (CC/CV con foldback), o una resistencia/inductor serie que reparta la disipación, o bajar ILIM a 100–200 mA (`R_ILIM ≥ 100 kΩ`) y aceptar una carga lenta. No aumentar R201 “para que cargue más rápido”: el problema es la disipación.

### C4 — D200 en SOD-323 a ~1.4–1.9 A

**Evidencia:** D200-2=`Vout_5V`, D200-1=`Vin_buck_5V`; MS2A40LWS, IF(AV)=2 A, Vf≈0.50 V a 2 A, TJmax=125 °C, SOD-323. A 1.4–1.9 A: P≈0.7–0.95 W; θJA típica 250–300 °C/W → Tj≈200–325 °C.

**Consecuencia:** D200 se sobrecalienta; el OR-ing de 5 V puede fallar. D201 es marginal a 0.8 A; D202 es aceptable a 0.5 A.

**Corrección:** SMA/SMB de 3 A (o ideal diode/PMOS) para D200/D201; verificar θJA y cobre de enfriamiento. Un ideal diode en D201 además recupera ~0.35 V y aumenta la energía útil del respaldo.

### C5 — PS201-3 = AGND: el HLK-5M03B pierde su aislamiento

**Evidencia:** `AGND` incluye `PS201-1` (AC) y `PS201-3` (−Vo); `NetF300_2` incluye `PS201-2` (AC). El HLK-5M03B es un módulo aislado de 2500–3000 VAC, pero al unir su entrada AC con su salida negativa, la barrera deja de existir. El AFE (RN8302B, divisores, jacks de CT) queda referenciado a N.

**Consecuencia:** si el neutro se abre o se invierte con la fase, AGND, el RN y los jacks de CT quedan a 230 V. No es SELV. El dominio digital solo queda separado por PS200 + ISO7741.

**Corrección:** elegir una arquitectura:
- **A) Aceptar AFE referenciado a neutro (3P4W):** bornera de 600 V con PE y etiquetas, jacks de CT seguros, gabinete Clase I/II, creepage de 400 V. Es la opción que mantiene la medición fase-neutro.
- **B) Aislar el AFE:** divisores diferenciales/aislados y fuente 3.3 V aislada dedicada. Más complejo y costoso.
- **C) Fuente trifásica aislada:** alimentar los HLK desde una fuente auxiliar aislada.
No basta con quitar `PS201-3=AGND`: el RN necesita AVCC referida a AGND=N.

### C6 — U301 de 250 V, sin PE ni etiquetas

**Evidencia:** BOM: `C50126V-4P0G56`, 1×4P, 10 A, **250 V**. Netlist: U301-1=AGND (N), U301-2=NetF302_1 (L3), U301-3=NetF301_1 (L2), U301-4=NetF300_1 (L1). Entre polos adyacentes hay 400 V L-L. No hay net de PE.

**Consecuencia:** la bornera puede no soportar 400 V entre polos; sin PE no hay tierra de protección; sin etiquetas/keying, invertir N/L deja AGND vivo.

**Corrección:** bornera de **600 V** (o 5 pines con PE), etiquetas N/L1/L2/L3/PE, keying, borne de PE al gabinete. Declarar Clase I o Clase II. Verificar creepage/clearance de 400 V.

### C7 — Jacks de CT inadecuados y sin protección

**Evidencia:** U300/U302/U303/U304 = HX PJ-320A-3P, **30 V/0.5 A**; pines 2/3 al CT; pin 4 sin conectar; burden R301+R302 en la placa; no hay TVS en `NetC300_2`/`NetC301_1`/etc. El RN tiene absoluto máximo ±2 V y rango 830 mVp.

**Consecuencia:** al desconectar un CT con corriente, el secundario queda abierto y puede generar cientos de voltios. El jack de 30 V y el RN de 2 V no están protegidos. El jack de audio no es un conector de CT.

**Corrección:** bornera de CT con cortocircuito (shorting link) o jack con contacto NC que cortocircuite al desenchufar; burden en el conector; BAT54S/TVS en cada entrada del RN; etiquetar polaridad y “no desconectar con corriente”.

### C8 — F300 de 200 mA/250 V/50 A

**Evidencia:** F300 = JFC2410-0200TS, 200 mA, 250 V, I²t 0.0682 A²s, interrupting 50 A @ 250 V. Alimenta PS200-1 + PS201-2 + R303 + RV300. Los datasheets de los HLK recomiendan **1 A/250 VAC slow-blow** (o 10 Ω wirewound); inrush ≤10 A por módulo.

**Consecuencia:** a 85 V y plena carga, la suma puede superar 200 mA; el inrush de ambos puede abrir F300. La placa queda muerta aunque L2/L3 estén presentes. La tensión de 250 V y la ruptura de 50 A son insuficientes para 230/400 V.

**Corrección:** **1 A/250 VAC slow-blow por HLK** o 1.5–2 A para ambos, con tensión ≥500 V y capacidad de ruptura ≥1.5 kA (o un MCB aguas arriba). Separar el fusible del divisor de fase A. Coordinar con el MOV.

### C9 — BOM CSV/XLSX viejo

**Evidencia:** `Analizador_trifasico_IoT_pcb.csv` y `.xlsx` son del **31/10/2026 22:59**; el `.BomDoc` es del 01/11/2026 13:54. El CSV tiene 133 filas; el netlist actual tiene 144 componentes. Faltan C112, C113, SW401, R104, R505-R507, C109-C111; U200 sigue como SY6280AAC (SOT-23-5). MPN incorrectos: 100 nF → 15 pF, 10 µF → 165 kΩ, 22 µF → cristal.

**Consecuencia:** el ensamblador coloca componentes equivocados y un SY6280 en huella WSON-6. La placa no funciona.

**Corrección:** recompilar y reexportar CSV/XLSX desde el `.BomDoc` actual; verificar las 144 líneas contra el esquemático; borrar el ítem duplicado `RES_10kohms` del `.BomDoc`; no enviar el CSV del 31/10.

### C10 — AVCC no está respaldado

**Evidencia:** PS201-4 → C203 → FB100 → `3v3_ENER_IC` → U100-9/28/40. Los supercaps C201/C202 respaldan `Vin_buck_5V` → `DVCC_3v3` (MCU/SD/RS485), no `AVCC_3v3`. U100-31 (INTN1) no llega al ESP32.

**Consecuencia:** en un corte, el MCU sigue ~8 s pero el RN se apaga de inmediato; no se pueden leer los registros de energía finales. El “last gasp” queda incompleto.

**Corrección:** respaldar AVCC desde el banco (OR-ing + LDO 3.3 V) o leer el RN continuamente y guardar ante una señal de power-fail. Llevar INTN1 por un canal aislado o usar la detección de sag del RN.

### C11 — No hay señal de power-fail

**Evidencia:** no hay comparador, ADC ni GPIO monitoreando `Vin_buck_5V`/`Vout_5V`. U200-3 (FAULT) está flotante; U201 no tiene PGOOD.

**Consecuencia:** el MCU no sabe cuándo empieza el respaldo; puede escribir en la SD cuando el riel cae. El *last gasp* no se puede coordinar.

**Corrección:** divisor 10 kΩ/10 kΩ de `Vin_buck_5V` a un ADC (IO4/ADC1) con 100 nF; umbral de firmware ~4.2 V. Alternativa: comparador con referencia de 1.2 V. El FAULT de U200 puede dar un aviso secundario, pero también se activa por overcurrent/overtemp.

### C12 — Ripple del HLK-5M03B en AVCC/DVCC

**Evidencia:** PS201-4 → C203 4.7 µF → FB100 → `3v3_ENER_IC` → U100-9/28/40. El HLK-5M03B tiene ripple ≤110 mVpp (con 10 µF + 0.1 µF); el RN pide 4.7 µF + 0.1 µF en AVCC/DVCC. El ferrite 0603 tiene impedancia despreciable a 65 kHz.

**Consecuencia:** el ripple de conmutación llega al AFE y puede modular ADC/referencia; se degrada la precisión 0.5S.

**Corrección:** LDO de baja ruido (p. ej. TPS7A2033) o RC 10 Ω + 10 µF tras PS201-4; agregar 10 µF cerámico + 100 nF en PS201-4; FB100 solo para HF; medir ripple en U100-9.

### C13 — Sobretensión de supercaps

**Evidencia:** C201/C202 = 30 F, 2.7 V, tolerancia 0 %/+30 %; R200/R202 = 1 kΩ; Vcharge ≈ 4.6 V. Peor caso 30 F/39 F: a 4.6 V una celda llega a **2.59 V**; a 4.8 V a **2.70 V**; a 4.9 V a **2.76 V**. El balanceo 1 kΩ tiene τ≈8.3 h y no corrige durante los ~53 s de carga.

**Consecuencia:** sobretensión y vida reducida; riesgo de fallo del banco.

**Corrección:** balanceo activo, o limitar Vcharge ≤4.5 V, o caps con tolerancia más estrecha; agregar clamp/TVS de 5.1 V y Schottky antiparalelo por celda.

---

## 5. Hallazgos altos

| ID | Hallazgo | Evidencia | Corrección |
|---|---|---|---|
| A1 | **C402 es una resistencia de 10 kΩ con designador de capacitor.** | `LibReference=RES_10kohms`, `Value=10kΩ`, `MPN=1RC0603F1002`, `Comment=CL10B105` (1 µF), `Designator=C402`; `BOOT` = C402-1, SW401-2, U401-27. | Renombrar a **R403**, corregir Value/Comment/MPN; reservar C402 para el 1 µF de EN. |
| A2 | **EN del ESP32 perdió el 1 µF.** | `EN` = C403 100 nF + R400 10 kΩ + SW400; el datasheet del módulo recomienda 10 kΩ + 1 µF; el AP63203 tarda ~4 ms en subir. | Agregar C404 1 µF de EN a DGND (o devolver C402 a EN). |
| A3 | **R401/R402 con Comment de 10 Ω.** | `Value=5.1k`, `MPN=HRC0603F5111ENTN`, `Comment=UNI-ROYAL HP05W3F100JT5E` (10 Ω, 5 W). | Corregir Comment al MPN de 5.11 kΩ; verificar el BOM. |
| A4 | **VBUS sin PTC ni desacople.** | `5V_USB` = 200-1, j400-A4/B9, j400-B4/A9, U400-5; no hay capacitor. | PTC 0.75–1 A en VBUS; 100 nF + 10 µF a DGND junto al conector. |
| A5 | **Header 200 es un jumper, no una entrada.** | 200-1=`5V_USB`; 200-2=`Net200_2`→D202; no hay GND. | Documentar; usar header de 3 pines o entrada de 5 V dedicada con PTC. |
| A6 | **3P4W solamente.** | Divisores single-ended a AGND/N; HLK L-N; MOV L-N; README promete 3P3W. | Documentar 3P4W solamente o rediseñar para 3P3W. |
| A7 | **Ambos HLK en L1.** | PS200-1 y PS201-2 en `NetF300_2`. | Alimentar desde al menos dos fases o agregar detector de pérdida de fase. |
| A8 | **165 kΩ 0603 de 75 V con MOV que clampa a 775 V.** | R303-R331; 775 V/6 ≈ 129 V por resistor. | Usar 0805/1206 o 8–10 en serie; coordinar MOV/fusible. |
| A9 | **U100-21 (NC) flotante.** | Datasheet V3: NC debe ir a AGND. | Conectar a AGND. |
| A10 | **Burden/CT indefinido.** | 20 Ω burden; RN 830 mVp; CT no definido. | Definir CT; 100 A/20 mA da 566 mVp (OK); 100 A/40 mA da 1.13 Vp (excede). |
| A11 | **INTN1/RSTN no llegan al ESP32.** | U100-31 solo R102 10 kΩ; U100-27 solo R103 1 kΩ. | Llevar INTN1 por canal aislado o documentar polling. |
| A12 | **UVLO del AP63203 ~3.1 V.** | U201-2=U201-3=`NetC207_1`; datasheet p. 11. | Divisor en EN para VOFF≈3.8 V o apagado por power-fail. |
| A13 | **Falta 100 nF en 3v3_RS485.** | `3v3_RS485` = C502 10 µF, FB500-1, R500-1, U500-1; C501 está en 3v3_SD. | Agregar C503 100 nF de U500-1 a DGND. |
| A14 | **Faltan 100–220 µF en las salidas de los HLK.** | PS200-4=`Vout_5V`; C200 10 µF está después de D200. PS201-4=`AVCC_3v3`; C203 4.7 µF. | Agregar 100–220 µF + 0.1 µF en cada salida, cerca del pin. |
| A15 | **R501 120 Ω permanente y bias marginal.** | RSM trae 22 kΩ internos; idle ~9 mV; umbral ≥−10 mV. | Hacer R501 seleccionable; agregar bias externo si el bus es largo. |
| A16 | **J500 no sigue el orden del datasheet.** | J500: 1=RGND, 2=B, 3=A; datasheet fig. 5: 1=B, 2=A, 3=shield. | Rotular A/B/RGND en silkscreen; agregar shield/PE. |
| A17 | **501-5 (3V3) y 501-7 (5V) alimentados a la vez.** | 501-5←FB503←DVCC; 501-7←FB502←Vin_buck_5V. | Alimentar solo por uno; dejar el otro NC o como salida. |
| A18 | **501-7 es ~4.6 V, no 5 V.** | Después de D200 (Vf≈0.37 V). | Alimentar desde `Vout_5V` antes de D200 o documentar. |
| A19 | **Sin PTC en 501-5/501-7.** | Solo ferritas. | PTC 0.5–1 A en cada riel. |
| A20 | **FGH100M no está en el esquemático.** | Solo headers 500/501. | Definir pinout y agregar módulo o documentar que es externo. |
| A21 | **Sin serie/ESD en SD.** | CLK/CMD/DAT0 directos al ESP32. | 22–33 Ω en CLK, 10–22 Ω en CMD/DAT0, ESD junto al conector. |
| A22 | **Sin ESD en CC/SBU del USB-C.** | U400 solo protege D+/D−/VBUS. | TVS de 2 canales en CC1/CC2; SBU no usados. |
| A23 | **D201 marginal a 0.8 A.** | MS2A40LWS, Vf≈0.40 V, P≈0.32 W. | SMA/SMB 3 A o ideal diode. |
| A24 | **C207 electrolítico de 4.7 µF + FB202.** | Datasheet AP63203 recomienda cerámico ≥10 µF; C208 lo cumple. | Verificar rizo/vida y damping del filtro. |
| A25 | **Sin protección de tensión inversa en supercaps.** | Datasheet prohíbe tensión inversa. | Schottky antiparalelo por celda o balancer con protección. |
| A26 | **Huellas dudosas.** | U100 `3`; U401 `N8` vs N4; D200-D202 `- duplicate`; Cxxx `R0805`; U201 `SOIC_05WU-7_DIO-M`. | Verificar/renombrar; confirmar TSOT-26 y LQFP-44. |
| A27 | **`Library_Analizador.IntLib` ausente.** | Solo en `Project Outputs for Library_Analizador`. | Decisión A/B del AGENTS §9; copiar/recompilar. |
| A28 | **Sin test points.** | No hay TP en 5V, DVCC, AVCC, AGND, DGND, REF, VO, SPI, UART, EN, BOOT. | Agregar test pads en el layout. |
| A29 | **HLK footprint “bottom view”.** | Datasheets §11 p. 11. | Verificar que el footprint no esté espejado; campanear el prototipo. |
| A30 | **U301 se llama `BR_...` y el README lo llama puente rectificador.** | Es una bornera 1×4P. | Renombrar y corregir el README. |

---

## 6. Hallazgos medios y bajos

| ID | Hallazgo | Corrección |
|---|---|---|
| M1 | U200-3 FAULT flotante. | Pull-up 100 kΩ a 3.3 V + GPIO/test point; no a 5 V. |
| M2 | IO3/IO45/IO46 sin pulls externos. | 10 kΩ a 3.3 V o GND según el boot; no traer IO45 a header. |
| M3 | UART0 sin test points. | Agregar pads U0TXD/U0RXD/GND. |
| M4 | REFV 10 µF vs 1 µF; VO 10 µF vs 4.7 µF. | Alinear o documentar. |
| M5 | DVCC/DGND/RC todos en AGND. | Estrella en U100-6; RC al plano DGND; separar AGND/DGND. |
| M6 | VCC2 del ISO comparte 3v3_ENER_IC con el RN. | Ferrite/RC dedicado para U101-16 o mover a AVCC_3v3. |
| M7 | 1 kΩ 1 %/100 ppm y carga de 270 kΩ. | Usar 0.1 %/25 ppm; calibrar por unidad. |
| M8 | 33 nF X7R 5 %. | Usar C0G/NP0 1 %. |
| M9 | Cristal 15 pF vs CL 12 pF; ESR 80 Ω. | Verificar arranque/frecuencia; ajustar 12–18 pF. |
| M10 | F301/F302 de 200 mA para 0.23 mA. | 50 mA o resistencia fusible; MOV antes del fusible. |
| M11 | Sin filtro EMI de entrada. | X2 0.1 µF/275 VAC + CM choke 10–30 mH + sangrado. |
| M12 | HLK-5M03B solo −25…+60 °C. | Verificar temperatura del gabinete; derratear. |
| M13 | Sin debounce en CD de la SD. | 100 nF o filtro en firmware. |
| M14 | SW400/SW401 sin MPN. | Agregar MPN. |
| M15 | Proveedor `LSCS` en C101/C402. | Corregir a LCSC. |
| B1 | Símbolo `CLX` en la SD. | Es el nombre del datasheet; anotar que la función es CLK. |
| B2 | Prefijos U para conectores/módulos. | Unificar en una revisión futura. |
| B3 | No hay fiduciales. | Agregar 3 fiduciales en el layout. |
| B4 | No hay plano de masa en el PcbDoc actual. | Crear los planos AGND/DGND/RGND en el layout. |

---

## 7. Correcciones a los cálculos de la Revisión 2

### 7.1 Vpp vs Vp

La Rev2 confundió **Vpp** con **Vp**:

- El RN8302B admite **830 mVp** (pico), no 830 mVpp.
- Divisor 990 kΩ/1 kΩ: a 230 Vrms entrega 232 mVrms = **328 mVp**, no 656 Vp. El máximo teórico es `830 mVp / √2 × 991 ≈ 581 Vrms`; el límite real son los resistores 0603 de 75 V y el rango de los HLK (265 VAC).
- Burden 20 Ω: un CT 100 A/20 mA entrega 20 mArms × 20 Ω = 0.4 Vrms = **566 mVp**, por debajo de 830 mVp. La Rev2 dijo que 1.13 Vpp “excede 0.83 Vp”, pero 1.13 Vpp = 0.565 Vp. El CT 100 A/20 mA **sí es compatible**; un 100 A/40 mA daría ~1.13 Vp y sí excedería.

### 7.2 Energía del respaldo

- Banco: 2×30 F en serie = 15 F; se carga a ~4.6 V (5 V − Vf D200 − caída U200).
- El AP63203 necesita ≥3.8 V; D201 cae ~0.4 V → Vcap mínimo ~4.2 V.
- Energía útil: 0.5 × 15 × (4.6² − 4.2²) ≈ **26.4 J**.
- A 3.2 W / η 0.9: **~8.25 s**; a 2.5 W: ~10.6 s. Los “83 J / 9 s” del README no se sostienen.
- Con ideal diode en D201: ~47 J, ~12–15 s.

### 7.3 Térmica del TPS2553

- R201=20 kΩ → IOSnom ≈ 1.28 A (1.20–1.38 A).
- P inicial = (4.6 − 0) × 1.295 ≈ **5.96 W**.
- θJA WSON = 72 °C/W → ΔT ≈ **429 °C**; thermal shutdown 135 °C.
- Para no entrar en shutdown a 25 °C: Imax ≈ 332 mA → R201 ≥ 100 kΩ; a 40 °C: ~287 mA; a 50 °C: ~254 mA.
- Carga de 15 F a 0.266 A: ~259 s (4.3 min); a 0.179 A: ~385 s (6.4 min). Es una carga lenta, no los ~53 s teóricos a 1.3 A.

### 7.4 D200

- D200: P ≈ 0.45–0.50 V × 1.4–1.9 A = **0.63–0.95 W**.
- SOD-323 θJA ≈ 250–300 °C/W → Tj ≈ 180–310 °C; el máximo es 125 °C.
- D201: P ≈ 0.32 W a 0.8 A → Tj ≈ 105–121 °C; marginal.
- D202: P ≈ 0.20 W a 0.5 A → aceptable.

### 7.5 Fusibles

- F300: 200 mA, I²t 0.0682 A²s; inrush de dos HLK ≤20 A. Un pulso de 20 A/1 ms da I²t ≈ 0.4 A²s (5.9× el fusible).
- Los HLK piden 1 A/250 VAC slow-blow; a 85 V y plena carga, la corriente de entrada puede superar 200 mA.
- F301/F302 de 200 mA para 0.23 mA no protegen nada; los 0603 fallan antes.

### 7.6 Supercaps

- 30 F, 2.7 V, tolerancia 0 %/+30 %.
- A 4.6 V: peor caso 2.59 V; a 4.8 V: 2.70 V; a 4.9 V: 2.76 V.
- El balanceo 1 kΩ tiene τ≈8.3 h; no corrige el desbalance durante la carga.
- Agregar clamp/balancer; limitar Vcharge ≤4.5 V.

### 7.7 Presupuesto de 5 V

- Carga de supercaps: 1.3 A (TPS2553).
- Buck AP63203: ~0.5 A a 5 V (para 0.84 A a 3.3 V, η≈0.9).
- Header 501-7: 0.3–0.5 A.
- Total: **2.1–2.3 A** > 2 A del HLK-10M05.
- USB-C: 500/900 mA; no alcanza para 1.4–1.9 A.

---

## 8. Auditoría del BOM

| Designador(es) | Valor esquemático | MPN en CSV viejo | Problema |
|---|---|---|---|
| C102, C104, C105, C107, C204, C401, C403, C501 | 100 nF | `HGC0603G0150J500NTHJ` | 15 pF (8 piezas). |
| C103, C106, C200, C208, C500, C502 | 10 µF | `RT0603BRD07165KL` | 165 kΩ (6 piezas). |
| C205, C206, C400 | 22 µF | `049SS2-8.192F12DZLAL` | Cristal 8.192 MHz (3 piezas). |
| C401, C403 | 100 nF X7R | `0603F104Z500CT` | Y5V ±80 % en lugar de X7R. |
| C402 | 10 kΩ | `CL10B105KB8NQNC` | 1 µF; designador C para una R. |
| U200 | TPS2553DRVR | `SY6280AAC` | SOT-23-5 vs WSON-6. |
| R201 | 20 kΩ | `FRC0603F8201TS` | 8.2 kΩ (Ilim 2.8 A). |
| R505-R507 | 10 kΩ | ausentes | Sin pull-ups de DAT0/DAT1/CD. |
| R104 | 10 kΩ | ausente | Sin pull-up de SCSN. |
| C109-C113 | 100 nF/10 µF | ausentes | Sin desacople. |
| SW401 | pulsador BOOT | ausente | Sin botón de boot. |
| FB200, FB201 | — | presentes | Obsoletos. |

**Conteo:** CSV 133 filas vs netlist 144. Faltan 13 designadores; sobran FB200/FB201. El `.BomDoc` sí tiene los MPN correctos, pero tiene un ítem duplicado `RES_10kohms`; borrarlo antes de exportar.

---

## 9. Checklist antes de rutear

1. Corregir **U500-3/U500-4** (TXD/RXD).
2. Resolver **MISO/DAT0** (bus separado, buffer o EN1 por GPIO).
3. Resolver **TPS2553** (cargador dedicado o ILIM 100–200 mA).
4. Cambiar **D200/D201** a SMA/SMB 3 A o ideal diode.
5. Decidir arquitectura **AGND=N** y corregir **PS201-3**, **U301**, **PE**, **CT**.
6. Cambiar **F300** a 1 A slow-blow por HLK (≥500 V, ≥1.5 kA).
7. Reexportar **BOM** y **netlist**; verificar 144 líneas.
8. Agregar **respaldo de AVCC** y **power-fail**.
9. Agregar **LDO/RC** en AVCC y **clamp/balancer** en supercaps.
10. Corregir **C402→R403**, **EN 1 µF**, **R401/R402 Comment**, **U100-21**, **100 nF en 3v3_RS485**, **U401 strapping**.
11. Verificar **huellas** (U100 `3`, U401 N8/N4, U201 TSOT-26, D200 SOD-323 pin 1, HLK bottom view, RSM3485).
12. Recompilar en Altium, ejecutar ERC y confirmar 0 unconnected no documentados.

---

## 10. Checklist antes de fabricar

- [ ] DRC/ERC sin violaciones.
- [ ] 0 nets sin rutear.
- [ ] 0 pines de alimentación flotantes.
- [ ] U401-2 conectado y verificado en el pad 2.
- [ ] TX/RX corregido.
- [ ] MISO/DAT0 sin contención.
- [ ] TPS2553/cargador y D200 térmicamente verificados.
- [ ] U301 600 V + PE + etiquetas.
- [ ] CT con cortocircuito/TVS.
- [ ] F300/F301/F302 con rating correcto.
- [ ] BOM de 144 líneas, MPN verificados.
- [ ] AVCC respaldado y power-fail probado.
- [ ] Supercaps con clamp/balancer.
- [ ] Antena con keepout total.
- [ ] Barreras AGND/DGND y RGND con creepage/ranura.
- [ ] Hipot primario-secundario.
- [ ] Test points y fiduciales.
- [ ] Gerbers/NC drill/assembly revisados.

---

## Anexo A — Evidencia del netlist (redes clave)

```
( 3v3_MCU       C113-2 C400-2 C401-2 C402-2 FB400-1 R101-2 R400-2 U101-1 U401-2 )
( 3v3_ENER_IC   C101-2 C102-2 C103-2 C104-2 C105-2 C109-2 C112-2 FB100-1
                 R100-2 R102-1 R103-2 R104-2 U100-9 U100-28 U100-40 U100-41 U101-16 )
( 3v3_SD        C500-2 C501-2 FB501-1 R502-2 R503-2 R504-2 R505-1 R506-1 R507-1 U501-4 )
( 3v3_RS485     C502-2 FB500-1 R500-1 U500-1 )
( NetR505_2     R505-2 U101-6 U401-25 U501-7 )
( NetU401_10    U401-10 U500-4 )
( NetU401_11    U401-11 U500-3 )
( AGND          ... PS200-2 PS201-1 PS201-3 U301-1 U100-6 U100-20 U100-29 U100-39
                 U100-42 U100-43 U101-9 U101-15 ... )
( NetF300_2     F300-2 PS200-1 PS201-2 R303-2 RV300-1 )
```

## Anexo B — Diagramas

Los diagramas están en `documentation/revision_v3/diagramas/`:

| Archivo | Contenido |
|---|---|
| `S0_BLOCK.svg/pdf/png` | Diagrama de bloques del sistema. |
| `S1_THREE_PHASES.svg/pdf/png` | Entrada AC, CT y divisores. |
| `S2_MEASURES_FP.svg/pdf/png` | RN8302B LQFP-44 + ISO7741 SOIC-16 en vista de footprint. |
| `S3_POWER_FP.svg/pdf/png` | HLK, TPS2553, AP63203 y respaldo en vista de footprint. |
| `S4_MCU_FP.svg/pdf/png` | ESP32-S3-WROOM-1, USB-C y USBLC6 en vista de footprint. |
| `S5_INTERFACES_FP.svg/pdf/png` | RSM3485PCT, microSD y headers en vista de footprint. |
| `S6_PLACEMENT.svg/pdf/png` | Colocación 120×120 mm, 2 capas. |
| `S7_ROUTING.svg/pdf/png` | Plan de ruteo por corredores. |
| `S8_NETINDEX.svg/pdf/png` | Índice completo de 104 redes y 405 pines. |
| `PLACEMENT.csv` | Coordenadas de los 144 componentes, con rotación y pin 1. |
| `NET_RULES.csv` | Clase, corriente, anchura y clearance de las 104 redes. |
| `ESQUEMATICO_COMPLETO.pdf` | Todas las hojas en un solo PDF. |
| `INSTRUCCIONES.md` | Guía completa de Altium: reglas, net classes, colocación, ruteo y fabricación. |

**Limitación final:** no se abrió Altium. La verificación en Altium (ERC, DRC, huellas, netlist reexportado) la debe hacer el humano. Los diagramas reflejan el netlist del 01/11/2026 14:28; si el esquemático cambia, hay que reexportar y regenerar.
