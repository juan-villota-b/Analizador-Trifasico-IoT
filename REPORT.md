# REPORT — Auditoría integral del diseño (Revisión 4)

**Fecha:** 05/11/2026  
**Proyecto:** Analizador Trifásico IoT — Universidad Nacional de Colombia  
**Alcance:** `MAIN`, `POWER`, `THREE PHASES`, `MEASURES`, `MCU`, `INTERFACES`, netlist, BOM y preparación del layout.  
**Fuente de conectividad:** `hardware/altium/Project Outputs for Analizador_trifasico_IoT_pcb/Analizador_trifasico_IoT_pcb.NET`, generado el **05/11/2026 a las 09:40:00**, después de la última escritura de los `.SchDoc` (09:39:42).  
**Método:** extracción de registros `RECORD=1/2/34/41` de los `.SchDoc` (OLE2) + netlist + contraste pin a pin con los datasheets de `references/datasheets/` + comparación contra el netlist del commit anterior.  
**Limitación:** no se abrió Altium Designer. No hay ERC/DRC, no se midió ningún prototipo y el layout no está ruteado. Las verificaciones en Altium las debe hacer el humano.

> Este documento es el único reporte vigente del repositorio; reemplaza a los reportes anteriores (`REPORT_v1.md` y `REPORT_v3.md`).  
> **Advertencia:** `documentation/revision_v3/` e `INSTRUCCIONES.md` están basados en el netlist del **01/11/2026 14:28**, que ya no corresponde al diseño actual. No los uses como fuente de conectividad hasta regenerarlos.

---

## 0. Veredicto rápido

### Lo que sí quedó corregido

- **UART del RS-485:** `U500-3` (TXD, entrada) ahora va a `IO17` y `U500-4` (RXD, salida) a `IO18`. El cruce de la Rev3 está resuelto.
- **SPI del RN8302B vs microSD:** se separaron en dos buses. El RN usa `IO14/IO21/IO47/IO48` a través del ISO7741; la microSD usa `IO11/IO12/IO13`. La contención de MISO/DAT0 de la Rev3 está resuelta.
- **C402 → R403:** el designador de capacitor que era una resistencia de 10 kΩ se corrigió; `BOOT` ahora tiene `R403` 10 kΩ.
- **EN del ESP32:** se agregó `C404` de 1 µF; el RC de EN quedó en 10 kΩ + 1.1 µF.
- **Desacople de `3v3_RS485`:** se agregó `C503` de 100 nF.
- **PS201/HLK-5M03B:** se eliminó. La alimentación del AFE ahora la genera `U202` (B0503S-1WR3) desde `Vin_buck_5V`, y el HLK-10M05 conserva su aislamiento.
- **Burden de CT:** cambió de 10 Ω/0805 a **5.1 Ω/0603** por pierna (10.2 Ω diferencial). Es compatible con un CT de 100 A/40 mA (577 mVp), pero el modelo de CT sigue sin definirse.

### Lo que bloquea la fabricación

Hay **9 críticos** nuevos o abiertos. Los más importantes:

| # | Criticidad | Hallazgo | Consecuencia |
|---|---|---|---|
| C1 | 🔴 | **Los cuatro jacks de CT usan pin 2 (tip) y pin 4 (switch), y dejan pin 3 (sleeve) sin conectar.** En el PJ-320A, pin 4 se abre al insertar el plug. | Al conectar el CT, el secundario queda abierto y el burden deja de estar en paralelo. Voltajes peligrosos y daño al RN. |
| C2 | 🔴 | **U202 B0503S-1WR3 necesita ≥4.5 V de entrada, pero `Vin_buck_5V` es ~4.6 V normal y ~4.2 V en respaldo.** | El AVCC del RN no está garantizado durante el *last gasp*; el RN puede apagarse antes que el MCU. |
| C3 | 🔴 | **TPS2553 no es cargador:** `R201=20 kΩ` fija ~1.3 A; al cargar 15 F desde 0 V disipa ~6 W. | Thermal shutdown; el banco no se carga de forma fiable. |
| C4 | 🔴 | **D200/D201 son SOD-323 MS2A40LWS** y ahora llevan más corriente por el HaLow: D200 ~2.4 A, D201 ~1.2 A. | Tj muy por encima de 125 °C; riesgo de fallo del OR-ing de 5 V. |
| C5 | 🔴 | **F300 de 200 mA** para el HLK-10M05, cuyo datasheet pide **1 A/250 VAC slow-blow**. | El inrush puede abrir F300; la placa queda muerta. |
| C6 | 🔴 | **BOM CSV/XLSX del 31/10:** 133 filas vs 148 componentes; faltan 16 componentes comprados y sobran PS201/C402/FB200/FB201; MPN equivocados. | El ensamblador coloca 15 pF, 165 kΩ, cristales, un SY6280 y no coloca U202/C209/R203/C404/R403/C503. |
| C7 | 🔴 | **U100-21 (NC) flotante.** El datasheet V3 del RN8302B pide conectarlo a AGND. | Pin flotante en un NC que el fabricante manda aterrizar; riesgo de ruido/inestabilidad. |
| C8 | 🔴 | **Supercaps 30 F 2.7 V con tolerancia 0 %/+30 % y balanceo 1 kΩ.** A 4.6 V una celda puede llegar a 2.59 V; a 4.8 V, a 2.70 V. | Sobretensión y vida reducida; el balanceo de 1 kΩ tiene τ≈8.3 h y no actúa durante la carga. |
| C9 | 🔴 | **La barrera de alimentación AGND–DGND queda determinada por U202 (1500 VDC).** `AGND = N` por `PS200-2`; el ISO7741 aísla las señales, pero U202 es el puente de alimentación y el eslabón más débil. | Si se requiere aislamiento reforzado, 1500 VDC puede no alcanzar. Verificar norma y alternativa de 3 kVAC. |

**Altos:** el HaLow comparte el SPI de la microSD sin CS con pull-up ni resistencias serie; falta BUSY/UART del HaLow; los nets `L1/L2/L3_120VAC` no coinciden con el README/diagrama; U301 sigue siendo de 250 V sin PE; no hay power-fail; INTN1/RSTN no llegan al ESP32; U200-3 flotante; no hay TVS en CT; faltan 100–220 µF en la salida del HLK; VBUS sin PTC; R401/R402 con Comment equivocado; 3P4W solamente; FGH100M fuera del esquemático; huellas dudosas; IntLib ausente; sin test points.

---

## 1. Qué cambió respecto a la Revisión 3

### 1.1 El netlist de la Rev3 estaba desactualizado

La Rev3 se basó en el netlist del **01/11/2026 14:28**, que no coincidía con los `.SchDoc`:

| Concepto | Netlist viejo (01/11) | Netlist nuevo (05/11) |
|---|---:|---:|
| Componentes | 144 | **148** |
| Redes | 104 | **104** |
| Pines con red | 405 | **413** |
| Pines sin red | 39 | **39** |

Componentes que el netlist viejo no incluía y el nuevo sí:

- `U202` — B0503S-1WR3 (DC-DC aislado 5 V → 3.3 V, 1 W).
- `C209` — 10 µF en `AVCC_3v3`.
- `R203` — 120 Ω de precarga en `AVCC_3v3`.
- `C404` — 1 µF en `EN`.
- `R403` — 10 kΩ en `BOOT`.
- `C503` — 100 nF en `3v3_RS485`.

Componentes que el netlist viejo tenía y el nuevo ya no:

- `PS201` — HLK-5M03B.
- `C402` — el capacitor que en realidad era una resistencia de 10 kΩ.

**Conclusión:** los `.SchDoc` actuales ya tenían la arquitectura nueva; lo que estaba viejo era el `.NET` exportado. El netlist del 05/11 sí coincide con los 148 componentes de las hojas. La jerarquía de `MAIN.SchDoc` incluye las cinco hojas hijas (`THREE PHASES`, `POWER`, `MEASURES`, `MCU`, `INTERFACES`); el netlist no tiene hojas huérfanas. Esto refuerza una regla de proceso: **cada vez que se guarde un `.SchDoc`, reexportar el `.NET` antes de auditar o rutear.**

### 1.2 Cambios de conectividad del netlist

| Red / bloque | Cambio |
|---|---|
| `NetU401_10` | `U401-10` (IO17/TX) ahora va a `U500-3` (TXD). |
| `NetU401_11` | `U401-11` (IO18/RX) ahora va a `U500-4` (RXD). |
| `SPI_MOSI_H` | Nueva: `U401-19` (IO11) → `U501-3` (CMD) + `501-4`. |
| `SPI_CLK_H` | Nueva: `U401-20` (IO12) → `U501-5` (CLK) + `501-2`. |
| `SPI_MISO_H` | Nueva: `U401-21` (IO13) ← `U501-7` (DAT0) + `501-3`. |
| `NetU101_3` | `U401-22` (IO14) → ISO INA → `U100-35` (SDI). |
| `NetU101_4` | `U401-23` (IO21) → ISO INB → `U100-34` (SCSN). |
| `NetU101_5` | `U401-24` (IO47) → ISO INC → `U100-33` (SCLK). Ya no incluye `U501-5`. |
| `NetU101_6` | `U401-25` (IO48) ← ISO OUTD ← `U100-32` (SDO). |
| `NetR502_1` / `NetR505_2` | Eliminadas: ya no comparten SPI el RN y la SD. |
| `NetR300_2` | Ahora incluye `U300-4` (switch) y ya no `U300-2`. |
| `NetR302_1` | Ahora incluye `U300-2` (tip) y ya no `U300-3`. |
| `NetR311_2` / `NetR321_1` | `U302-4` / `U302-2` (mismo cambio en fase B). |
| `NetR324_2` / `NetR333_1` | `U303-4` / `U303-2` (mismo cambio en fase C). |
| `NetR336_2` / `NetR338_1` | `U304-4` / `U304-2` (mismo cambio en fase C). |
| `AGND` | Se quitaron `PS201-1/3` y `C203-2`; se agregaron `U202-3`, `C209-1`, `R203-1`. |
| `AVCC_3v3` | Se quitaron `PS201-4` y `C203-1`; se agregaron `U202-4`, `C209-2`, `R203-2`. |
| `Vin_buck_5V` | Se agregaron `U202-2` y `C203-1`. |
| `DGND` | Se agregaron `C203-2`, `C404-1`, `C503-1`, `U202-1`. |
| `3v3_MCU` / `BOOT` | `C402` salió; `R403` entró. |
| `EN` | Se agregó `C404-2`. |
| `3v3_RS485` | Se agregó `C503-2`. |
| `L1_120VAC` / `L2_120VAC` / `L3_120VAC` | Reemplazan a `NetF300_2` / `NetF301_2` / `NetF302_2`. |
| `NetD500_1` / `NetD500_2` | Reemplazan a las redes `A` / `B` del RS-485. |

### 1.3 Correcciones de la Rev3 verificadas

> **Nota de numeración:** los IDs `C1…C13` y `A1…A30` de esta tabla son los de la Rev3. Los IDs `C1…C9` y `A1…A33` de las secciones 5 y 6 son los de esta revisión y **no coinciden** con los anteriores.

| Hallazgo Rev3 | Estado | Evidencia |
|---|---|---|
| C1 — TXD/RXD cruzados | ✅ Resuelto | `U500-3` = `IO17`; `U500-4` = `IO18`. |
| C2 — MISO/DAT0 en contención | ✅ Resuelto | RN en `IO14/21/47/48`; SD en `IO11/12/13`; CS separados. |
| C3 — TPS2553 no es cargador | ❌ Abierto | `R201=20 kΩ`; ~1.3 A; ~6 W. |
| C4 — D200 SOD-323 | ❌ Abierto | Sigue `MS2A40LWS`; ahora con más carga. |
| C5 — PS201-3 = AGND | ⚠️ Parcial | PS201 eliminado; el HLK-10M05 conserva aislamiento. Pero `AGND=N` sigue y U202 es la nueva barrera (1500 VDC). |
| C6 — U301 de 250 V sin PE | ❌ Abierto | Sin PE, sin etiquetas, 250 V. |
| C7 — CT jack 30 V/0.5 A sin TVS | ❌ Abierto y agravado | Además, pin 2/4 en vez de 2/3. |
| C8 — F300 de 200 mA | ❌ Abierto | Sigue `JFC2410-0200TS`. |
| C9 — BOM viejo | ❌ Abierto | CSV/XLSX del 31/10; 133 filas. |
| C10 — AVCC sin respaldo | ⚠️ Intentado | U202 está en `Vin_buck_5V`, pero su UVLO de 4.5 V no se cumple en respaldo. |
| C11 — Sin power-fail | ❌ Abierto | No hay divisor/ADC; `IO4` sigue libre. |
| C12 — Ripple del HLK-5M03B en AVCC | ⚠️ Transformado | Ahora es el ripple del B0503S (~100 mVpp) sin LDO/RC. |
| C13 — Sobretensión de supercaps | ❌ Abierto | 30 F 0/+30 %, balanceo 1 kΩ, carga ~4.6 V. |
| A1 — C402 era una R | ✅ Resuelto | `R403` 10 kΩ. |
| A2 — EN sin 1 µF | ✅ Resuelto | `C404` 1 µF. |
| A3 — R401/R402 Comment 10 Ω | ❌ Abierto | `Comment=UNI-ROYAL HP05W3F100JT5E`; `Value=5.1k`; MPN `C55098456`. |
| A4 — VBUS sin PTC/desacople | ❌ Abierto | `5V_USB` sin capacitor ni PTC. |
| A5 — Header 200 es jumper | ❌ Abierto | Sigue siendo un jumper de 2 pines. |
| A6 — 3P4W solamente | ❌ Abierto | Divisores single-ended a N; README promete 3P3W. |
| A7 — Ambos HLK en L1 | ⚠️ Cambiado | Ya hay un solo HLK, pero sigue en L1; si se pierde L1, la placa muere. |
| A8 — 165 kΩ 0603 de 75 V | ❌ Abierto | MOV clampa a ~775 V; 129 V por resistor. |
| A9 — U100-21 flotante | ❌ Abierto | Sigue flotante. |
| A10 — Burden/CT indefinido | ⚠️ Cambiado | Burden 5.1 Ω por pierna; CT sigue sin modelo. |
| A11 — INTN1/RSTN no llegan al ESP32 | ❌ Abierto | Solo pull-ups locales. |
| A12 — UVLO del AP63203 | ❌ Abierto | EN=VIN; UVLO ~3.1 V. |
| A13 — 100 nF en 3v3_RS485 | ✅ Resuelto | `C503`. |
| A14 — Faltan 100–220 µF en HLK | ❌ Abierto | `PS200-4` sin bulk; `C200` está después de D200. |
| A15 — R501 120 Ω permanente | ❌ Abierto | Sigue permanente; ahora 0805. |
| A16 — J500 no sigue datasheet | ⚠️ Cambiado | `J500-2=A`, `J500-3=B`, `J500-1=RGND`; documentar silkscreen. |
| A17 — 501-5 y 501-7 alimentados | ✅ Aclarado | El módulo HaLow requiere **3.3 V y 5 V**; no es un conflicto. |
| A18 — 501-7 es ~4.6 V | ⚠️ Revisado | El FGH100M admite VDD_FEM 3.0–5.25 V; 4.6 V está dentro de rango, pero no es el nominal. |
| A19 — Sin PTC en 501-5/501-7 | ❌ Abierto | Solo ferritas. |
| A20 — FGH100M no está en el esquemático | ❌ Abierto | Headers 500/501 provisionales. |
| A21 — Sin serie/ESD en SD | ❌ Abierto | Ahora comparte bus con HaLow; más importante. |
| A22 — Sin ESD en CC/SBU | ❌ Abierto | U400 solo protege D+/D−/VBUS. |
| A23 — D201 marginal | ❌ Abierto | Ahora ~1.2 A en respaldo. |
| A24 — C207 electrolítico | ❌ Abierto | 4.7 µF + FB202. |
| A25 — Sin protección inversa en supercaps | ❌ Abierto | Sin Schottky antiparalelo. |
| A26 — Huellas dudosas | ❌ Abierto | U100 `3`, U401 N8, D200 `- duplicate`, Cxxx `R0805`, U201 `SOIC_05WU-7`, U202 `-1WR2`. |
| A27 — IntLib ausente | ❌ Abierto | Decisión A/B del AGENTS §9 pendiente. |
| A28 — Sin test points | ❌ Abierto | Sin TP en 5 V, DVCC, AVCC, AGND, DGND, REF, VO, SPI, UART, EN, BOOT. |
| A29 — HLK footprint bottom view | ❌ Abierto | Verificar que no esté espejado. |
| A30 — U301 se llama BR y el README dice puente | ❌ Abierto | Es una bornera 1×4P. |

---

## 2. Conteo, método y pines sin red

### 2.1 Conteo del netlist actual

| Métrica | Valor |
|---|---:|
| Componentes | **148** |
| Redes | **104** |
| Pines con red | **413** |
| Pines sin red | **39** |
| Redes de un solo pin | 0 |
| Redes solo de pasivos | 23 |

### 2.2 Los 39 pines sin red

| Componente | Pines sin red | Clasificación |
|---|---|---|
| `U100` RN8302B | 1, 2, 30, 44 | `NC`; flotar es correcto. |
| `U100` | **21** | `NC` que el datasheet V3 pide **conectar a AGND**. → **C7** |
| `U100` | 22-26 | `CF5…CF1`; no se usan. Correcto. |
| `U200` | 3 | `FAULT#` open-drain; puede quedar flotante, pero se pierde telemetría. → **A13** |
| `U300/U302/U303/U304` | 3 | **No es un pin libre: es el sleeve del jack.** Debe usarse. → **C1** |
| `U401` | 4, 8, 12, 28-30, 32-35, 38, 39 | GPIO libres. Correcto. |
| `U401` | 15, 16, 26 | Strapping IO3/IO46/IO45; defaults internos. → **A14** |
| `U401` | 36, 37 | RXD0/TXD0; no traídos a header. → **A15** |
| `U500` | 7 | `VO` (salida aislada 5 V) no usada; flotante es correcto. |
| `j400` USB-C | A8, B8 | SBU1/SBU2; no usados. Correcto. |
| `500` | 5, 6, 7 | Sin conectar; documentar. |
| `501` | 1 | Sin conectar; **posible CS/TX del HaLow**. → **A1** |

**Conclusión:** los únicos pines que requieren acción son `U100-21`, `U300/U302/U303/U304-3` (sleeve), `U401-15/16/26` (pulls externos), `U200-3` (telemetría), `501-1` (CS del HaLow) y `500-5/6/7` (reservados).

### 2.3 Limitaciones

- No se abrió Altium; la conectividad es la del netlist exportado.
- No se ejecutó ERC/DRC.
- El layout no está ruteado; no se verificaron creepage, térmica real ni keepout de antena.
- El modelo de CT/Rogowski y la tensión nominal (120 V vs 230 V) siguen sin definirse.
- No se midió ningún prototipo; los cálculos son analíticos.

---

## 3. Auditoría pin a pin por IC

### 3.1 U100 — RN8302B V3 (LQFP-44)

| Pin | Nombre | Red | Veredicto |
|---:|---|---|---|
| 1, 2 | NC | — | ✅ Flotar es correcto. |
| 3 | REFV | `REF` (C110 10 µF + C111 100 nF) | ⚠️ 10 µF vs 1 µF (M4). |
| 4-5 | IAP/IAN | `NetC300_2` / `NetC301_1` | ✅ Topología; ver CT (C1). |
| 6 | AGND | `AGND` | ✅ |
| 7-8 | IBP/IBN | `NetC304_2` / `NetC305_1` | ✅ |
| 9 | AVCC | `3v3_ENER_IC` | ✅ (C101-C105/C109/C112). |
| 10-11 | ICP/ICN | `NetC308_2` / `NetC310_1` | ✅ |
| 12-17 | VAP…VCN | `NetC302_2`…`NetC311_1` | ✅ (3P4W). |
| 18-19 | INP/INN | `NetC312_2` / `NetC313_1` | ✅ |
| 20 | RA | `AGND` | ✅ |
| **21** | **NC** | **—** | ❌ **Debe ir a AGND (C7).** |
| 22-26 | CF5…CF1 | — | ✅ No usadas. |
| 27 | RSTN | `NetR103_1` (R103 1 kΩ) | ⚠️ No llega al ESP32 (A11). |
| 28 | DVCC | `3v3_ENER_IC` | ✅ |
| 29 | DGND | `AGND` | ⚠️ Debería ser DGND; estrella en layout (M5). |
| 30 | NC | — | ✅ Flotar o DGND. |
| 31 | INTN1 | `NetR102_2` (R102 10 kΩ) | ⚠️ No llega al ESP32 (A11). |
| 32 | SDO | `SPI_MISO_RN` → U101-11 | ✅ |
| 33 | SCLK | `SPI_CLK_RN` → U101-12 | ✅ |
| 34 | SCSN | `SPI_CS_RN` → U101-13 + R104 | ✅ |
| 35 | SDI | `SPI_MOSI_RN` → U101-14 | ✅ |
| 36-37 | XO/XI | X100 + C108/C100 | ✅/⚠️ 15 pF vs CL 12 pF (M9). |
| 38 | VO | C106 10 µF + C107 100 nF | ⚠️ 10 µF vs 4.7 µF (M4). |
| 39 | DGND | `AGND` | ⚠️ Misma red (M5). |
| 40 | DVCC | `3v3_ENER_IC` | ✅ |
| 41 | RB | `3v3_ENER_IC` | ✅ (DVCC permitido). |
| 42 | PM | `AGND` | ✅ (EMM). |
| 43 | RC | `AGND` | ⚠️ Datasheet pide DGND (M5). |
| 44 | NC | — | ✅ |

**Conclusión RN8302B:** pinout funcional correcto salvo **pin 21**. El banco de desacople está bien conectado. La referencia, AVCC, DVCC, VO, RSTN, RB y PM están correctos. El cristal no necesita 10 MΩ externo. La separación AGND/DGND no existe en el esquemático; hay que hacerla en el layout o dividir las redes.

### 3.2 U101 — ISO7741DWR (SOIC-16)

| Pin | Nombre | Red | Veredicto |
|---:|---|---|---|
| 1 | VCC1 | `3v3_MCU` + C113 | ✅ |
| 2, 8 | GND1 | `DGND` | ✅ |
| 3 | INA | `NetU101_3` (MOSI) | ✅ |
| 4 | INB | `NetU101_4` (CS RN) | ✅ |
| 5 | INC | `NetU101_5` (CLK) | ✅ |
| 6 | OUTD | `NetU101_6` (MISO) | ✅ Ahora es bus dedicado; sin contención. |
| 7 | EN1 | `NetR101_1` (10 kΩ a `3v3_MCU`) | ✅ |
| 9, 15 | GND2 | `AGND` | ✅ |
| 10 | EN2 | `NetR100_1` (10 kΩ a `3v3_ENER_IC`) | ✅ |
| 11 | IND | `SPI_MISO_RN` (RN SDO) | ✅ |
| 12 | OUTC | `SPI_CLK_RN` | ✅ |
| 13 | OUTB | `SPI_CS_RN` | ✅ |
| 14 | OUTA | `SPI_MOSI_RN` | ✅ |
| 16 | VCC2 | `3v3_ENER_IC` + C112 | ✅ |

**Conclusión ISO7741:** direcciones y mapa A/B/C/D correctos. EN1/EN2 fijos en alto es aceptable ahora que el bus del RN es dedicado. El OUTD sigue habilitado, pero solo maneja `IO48`; cuando el RN está deseleccionado, el SDO queda en alta impedancia y la entrada IND flota, por lo que la salida va al estado de fail-safe alto (idle de SPI). No hay contención.

### 3.3 U200 — TPS2553DRVR (WSON-6 + EP)

| Pin | Nombre | Red | Veredicto |
|---:|---|---|---|
| 1 | OUT | `NetC201_1` | ✅ |
| 2 | ILIM | `NetR201_2` (R201 20 kΩ) | ✅ Pinout; ❌ fija ~1.3 A (C3). |
| 3 | FAULT | — | ⚠️ Flotante; agregar pull-up/test point (A13). |
| 4 | EN | `Vin_buck_5V` | ✅ |
| 5 | GND | `DGND` | ✅ |
| 6 | IN | `Vin_buck_5V` | ✅ |
| 7 | PAD | `DGND` | ✅ (soldar al plano con vías). |

**Conclusión TPS2553:** pinout correcto. El problema es la arquitectura: **no es un cargador**. Con `R201=20 kΩ`, IOS ≈ 1.28 A; al cargar 15 F desde 0 V, `P = (4.6 − 0) × 1.295 ≈ 5.96 W`; el WSON (θJA 72 °C/W) entra en thermal shutdown.

### 3.4 U201 — AP63203WU-7 (TSOT-26)

| Pin | Nombre | Red | Veredicto |
|---:|---|---|---|
| 1 | FB | `DVCC_3v3` | ✅ |
| 2 | EN | `NetC207_1` | ✅/⚠️ EN=VIN; UVLO ~3.1 V (A12). |
| 3 | VIN | `NetC207_1` | ✅ |
| 4 | GND | `DGND` | ✅ |
| 5 | SW | `NetC204_1` | ✅ |
| 6 | BST | `NetC204_2` | ✅ |

**Conclusión AP63203:** pinout y pasivos correctos (L200 3.9 µH, C204 100 nF, C205/C206 22 µF). Falta UVLO programado y power-fail.

### 3.5 U202 — B0503S-1WR3 (SIP-4, 1 W)

| Pin | Nombre | Red | Veredicto |
|---:|---|---|---|
| 1 | −Vin | `DGND` | ✅ |
| 2 | +Vin | `Vin_buck_5V` | ❌/⚠️ 4.5–4.7 V normal; ~4.2 V en respaldo; mínimo 4.5 V (C2). |
| 3 | −Vout | `AGND` | ✅ (referencia del AFE). |
| 4 | +Vout | `AVCC_3v3` + C209 + R203 | ✅/⚠️ 100 mVpp sin LDO (A4). |

**Conclusión U202:** pinout correcto y la idea de aislar el AFE es buena, pero el módulo no es adecuado para el rango de tensión disponible. El B0503S-1WR3 es de **1 W, salida 3.3 V/303 mA, entrada 4.5–5.5 V, aislamiento 1500 VDC, ripple ≤100 mVpp, carga mínima 30.3 mA**. La carga del RN + R203 es ~40 mA, así que la potencia alcanza; el problema es la tensión de entrada y el aislamiento.

### 3.6 U400 — USBLC6-2SC6 (SOT-23-6)

| Pin | Nombre | Red | Veredicto |
|---:|---|---|---|
| 1 | I/O1 | `Netj400_A6` (D+) | ✅ |
| 2 | GND | `DGND` | ✅ |
| 3 | I/O2 | `Netj400_A7` (D−) | ✅ |
| 4 | I/O2 | `DN_USB` | ✅ |
| 5 | VBUS | `5V_USB` | ⚠️ Sin PTC/desacople (A4). |
| 6 | I/O1 | `DP_USB` | ✅ |

**Conclusión USBLC6:** canales y polaridad correctos.

### 3.7 U401 — ESP32-S3-WROOM-1-N4 (41 pines)

| Pin | Nombre | Red | Veredicto |
|---:|---|---|---|
| 1, 40, 41 | GND | `DGND` | ✅ |
| **2** | **3V3** | **`3v3_MCU`** | ✅ |
| 3 | EN | `EN` (R400/C403/C404/SW400) | ✅ RC 10 kΩ + 1.1 µF. |
| 4 | IO4 | — | ⚠️ Libre; candidato a power-fail (A5). |
| 5-7 | IO5/IO6/IO7 | `Net500_1..3` | ✅ Control HaLow: RST/WK/IRQ. |
| 8 | IO15 | — | ✅ Libre. |
| 9 | IO16 | `NetR500_2` (CON RS485) | ✅ |
| 10 | IO17 | `NetU401_10` | ✅ TX → U500-3. |
| 11 | IO18 | `NetU401_11` | ✅ RX ← U500-4. |
| 12 | IO8 | — | ✅ Libre. |
| 13-14 | IO19/IO20 | `DN_USB`/`DP_USB` | ✅ |
| 15 | IO3 | — | ⚠️ Strapping JTAG (A14). |
| 16 | IO46 | — | ⚠️ Strapping boot (A14). |
| 17 | IO9 | `NetR507_2` | ✅ CD de la microSD. |
| 18 | IO10 | `Net500_4` | ✅ CS del HaLow. |
| 19 | IO11 | `SPI_MOSI_H` | ✅ MOSI SD/HaLow. |
| 20 | IO12 | `SPI_CLK_H` | ✅ CLK SD/HaLow. |
| 21 | IO13 | `SPI_MISO_H` | ✅ MISO SD/HaLow. |
| 22 | IO14 | `NetU101_3` | ✅ MOSI RN. |
| 23 | IO21 | `NetU101_4` | ✅ CS RN. |
| 24 | IO47 | `NetU101_5` | ✅ CLK RN. |
| 25 | IO48 | `NetU101_6` | ✅ MISO RN. |
| 26 | IO45 | — | ⚠️ Strapping VDD_SPI (A14). |
| 27 | IO0 | `BOOT` | ✅ R403 10 kΩ + SW401. |
| 28-30 | IO35/IO36/IO37 | — | ✅ Libres. |
| 31 | IO38 | `NetR503_1` | ✅ CS microSD. |
| 32-35 | IO39-IO42 | — | ✅ Libres. |
| 36-37 | RXD0/TXD0 | — | ⚠️ Sin test points (A15). |
| 38-39 | IO2/IO1 | — | ✅ Libres. |

**Conclusión ESP32:** alimentación y EN/BOOT correctos. El conexionado de comunicaciones es correcto. Quedan los strapping sin pulls externos, UART0 sin test points y la falta de power-fail.

### 3.8 U500 — RSM3485PCT (módulo de 10 pines; el símbolo tiene 9)

| Pin | Nombre | Red | Veredicto |
|---:|---|---|---|
| 1 | VCC | `3v3_RS485` (C502 10 µF + C503 100 nF) | ✅ |
| 2 | GND | `DGND` | ✅ |
| 3 | TXD (entrada) | `NetU401_10` = IO17/TX | ✅ Corregido. |
| 4 | RXD (salida) | `NetU401_11` = IO18/RX | ✅ Corregido. |
| 5 | CON | `NetR500_2` (R500 10 kΩ + IO16) | ✅ Reposo = RX. |
| 7 | VO | — | ✅ Flotante permitido. |
| 8 | B | `NetD500_1` (D500-1, J500-3, R501-1) | ✅ |
| 9 | A | `NetD500_2` (D500-2, J500-2, R501-2) | ✅ |
| 10 | RGND | `RGND` (D500-3, J500-1) | ✅ Aislada. |

**Conclusión RSM3485:** pinout correcto y TXD/RXD ya no están cruzados. Quedan R501 permanente, J500 sin documentar y la falta de choke/GDT para entornos industriales.

### 3.9 U501 — microSD TF-CARD-9P

| Pin | Nombre | Red | Veredicto |
|---:|---|---|---|
| 1 | DAT2 | `NetR504_1` (R504 10 kΩ) | ✅ |
| 2 | CD/DAT3 | `NetR503_1` (R503 10 kΩ + IO38) | ✅ CS con pull-up. |
| 3 | CMD | `SPI_MOSI_H` (R502 10 kΩ + IO11 + 501-4) | ✅ MOSI compartido con HaLow. |
| 4 | VDD | `3v3_SD` (C500 10 µF + C501 100 nF) | ✅ |
| 5 | CLX/CLK | `SPI_CLK_H` (IO12 + 501-2) | ✅ (nombre `CLX` cosmético). |
| 6 | VSS | `DGND` | ✅ |
| 7 | DAT0 | `SPI_MISO_H` (R505 10 kΩ + IO13 + 501-3) | ✅ MISO compartido con HaLow. |
| 8 | DAT1 | `NetR506_2` (R506 10 kΩ) | ✅ |
| 9 | CD | `NetR507_2` (R507 10 kΩ + IO9) | ✅ |
| 10 | GND/shell | `DGND` | ✅ |

**Conclusión microSD:** pinout y pull-ups correctos. El bus ya no se comparte con el RN. Sí se comparte con el HaLow; ver §4.3. Faltan serie/ESD en CLK/CMD/DAT0.

### 3.10 PS200 — HLK-10M05

| Pin | Nombre | Red | Veredicto |
|---:|---|---|---|
| 1 | AC1 | `L1_120VAC` | ✅ L1. |
| 2 | AC2 | `AGND` (N) | ✅ N; el AFE queda referenciado a N. |
| 3 | −VO | `DGND` | ✅ Salida aislada. |
| 4 | +VO | `Vout_5V` | ⚠️ Sin 100–220 µF en el pin (A9). |

**Conclusión HLK-10M05:** pinout correcto y aislamiento de 3000 VAC intacto. El problema es que es la **única** fuente AC/DC y está en L1; si L1 se pierde, la placa queda muerta. Además, la salida no tiene el bulk que recomienda el datasheet.

### 3.11 U301 — bornera 1×4P y jacks de CT

| Pin | Red | Veredicto |
|---:|---|---|
| 1 | `AGND` (N) | ⚠️ Sin etiqueta/keying. |
| 2 | `NetF302_1` (L3) | 🔴 400 V respecto a 3 (si es 230/400 V). |
| 3 | `NetF301_1` (L2) | 🔴 400 V respecto a 2/4. |
| 4 | `NetF300_1` (L1) | ✅ L1. |

**Conclusión U301:** es una bornera de 250 V, no un puente rectificador. No hay PE ni etiquetas N/L1/L2/L3. Si la red es 120/208 V, 250 V es marginal para 208 V L-L; si es 230/400 V, es insuficiente. Cambiar a 300/600 V, agregar PE y keying.

**Jacks de CT (U300/U302/U303/U304):** ver **C1**. El pin 3 (sleeve) está sin conectar y el pin 4 (switch) se usa como retorno. Es el hallazgo más grave de esta revisión.

---

## 4. Comunicaciones SPI (foco de esta revisión)

### 4.1 Bus SPI del RN8302B (aislado)

| Señal | ESP32-S3 | ISO7741 | RN8302B | Red |
|---|---|---|---|---|
| MOSI | `IO14` (pin 22) | INA 3 → OUTA 14 | SDI 35 | `NetU101_3` / `SPI_MOSI_RN` |
| CS | `IO21` (pin 23) | INB 4 → OUTB 13 | SCSN 34 | `NetU101_4` / `SPI_CS_RN` |
| CLK | `IO47` (pin 24) | INC 5 → OUTC 12 | SCLK 33 | `NetU101_5` / `SPI_CLK_RN` |
| MISO | `IO48` (pin 25) | OUTD 6 ← IND 11 | SDO 32 | `NetU101_6` / `SPI_MISO_RN` |
| EN1 | `3v3_MCU` vía R101 10 kΩ | pin 7 | — | `NetR101_1` |
| EN2 | `3v3_ENER_IC` vía R100 10 kΩ | pin 10 | — | `NetR100_1` |
| VCC1/GND1 | `3v3_MCU`/`DGND` | 1, 2, 8 | — | C113 |
| VCC2/GND2 | `3v3_ENER_IC`/`AGND` | 16, 9, 15 | — | C112 |

**Veredicto:** direcciones correctas. El bus es dedicado; el OUTD del ISO7741 ya no comparte DAT0 con la microSD. La contención de la Rev3 (C2) está resuelta. El único detalle es que el ISO7741 sin sufijo F tiene salida de fail-safe alta cuando la entrada flota; eso es correcto para el idle de MISO.

### 4.2 Bus SPI de la microSD

| Señal | ESP32-S3 | Pin microSD | Red | Pull-up |
|---|---|---|---|---|
| MOSI | `IO11` (pin 19) | CMD 3 | `SPI_MOSI_H` | R502 10 kΩ |
| CLK | `IO12` (pin 20) | CLX 5 | `SPI_CLK_H` | — |
| MISO | `IO13` (pin 21) | DAT0 7 | `SPI_MISO_H` | R505 10 kΩ |
| CS | `IO38` (pin 31) | CD/DAT3 2 | `NetR503_1` | R503 10 kΩ |
| CD | `IO9` (pin 17) | CD 9 | `NetR507_2` | R507 10 kΩ |
| VDD | — | 4 | `3v3_SD` | C500/C501 |

**Veredicto:** bus dedicado y correcto. La microSD ya no comparte MOSI/MISO/CLK con el RN. Faltan resistencias serie de 22–33 Ω en CLK y 10–22 Ω en CMD/DAT0, y ESD junto al conector (A11/A21).

### 4.3 Bus SPI compartido con el HaLow

La microSD y el HaLow comparten `SPI_CLK_H`, `SPI_MOSI_H` y `SPI_MISO_H`. El CS de la SD es `IO38`; el CS del HaLow es `IO10`, que sale por el header 500-4. La separación de CS es correcta, pero hay que verificar el tri-state de MISO.

**Header 501 (SPI + alimentación):**

| Pin | Señal | Pad FGH100M | Comparte con | Observación |
|---:|---|---:|---|---|
| 1 | NC | — | — | En el diseño de referencia es **UART TX** (CN4-1); aquí está sin conectar. |
| 2 | `SPI_CLK_H` | 24 | SD CLK | — |
| 3 | `SPI_MISO_H` | 25 | SD DAT0 | **MISO compartido**; verificar tri-state. |
| 4 | `SPI_MOSI_H` | 23 | SD CMD | **MOSI compartido**. |
| 5 | `3.3V` | 17/22 | `DVCC_3v3` vía FB503 | — |
| 6 | `DGND` | GND | — | — |
| 7 | `5V` | 4 | `Vin_buck_5V` vía FB502 | **~4.6 V**; el FGH100M admite VDD_FEM 3.0–5.25 V, pero el nominal es 5 V. |

**Header 500 (control del HaLow):**

| Pin | Señal | Pad FGH100M | GPIO ESP32-S3 | Observación |
|---:|---|---:|---|---|
| 1 | `RST_H` | 8 | `IO5` | Reset del módulo. |
| 2 | `WK_IN_H` | 6 | `IO6` | Wake. |
| 3 | `SPI_IRQ_H` | 26 | `IO7` | IRQ. |
| 4 | `SPI_CS_H` | 20 | `IO10` | **CS del HaLow**. |
| 5, 6, 7 | NC | 9 / — / — | — | El diseño de referencia usa **BUSY (pad 9)** en CN3-5, más SCL y TX. Aquí no están. |

> La correspondencia de los headers 500/501 se dedujo de las coordenadas de los puertos jerárquicos y de los pines en `INTERFACES.SchDoc`. El netlist los llama `Net500_1..4`, que no es descriptivo; conviene renombrarlos a `SPI_CS_H`, `SPI_IRQ_H`, `WK_IN_H`, `RST_H`.
>
> **Mapa confirmado en el PCB de referencia de Seeed (KiCad):** `UM1` pad 20 = `SPI_CS`, pad 23 = `SPI_MOSI`, pad 24 = `SPI_CLK`, pad 25 = `SPI_MISO`, pad 26 = `SPI_INT`, pad 8 = `RESET`, pad 6 = `WAKEUP_IN`, pad 9 = `BUSY`, pad 4 = `VDD_FEM` (5 V), pads 17/22 = 3.3 V. Ese diseño conecta el módulo a los mismos D8/D9/D10 que la microSD del XIAO ESP32S3 Sense, así que **el módulo está pensado para compartir el bus SPI con la SD**.
>
> **Comparación con el adaptador de referencia:** tu header 501 coincide con el CN4 de Seeed en 501-2..7 (SCK/MISO/MOSI/3V3/GND/5V), pero **501-1 está NC** y en el CN4 es **UART RX**. Tu header 500 coincide con el CN3 en 500-1..4 (RESET/WAKE/INT/CS), pero **500-5/6/7 están NC** y en el CN3 son **BUSY/SCL/TX**. Si vas a usar el adaptador Wio-WM6108/FGH100M, conecta esos pines o documenta que no los usas.

**Riesgos del bus compartido:**

1. **MISO compartido:** el diseño de referencia de Seeed comparte D8/D9/D10 con la microSD del XIAO ESP32S3 Sense y funciona; eso es evidencia fuerte de que el FGH100M tri-statea MISO con CS alto. Aun así, como no puedes medirlo antes de fabricar, deja un **buffer 74LVC1G125** habilitado por CS o un **0 Ω de opción** para aislar el MISO del HaLow si aparece contención.
2. **CS del HaLow sin pull-up:** `IO10` flota hasta que el ESP32 configura el GPIO. El HaLow podría quedar seleccionado al arranque y manejar MISO. Agregar 10 kΩ a 3.3 V.
3. **Sin resistencias serie:** el bus compartido no tiene 22–33 Ω en CLK/MOSI/MISO. El módulo HaLow y la SD están en extremos distintos; agregar serie y mantener <30 mm.
4. **`501-7` a ~4.6 V:** el FGH100M admite `VDD_FEM` de **3.0–5.25 V**, así que 4.6 V no lo daña; el nominal es 5 V y la potencia RF puede ser menor. Si quieres 5 V nominal, alimenta desde `Vout_5V` antes de D200 o usa un ideal diode.
5. **FGH100M no está en el esquemático:** los headers 500/501 son provisionales; el mapa de pads se confirmó en el PCB de referencia, pero el orden físico del cable no. Ver A1/A20/A33.
6. **`501-1` sin conectar:** en el diseño de referencia es **UART TX** (CN4-1). Si necesitas debug/flasheo por UART, agrégalo; si no, déjalo NC y documenta que el módulo se usa solo por SPI.
7. **Falta BUSY:** el diseño de referencia lleva `BUSY` (pad 9) a CN3-5 (D4/SDA) con 10 kΩ a GND y 0 Ω al header. Tu 500-5/6/7 están NC. Si el firmware usa BUSY, agrégalo a un GPIO.
8. **No hay UART RX/TX del HaLow:** el diseño de referencia expone TX en CN4-1 y RX en CN3-7. Tu 501-1 y 500-5/6/7 están NC. Si el módulo necesita UART para firmware/debug, el header está incompleto.

### 4.4 Qué corrigió el cambio de SPI

- **Antes:** el RN y la SD compartían MOSI/MISO/CLK; el OUTD del ISO7741 manejaba DAT0 de la SD y el SDO del RN en alta impedancia no lo tri-stateaba. Eso era la contención C2 de la Rev3.
- **Ahora:** el RN tiene su propio bus aislado en `IO14/21/47/48`; la SD tiene el suyo en `IO11/12/13`. El CS del RN (`IO21`) y el de la SD (`IO38`) son independientes. **C2 resuelto.**
- **UART:** `IO17` → TXD del RSM y `IO18` ← RXD. **C1 resuelto.**
- **Nuevo:** el HaLow comparte el bus de la SD, no el del RN. Eso es aceptable si el CS y el tri-state se manejan bien, pero es un riesgo nuevo que la Rev3 no cubría.

### 4.5 Checklist de SPI antes de rutear

- [ ] Verificar que `U100-32` (SDO) queda en alta impedancia con `SCSN=1`.
- [ ] Verificar que `U501-7` (DAT0) queda en alta impedancia con CS de SD alto.
- [ ] Verificar que el MISO del HaLow queda en alta impedancia con `SPI_CS_H=1`.
- [ ] Dejar un **buffer 74LVC1G125** o un **0 Ω de opción** para aislar el MISO del HaLow si hay contención.
- [ ] Agregar 10 kΩ de pull-up en `SPI_CS_H` (`IO10`).
- [ ] Agregar 22–33 Ω serie en CLK/MOSI/MISO de la SD/HaLow.
- [ ] Agregar `BUSY` (pad 9) a un GPIO si el firmware lo usa.
- [ ] Agregar UART TX/RX del HaLow si se necesita debug/flasheo.
- [ ] Mantener las trazas <30–50 mm, sin stubs.
- [ ] Cruzar la barrera solo por el ISO7741; no rutear SPI del RN por debajo del cuerpo.
- [ ] Mantener DGND bajo el SPI del lado MCU y AGND bajo el SPI del lado RN.
- [ ] Agregar test points: `SPI_CLK_RN`, `SPI_MOSI_RN`, `SPI_MISO_RN`, `SPI_CS_RN`, `SPI_CLK_H`, `SPI_MOSI_H`, `SPI_MISO_H`, `SPI_CS_H`.
- [ ] Confirmar el pinout del FGH100M y el orden del cable de los headers 500/501.

---

## 5. Hallazgos críticos

### C1 — Los jacks de CT usan el pin del switch, no el sleeve

**Evidencia:** `U300-2` = `NetR302_1` (señal, R309 1 kΩ a IAN); `U300-4` = `NetR300_2` (burden R301 5.1 Ω a AGND); `U300-3` = sin red. Lo mismo en `U302`, `U303`, `U304`.

En el datasheet `HX-PJ-320A-3P`:
- Pin 2 = **tip**.
- Pin 3 = **sleeve** (cuerpo).
- Pin 4 = **switch** normalmente cerrado con el tip; se **abre** al insertar el plug.
- El jack está especificado para **30 V / 0.5 A**, insuficiente para un secundario abierto.

**Nota:** si el footprint que usas numera los pads de otra forma, verifica el mapa físico antes de cambiar el esquemático; el símbolo, el footprint y el datasheet deben coincidir.

**Consecuencia:** si el CT se conecta entre pin 2 y pin 4, al insertar el plug el switch abre y el secundario queda abierto; el burden `R301/R302` deja de estar en paralelo con el CT. Un CT abierto con corriente genera cientos de voltios, daña el RN y es peligroso para el usuario. Es peor que el diseño anterior, que usaba pin 2/3.

**Corrección:**
1. Conectar el CT entre **pin 2 (tip)** y **pin 3 (sleeve)**.
2. Mover a pin 3 las conexiones que hoy están en pin 4 (`R300-2` y `R301-2`); dejar en pin 2 las que ya están (`R309-2` y `R302-1`). Así el CT queda entre pin 2 y pin 3, con burden 5.1 Ω por pierna.
3. Si se quiere cortocircuito de seguridad al desenchufar, unir **pin 4 (switch)** a **pin 3 (sleeve)**. Así, sin plug, el switch cortocircuita tip y sleeve; con plug, abre y deja el CT con su burden.
4. Agregar TVS/BAT54S en cada entrada del RN y etiquetar “NO DESCONECTAR CT CON CORRIENTE”.

### C2 — U202 no garantiza AVCC durante el respaldo

**Evidencia:** `U202-2` (+Vin) = `Vin_buck_5V`. Cadena:

```
Vout_5V (5.0 V) → D200 (0.3–0.5 V) → Vin_buck_5V (4.5–4.7 V) → U202 (+Vin)
Supercap (4.5–4.6 V) → D201 (0.3–0.4 V) → Vin_buck_5V (4.1–4.3 V) en respaldo
B0503S-1WR3: Vin mínimo = 4.5 V
```

**Consecuencia:** el B0503S queda fuera de especificación en respaldo y, con baja línea o USB, también en operación normal. El AVCC del RN puede caer antes que el 3.3 V del MCU; el *last gasp* no puede leer los registros finales del RN. Es el mismo objetivo de C10 de la Rev3, pero la implementación no lo cumple.

**Corrección:** una de:
- Alimentar U202 desde el nodo de supercaps (`NetC201_1`) con un módulo de entrada 3.5–5.5 V, o
- Usar un LDO/buck de entrada ancha (p. ej. 3.0–5.5 V) para AVCC, o
- Bajar la caída de D200/D201 con ideal diodes y asegurar ≥4.5 V hasta el final del respaldo, o
- Cambiar a un módulo aislado de 3 kVAC con rango de entrada 4.0–5.5 V.

### C3 — El TPS2553 no es un cargador de supercaps

**Evidencia:** `U200-1=OUT`, `U200-2=ILIM` (R201=20 kΩ), `U200-4=EN`, `U200-6=IN`, `U200-5/7=GND/EP`. Datasheet TPS2553: `IOSnom(mA) = 23950 / R_ILIM^0.977`; con 20 kΩ → **1.28 A** (1.20–1.38 A). θJA WSON = 72 °C/W; thermal shutdown 135 °C. Al cargar 15 F desde 0 V: `P = (4.6 − 0) × 1.295 ≈ 5.96 W`; `ΔT ≈ 429 °C`.

**Consecuencia:** la carga de 15 F no es fiable; el banco puede tardar minutos u horas en alcanzar la tensión de respaldo. El *last gasp* no está garantizado. Además, 1.3 A de carga + ~0.85 A del buck + ~0.3–0.5 A del HaLow supera los 2 A del HLK-10M05.

**Corrección:** usar un cargador de supercaps dedicado (CC/CV con foldback), o una resistencia/inductor serie que reparta la disipación, o bajar ILIM a 100–200 mA (`R_ILIM ≥ 100 kΩ`) y aceptar una carga lenta. No aumentar R201 “para que cargue más rápido”: el problema es la disipación.

### C4 — D200/D201 en SOD-323 con demasiada corriente

**Evidencia:** `D200-2=Vout_5V`, `D200-1=Vin_buck_5V`; `D201-2=NetC201_1`, `D201-1=Vin_buck_5V`; ambos `MS2A40LWS`, IF(AV)=2 A, Vf≈0.50 V a 2 A, TJmax=125 °C, SOD-323. Con el HaLow, la carga de 5 V sube: D200 ~2.4 A estimados; D201 ~1.2 A estimados en respaldo.

**Consecuencia:** D200: P≈1.2 W; θJA 250–300 °C/W → Tj≈300–360 °C. D201: P≈0.48 W → Tj≈120–145 °C. El OR-ing de 5 V se sobrecalienta; riesgo de fallo.

**Corrección:** SMA/SMB de 3 A (o ideal diode/PMOS) para D200/D201; verificar θJA y cobre de enfriamiento. Un ideal diode en D201 además recupera ~0.35 V y aumenta la energía útil del respaldo.

### C5 — F300 de 200 mA y presupuesto del HLK-10M05

**Evidencia:** F300 = `JFC2410-0200TS`, 200 mA, 250 V, I²t 0.0682 A²s, interrupting 50 A @ 250 V. Alimenta `PS200-1`, `R303`, `RV300`. El datasheet del HLK-10M05 recomienda **1 A/250 VAC slow-blow** (o 10 Ω wirewound). El HLK-10M05 es 5 V/2 A (10 W); a 120 V y 80 % de eficiencia, la corriente de entrada a plena carga es ~104 mA, pero el inrush puede superar 10 A.

**Consecuencia:** el inrush o una baja de línea pueden abrir F300; la placa queda muerta aunque L2/L3 estén presentes. La tensión de 250 V y la ruptura de 50 A son insuficientes para 230/400 V.

**Corrección:** **1 A/250 VAC slow-blow** para el HLK-10M05, con tensión ≥500 V y capacidad de ruptura ≥1.5 kA (o un MCB aguas arriba). Separar el fusible del divisor de fase A. Coordinar con el MOV.

### C6 — BOM CSV/XLSX viejo

**Evidencia:** `Analizador_trifasico_IoT_pcb.csv` y `.xlsx` son del **31/10/2026 22:59**; el `.BomDoc` es del **05/11/2026 09:40:09**. El CSV tiene 133 filas; el netlist actual tiene 148 componentes.

| Tipo | Designadores | Problema |
|---|---|---|
| Faltan (16 comprados) | `C109`, `C110`, `C111`, `C112`, `C113`, `C209`, `C404`, `C503`, `R104`, `R203`, `R403`, `R505`, `R506`, `R507`, `SW401`, `U202` | No se colocan. |
| Sobran | `C402`, `PS201`, `FB200`, `FB201` | Obsoletos. |
| MPN erróneo | `C102/C104/C105/C107/C204/C401/C403/C501` → 15 pF; `C103/C106/C200/C208/C500/C502` → 165 kΩ; `C205/C206/C400` → cristal 8.192 MHz; `U200` → SY6280AAC; `R201` → 8.2 kΩ; `R301/R302/R313/R321/R325/R333/R337/R338` → 10 Ω/0805 | El ensamblador coloca componentes equivocados. |
| Headers en stock | `200`, `500`, `501` | No requieren MPN (AGENTS §3); ignorar en la lista de compra. |

**Consecuencia:** la placa no funciona si se ensambla con el CSV del 31/10.

**Corrección:** recompilar y reexportar CSV/XLSX desde el `.BomDoc` actual; verificar las 148 líneas contra el netlist; borrar el ítem duplicado `RES_10kohms` del `.BomDoc` si sigue; no enviar el CSV del 31/10.

### C7 — U100-21 (NC) flotante

**Evidencia:** `U100-21` no está en ninguna red. El datasheet `RN8302B_Datasheet_v3.pdf`, tabla de pines, dice para RN8302B pin 21: `NC`, **“接模拟地”** (conectar a AGND).

**Consecuencia:** pin flotante en un NC que el fabricante manda aterrizar; puede acoplar ruido al AFE.

**Corrección:** conectar `U100-21` a `AGND` con traza corta al pin 6.

### C8 — Sobretensión de supercaps

**Evidencia:** `C201/C202` = 30 F, 2.7 V, tolerancia 0 %/+30 %; `R200/R202` = 1 kΩ; `Vcharge ≈ 4.6 V`. Peor caso 30 F/39 F: a 4.6 V una celda llega a **2.59 V**; a 4.8 V a **2.70 V**; a 4.9 V a **2.76 V**. El balanceo 1 kΩ tiene τ≈8.3 h y no corrige durante los ~53 s de carga.

**Consecuencia:** sobretensión y vida reducida; riesgo de fallo del banco.

**Corrección:** balanceo activo, o limitar `Vcharge ≤4.5 V`, o caps con tolerancia más estrecha; agregar clamp/TVS de 5.1 V y Schottky antiparalelo por celda.

### C9 — La barrera AGND–DGND es de 1500 VDC

**Evidencia:** `PS200-2` = `AGND` (N). `U202-3` = `AGND`, `U202-1` = `DGND`. El B0503S-1WR3 tiene aislamiento **1500 VDC/min**; el HLK-10M05 tiene **3000 VAC**. El ISO7741 aporta 5000 Vrms en las señales, pero la alimentación del lado AGND pasa por U202. Ambos ven la misma diferencia de potencial entre N y DGND; el más débil (U202) determina la barrera de alimentación.

**Consecuencia:** si el AFE se considera vivo (`AGND=N`), la barrera entre los jacks de CT y el dominio digital es de 1500 VDC. Para aislamiento reforzado (IEC 61010-1 / 62053-21) puede no alcanzar.

**Corrección:** usar un DC-DC aislado de **3 kVAC/5 kVAC** o un módulo con aislamiento reforzado; o cambiar la arquitectura para que el AFE no esté referenciado a N (divisores diferenciales/aislados). Verificar la norma aplicable y el creepage.

---

## 6. Hallazgos altos

| ID | Hallazgo | Evidencia | Corrección |
|---|---|---|---|
| A1 | **HaLow comparte SPI con la SD sin CS pull-up ni serie.** | El PCB de referencia de Seeed comparte D8/D9/D10 con la SD del XIAO y funciona; el FGH100M debería tri-statear MISO. Tu bus no tiene pull-up en CS ni serie. | 10 kΩ en `SPI_CS_H`; 22–33 Ω serie; dejar buffer/0Ω de opción. |
| A2 | **Falta BUSY y UART del HaLow.** | El PCB de referencia lleva `BUSY` (pad 9) a CN3-5, `TX` a CN4-1 y `RX` a CN3-7; tu 500-5/6/7 y 501-1 están NC. | Agregar BUSY a un GPIO y UART TX/RX si el firmware los usa; si no, documentar que solo se usa SPI. |
| A3 | **Nets `L1/L2/L3_120VAC` vs README/diagrama.** | El netlist nombra 120 V; el README/diagrama V2 no fijan tensión y la Rev3 asumió 230/400 V. | Confirmar 120/208 V o 230/400 V; ajustar U301, MOV y divisor. |
| A4 | **AVCC con ripple del B0503S sin LDO/RC.** | `U202-4` → C209 10 µF → FB100 → `3v3_ENER_IC`; B0503S ripple ≤100 mVpp a ~100 kHz; FB100 es 90 Ω@100 MHz; 20 pF de aislamiento pueden inyectar ruido de modo común. | Agregar LDO de baja ruido o RC 10 Ω + 10 µF; medir ripple en U100-9. |
| A5 | **No hay power-fail.** | No hay comparador/ADC monitoreando `Vin_buck_5V`; `IO4` libre. | Divisor 10 kΩ/10 kΩ a `IO4` (ADC1) + 100 nF; umbral ~4.2 V. |
| A6 | **INTN1/RSTN no llegan al ESP32.** | `U100-31` solo R102 10 kΩ; `U100-27` solo R103 1 kΩ. | Llevar INTN1 por un canal aislado o documentar polling; RSTN a GPIO. |
| A7 | **U301 de 250 V sin PE ni etiquetas.** | BOM `C50126V-4P0G56`, 1×4P, 10 A, 250 V; netlist sin PE. | 300/600 V, PE, etiquetas N/L1/L2/L3/PE, keying. |
| A8 | **165 kΩ 0603 de 75 V con MOV que clampa a ~775 V.** | R303-R308, R314-R319, R326-R331 (165 kΩ 0603); 775 V/6 ≈ 129 V por resistor. | 0805/1206 o 8–10 en serie; coordinar MOV/fusible. |
| A9 | **Faltan 100–220 µF en la salida del HLK.** | `PS200-4` = `Vout_5V`; C200 10 µF está después de D200. | Agregar 100–220 µF + 0.1 µF junto a PS200-4. |
| A10 | **VBUS sin PTC ni desacople.** | `5V_USB` = 200-1, j400 VBUS, U400-5; sin capacitor. | PTC 0.75–1 A; 100 nF + 10 µF a DGND. |
| A11 | **Sin serie/ESD en SD/HaLow.** | CLK/CMD/DAT0 directos al ESP32; sin TVS junto al conector. | 22–33 Ω en CLK; 10–22 Ω en CMD/DAT0; ESD junto a U501/501. |
| A12 | **R401/R402 con Comment de 10 Ω.** | `Value=5.1k`, `MPN=C55098456`, `Comment=UNI-ROYAL HP05W3F100JT5E` (10 Ω, 5 W). | Corregir Comment al MPN de 5.11 kΩ; verificar BOM. |
| A13 | **U200-3 FAULT flotante.** | `U200-3` sin red. | Pull-up 100 kΩ a 3.3 V + GPIO/test point; no a 5 V. |
| A14 | **IO3/IO45/IO46 sin pulls externos.** | `U401-15/16/26` sin red. | 10 kΩ a 3.3 V o GND según el boot; no traer IO45 a header. |
| A15 | **UART0 sin test points.** | `U401-36/37` sin red. | Pads U0TXD/U0RXD/GND. |
| A16 | **J500 no sigue el datasheet del RSM.** | `J500-1=RGND`, `J500-2=A`, `J500-3=B`; datasheet fig. 5: 1=B, 2=A, 3=shield. | Rotular A/B/RGND en silkscreen; documentar el cableado. |
| A17 | **R501 120 Ω permanente.** | `R501` entre A y B; RSM trae 22 kΩ internos. | Hacer R501 seleccionable; agregar bias externo si el bus es largo. |
| A18 | **AP63203 UVLO ~3.1 V.** | `U201-2=U201-3=NetC207_1`; datasheet p. 11. | Divisor en EN para VOFF≈3.8 V o apagado por power-fail. |
| A19 | **D201 marginal.** | MS2A40LWS, Vf≈0.40 V, P≈0.48 W a 1.2 A. | SMA/SMB 3 A o ideal diode. |
| A20 | **C207 electrolítico de 4.7 µF + FB202.** | Datasheet AP63203 recomienda cerámico ≥10 µF; C208 lo cumple. | Verificar rizo/vida y damping del filtro. |
| A21 | **Sin protección de tensión inversa en supercaps.** | Datasheet prohíbe tensión inversa. | Schottky antiparalelo por celda o balancer con protección. |
| A22 | **Huellas dudosas.** | U100 `3`; U401 `N8` vs N4; D200-D202 `- duplicate`; Cxxx `R0805`; U201 `SOIC_05WU-7`; U202 `-1WR2`; U300 `AUDIO-SMD...` vs DIP. | Verificar/renombrar; confirmar TSOT-26, LQFP-44, SIP-4, PJ-320A DIP. |
| A23 | **`Library_Analizador.IntLib` ausente.** | Solo en `Project Outputs for Library_Analizador`. | Decisión A/B del AGENTS §9; no elegir por cuenta propia. |
| A24 | **Sin test points.** | No hay TP en 5V, DVCC, AVCC, AGND, DGND, REF, VO, SPI, UART, EN, BOOT. | Agregar test pads en el layout. |
| A25 | **HLK footprint “bottom view”.** | Datasheets §11 p. 11. | Verificar que el footprint no esté espejado; campanear el prototipo. |
| A26 | **U301 se llama `BR_...` y el README lo llama puente rectificador.** | Es una bornera 1×4P. | Renombrar y corregir el README. |
| A27 | **Header 200 es un jumper, no una entrada.** | `200-1=5V_USB`; `200-2=Net200_2`→D202; no hay GND. | Documentar; usar header de 3 pines o entrada de 5 V dedicada con PTC. |
| A28 | **No hay filtro EMI de entrada.** | Sin X2/CM choke. | X2 0.1 µF/275 VAC + CM choke 10–30 mH + sangrado. |
| A29 | **Sin PTC en `501-5`/`501-7`.** | Solo ferritas FB503/FB502. | PTC 0.5–1 A en cada riel del HaLow. |
| A30 | **Sin ESD en CC/SBU del USB-C.** | U400 solo protege D+/D−/VBUS. | TVS de 2 canales en CC1/CC2; SBU no usados. |
| A31 | **3P4W solamente.** | Divisores single-ended a AGND/N; README promete 3P3W. | Documentar 3P4W o rediseñar para 3P3W. |
| A32 | **Modelo de CT/burden indefinido.** | Burden 5.1 Ω por pierna; no hay relación, clase ni saturación del CT. | Definir CT; 100 A/40 mA da 577 mVp (OK); 100 A/60 mA da 866 mVp (excede). |
| A33 | **FGH100M no está en el esquemático.** | Solo headers 500/501 provisionales; el PCB de referencia confirma el mapa de pads (20=CS, 23=MOSI, 24=CLK, 25=MISO, 26=INT, 8=RESET, 6=WAKE, 9=BUSY). | Agregar el módulo al esquemático o documentar el cableado header-módulo; incluir BUSY/UART. |

---

## 7. Hallazgos medios y bajos

| ID | Hallazgo | Corrección |
|---|---|---|
| M1 | `R203` 120 Ω 0805 125 mW disipa 91 mW (73 %). | Usar 1/4 W o 120 Ω 1/4 W; verificar derating a 70 °C. |
| M2 | `C203` 4.7 µF 0603 en la entrada de U202; el datasheet recomienda 10 µF/16 V. | Subir a 10 µF/16 V 0805; verificar DC bias a 5 V. |
| M3 | B0503S carga mínima 30.3 mA; `R203` da 27.5 mA. | El RN suma ~10 mA; verificar regulación con RN en reset. |
| M4 | REFV 10 µF vs 1 µF; VO 10 µF vs 4.7 µF. | Alinear o documentar. |
| M5 | DVCC/DGND/RC del RN en `AGND`. | Estrella en U100-6; RC al plano DGND; separar AGND/DGND en layout. |
| M6 | VCC2 del ISO comparte `3v3_ENER_IC` con el RN. | Ferrite/RC dedicado para U101-16 o mover a `AVCC_3v3`. |
| M7 | 1 kΩ 1 %/100 ppm en la base de los divisores. | Usar 0.1 %/25 ppm; calibrar por unidad. |
| M8 | 33 nF X7R 5 %. | Usar C0G/NP0 1 %. |
| M9 | Cristal 15 pF vs CL 12 pF; ESR 80 Ω. | Verificar arranque/frecuencia; ajustar 12–18 pF. |
| M10 | F301/F302 de 200 mA para 0.12 mA. | 50 mA o resistencia fusible; MOV antes del fusible. |
| M11 | HLK-5M03B ya no está; README/diagrama siguen mostrando dos HLK. | Actualizar documentación a HLK-10M05 + B0503S. |
| M12 | Sin detección de pérdida de fase. | Monitorear L1/L2/L3 o usar power-fail; el HLK está solo en L1. |
| M13 | Sin debounce en CD de la SD. | 100 nF o filtro en firmware. |
| M14 | `SW400/SW401` sin MPN en el CSV. | Agregar MPN `TSC015A05026A` (BZCN, C2888509). |
| M15 | Proveedor `LSCS` en C101. | Corregir a LCSC. |
| M16 | `U501-5` se llama `CLX`. | Es CLK; anotar que es el nombre del datasheet. |
| M17 | Prefijos U para conectores/módulos. | Unificar en una revisión futura. |
| M18 | No hay fiduciales. | Agregar 3 fiduciales en el layout. |
| M19 | No hay plano de masa en el PcbDoc actual. | Crear AGND/DGND/RGND en el layout. |
| M20 | `U202` footprint `PWRM-TH_B0503S-1WR2` vs part `-1WR3`. | Verificar que el footprint SIP-4 sea el mismo; renombrar. |
| M21 | `501-7` entrega ~4.6 V, no 5 V. | El FGH100M admite `VDD_FEM` 3.0–5.25 V; 4.6 V está dentro de rango, pero no es el nominal y puede reducir la potencia RF. Documentar; si se quiere 5 V nominal, alimentar desde `Vout_5V` antes de D200 o usar ideal diode. |

---

## 8. Auditoría del BOM

### 8.1 Conteo

| Concepto | Valor |
|---|---:|
| Componentes en el netlist | **148** |
| Headers en stock (`200`, `500`, `501`) | 3 |
| Componentes comprados esperados | **145** |
| Filas del CSV actual | 133 |
| Faltan (comprados) | **16** |
| Sobran (obsoletos) | **4** |

### 8.2 Lista de compra faltante

`C109`, `C110`, `C111`, `C112`, `C113`, `C209`, `C404`, `C503`, `R104`, `R203`, `R403`, `R505`, `R506`, `R507`, `SW401`, `U202`.

### 8.3 MPN peligrosos del CSV viejo

| Designadores | Valor esquemático | MPN en CSV | Problema |
|---|---|---|---|
| `C102`, `C104`, `C105`, `C107`, `C204`, `C401`, `C403`, `C501` | 100 nF | `HGC0603G0150J500NTHJ` | 15 pF (8 piezas). |
| `C103`, `C106`, `C200`, `C208`, `C500`, `C502` | 10 µF | `RT0603BRD07165KL` | 165 kΩ (6 piezas). |
| `C205`, `C206`, `C400` | 22 µF | `049SS2-8.192F12DZLAL` | Cristal 8.192 MHz (3 piezas). |
| `U200` | TPS2553DRVR | `SY6280AAC` | SOT-23-5 vs WSON-6. |
| `R201` | 20 kΩ | `FRC0603F8201TS` | 8.2 kΩ (Ilim 2.8 A). |
| `R301`, `R302`, `R313`, `R321`, `R325`, `R333`, `R337`, `R338` | 5.1 Ω 0603 | `HP05W3F100JT5E` | 10 Ω 0805. |
| `C402` | — | `CL10B105KB8NQNC` | Obsoleto. |
| `PS201` | — | `HLK-5M03B` | Obsoleto. |
| `FB200`, `FB201` | — | — | Obsoletos. |

**Corrección:** reexportar el CSV/XLSX desde el `.BomDoc` actual; verificar las 148 líneas contra el netlist; borrar duplicados; confirmar U202, C209, R203, C404, R403, C503, C109-C113, R104, R505-R507, SW401.

---

## 9. Checklist antes de rutear

1. Corregir **C1**: CT entre pin 2 y pin 3; pin 4 a pin 3 para cortocircuito; burden en 2/3.
2. Corregir **C2**: U202 con entrada ≥4.5 V en todo el respaldo, o cambiar de módulo.
3. Resolver **C3**: TPS2553 como cargador dedicado o ILIM 100–200 mA.
4. Cambiar **D200/D201** a SMA/SMB 3 A o ideal diode (**C4**).
5. Cambiar **F300** a 1 A/250 VAC slow-blow y revisar el presupuesto del HLK (**C5**).
6. Reexportar **BOM** y **netlist**; verificar 145 comprados + 3 headers en stock (**C6**).
7. Conectar **U100-21** a AGND (**C7**).
8. Agregar **clamp/balancer** a los supercaps (**C8**).
9. Verificar la **barrera de 1500 VDC** de U202 y la norma aplicable (**C9**).
10. Agregar **power-fail** en IO4 y **INTN1/RSTN** al ESP32.
11. Agregar **10 kΩ en SPI_CS_H**, **serie 22–33 Ω** en el bus SD/HaLow y verificar tri-state.
12. Confirmar **120 V vs 230 V**; ajustar U301, MOV y divisor.
13. Agregar **TVS/BAT54S** en CT, **PTC** en VBUS y **100–220 µF** en PS200-4.
14. Corregir **R401/R402 Comment**, **U200-3 FAULT**, **strapping IO3/IO46/IO45**, **UART0 test points**.
15. Verificar **huellas** (U100 `3`, U401 N8/N4, U201 TSOT-26, D200 SOD-323 pin 1, HLK bottom view, RSM3485, U202 SIP-4).
16. Recompilar en Altium, ejecutar ERC y confirmar 0 unconnected no documentados.

---

## 10. Checklist antes de fabricar

- [ ] DRC/ERC sin violaciones.
- [ ] 0 nets sin rutear.
- [ ] 0 pines de alimentación flotantes.
- [ ] U401-2 conectado y verificado en el pad 2.
- [ ] U500-3/U500-4 corregidos.
- [ ] MISO/DAT0 sin contención (RN, SD y HaLow).
- [ ] TPS2553/cargador y D200/D201 térmicamente verificados.
- [ ] U301 300/600 V + PE + etiquetas.
- [ ] CT con cortocircuito/TVS y pin 2/3.
- [ ] F300/F301/F302 con rating correcto.
- [ ] BOM de 145 líneas compradas (+3 headers en stock), MPN verificados.
- [ ] AVCC respaldado y power-fail probado.
- [ ] Supercaps con clamp/balancer.
- [ ] U202 con entrada ≥4.5 V en respaldo.
- [ ] Barrera AGND/DGND con creepage/ranura y aislamiento reforzado.
- [ ] Antena con keepout total.
- [ ] Hipot primario-secundario.
- [ ] Test points y fiduciales.
- [ ] Gerbers/NC drill/assembly revisados.

---

## Anexo A — Evidencia del netlist (redes clave)

```
( 3v3_MCU       C113-2 C400-2 C401-2 FB400-1 R101-2 R400-2 R403-2 U101-1 U401-2 )
( 3v3_ENER_IC   C101-2 C102-2 C103-2 C104-2 C105-2 C109-2 C112-2 FB100-1
                 R100-2 R102-1 R103-2 R104-2 U100-9 U100-28 U100-40 U100-41 U101-16 )
( 3v3_SD        C500-2 C501-2 FB501-1 R502-2 R503-2 R504-2 R505-1 R506-1 R507-1 U501-4 )
( 3v3_RS485     C502-2 C503-2 FB500-1 R500-1 U500-1 )
( AVCC_3v3      C209-2 FB100-2 R203-2 U202-4 )
( Vin_buck_5V   C200-2 C203-1 D200-1 D201-1 FB202-2 FB502-1 U200-4 U200-6 U202-2 )
( NetC201_1     C201-1 D201-2 R200-2 U200-1 )
( SPI_MOSI_RN   U100-35 U101-14 )
( SPI_MISO_RN   U100-32 U101-11 )
( SPI_CS_RN     R104-1 U100-34 U101-13 )
( SPI_CLK_RN    U100-33 U101-12 )
( NetU101_3     U101-3 U401-22 )
( NetU101_4     U101-4 U401-23 )
( NetU101_5     U101-5 U401-24 )
( NetU101_6     U101-6 U401-25 )
( SPI_MOSI_H    501-4 R502-1 U401-19 U501-3 )
( SPI_MISO_H    501-3 R505-2 U401-21 U501-7 )
( SPI_CLK_H     501-2 U401-20 U501-5 )
( NetU401_10    U401-10 U500-3 )
( NetU401_11    U401-11 U500-4 )
( NetR300_2     R300-2 R301-2 U300-4 )
( NetR302_1     R302-1 R309-2 U300-2 )
( AGND          ... PS200-2 U202-3 U301-1 U100-6 U100-20 U100-29 U100-39
                 U100-42 U100-43 U101-9 U101-15 ... )
```

## Anexo B — Fuentes y archivos

| Archivo | Uso |
|---|---|
| `hardware/altium/Project Outputs for Analizador_trifasico_IoT_pcb/Analizador_trifasico_IoT_pcb.NET` | Conectividad vigente (05/11/2026 09:40). |
| `hardware/altium/*.SchDoc` | Designadores, valores, pines y parámetros. |
| `hardware/altium/Analizador_trifasico_IoT_pcb.BomDoc` | BOM actual (05/11/2026 09:40:09). |
| `hardware/altium/Project Outputs .../*.csv` / `*.xlsx` | BOM viejo (31/10/2026 22:59); no usar. |
| `references/datasheets/RN8302B_Datasheet_v3.pdf` | Pinout y desacople del RN. |
| `references/datasheets/ISO7741DWR_Datasheet.pdf` | Canales y direcciones del ISO. |
| `references/datasheets/TI TPS2553DRVR.pdf` | ILIM y térmica. |
| `references/datasheets/AP63203WU-7_Datasheet.pdf` | UVLO y pasivos. |
| `references/datasheets/EVISUN B0503S-1WR3.pdf` | Entrada 4.5–5.5 V, 1 W, 1500 VDC. |
| `references/datasheets/ESP32-S3-WROOM_Module.pdf` | Pines y strapping. |
| `references/datasheets/RSM3485PCT_Datasheet.pdf` | TXD/RXD, CON, A/B. |
| `references/datasheets/TF-CARD-9P_Datasheet.pdf` | Pinout microSD. |
| `references/datasheets/HLK-10M05_Datasheet.pdf` | Fusible 1 A, bulk 100–220 µF, 3000 VAC. |
| `references/datasheets/HX-PJ-320A-3P_Datasheet.pdf` | Pin 2 tip, pin 3 sleeve, pin 4 switch. |
| `references/datasheets/JFC2410-0200TS_Datasheet.pdf` | Fusible 200 mA. |
| `references/datasheets/MOV-14D471K_Datasheet.pdf` | Clamp ~775 V. |
| `references/datasheets/Supercapacitor_Datasheet.pdf` | 30 F, 2.7 V, tolerancia. |

---

**Limitación final:** no se abrió Altium. La verificación en Altium (ERC, DRC, huellas, netlist reexportado) la debe hacer el humano. Este reporte refleja el netlist del **05/11/2026 09:40:00** y los `.SchDoc` guardados hasta las **09:39:42**. Si el esquemático cambia, reexporta el `.NET` y vuelve a auditar.
