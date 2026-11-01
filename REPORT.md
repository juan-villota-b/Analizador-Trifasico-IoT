# REPORT — Auditoría pin a pin de los esquemáticos (Revisión 2)

**Fecha:** 01/11/2026  
**Proyecto:** Analizador Trifásico IoT — Universidad Nacional de Colombia  
**Alcance:** `MAIN.SchDoc`, `POWER.SchDoc`, `THREE PHASES.SchDoc`, `MEASURES.SchDoc`, `MCU.SchDoc`, `INTERFACES.SchDoc`, BOM y netlist.  
**Fuente de conectividad:** `hardware/altium/Project Outputs for Analizador_trifasico_IoT_pcb/Analizador_trifasico_IoT_pcb.NET`, exportado el **01/11/2026 01:16:33**, posterior a la última modificación de las hojas (`MEASURES` 01:13:01; las demás 00:41:46).  
**Método:** extracción directa de pines y parámetros desde los `.SchDoc` (OLE2) + netlist + contraste pin a pin con los datasheets de `references/datasheets/`, usando el **RN8302B V3** (`RN8302B_Datasheet_v3.pdf`) y no la versión genérica.  
**Limitación:** no se abrió Altium Designer. El layout **no** está en el repositorio (no hay `.PcbDoc`), así que la revisión es eléctrica/esquemática; las condiciones de creepage, térmicas y de ruteo quedan como checklist para el layout.

> Este documento reemplaza la Revisión 1 (`REPORT_v1.md`, conservada solo como historial). Los identificadores `C1…C8`, `H1…`, `M1…` de la Revisión 1 **no** son los mismos de esta revisión; el estado de cada uno se aclara en §2.

---

## 0. Veredicto rápido

**Buenas noticias:** los siete errores críticos de conexión de la Revisión 1 **ya están corregidos** en el netlist nuevo:

- La entrada AC de los HLK ya está conectada (U301 → F300/F301/F302 → HLK/divisores).
- El RN8302B ya tiene AVCC en el pin 9 y REFV separado de AVCC en el pin 3.
- El ISO7741 ya tiene GND1 = DGND y GND2 = AGND.
- El RSM3485PCT ya tiene VCC/GND en el sentido correcto y RGND aislada.
- Los dos HLK ya no comparten el mismo riel de salida (PS200-3 = DGND; PS201-3 = AGND).
- Las ferritas en serie con 230 V AC desaparecieron.
- El bus SPI compartido RN8302B/microSD es **correcto** (falso positivo de la Revisión 1, ver Anexo B).

**Pero el diseño todavía no está listo para fabricar.** La Revisión 2 encuentra **8 críticos nuevos/abiertos**, además de los altos y medios:

| # | Criticidad | Hallazgo | Consecuencia |
|---|---|---|---|
| C1 | 🔴 Crítico (seguridad) | **AGND = N es necesario para medir tensión fase-neutro**; el problema es que **PS201-1 (AC) y PS201-3 (−VO) también están en AGND**, así que el HLK-5M03B ya no aísla y todo el AFE queda referenciado al primario. | Si el neutro se abre o se invierte con la fase, AGND, los jacks de CT y el AFE quedan a potencial de fase. No es SELV; falta PE, bornera de 600 V y etiquetas. |
| C2 | 🔴 Crítico (seguridad/AFE) | Las entradas de CT usan **jacks de audio 3.5 mm** (HX PJ-320A-3P, 30 V/0.5 A), sin cortocircuitador y sin TVS. | Al desconectar un CT con corriente, el secundario queda abierto y puede generar cientos de voltios; daña el RN8302B y es peligroso. |
| C3 | 🔴 Crítico (funcional) | El hardware es **3P4W solamente**: todos los divisores de tensión referencian a N/AGND y los HLK se alimentan fase-neutro. | No puede medir 3P3W como promete el README; en 3P3W los HLK verían 400 V entre fases y se dañarían. |
| C4 | 🔴 Crítico (seguridad) | La bornera **U301 es de 250 V** y el sistema es 230/400 V; no hay borne de **PE** ni etiquetas N/L1/L2/L3. | 400 V entre polos adyacentes supera la bornera; si se invierte N/L, AGND queda vivo. |
| C5 | 🔴 Crítico (funcional) | **F300 = 200 mA** compartido por los dos HLK; el datasheet de ambos recomienda **1 A/250 VAC slow-blow**. | El inrush (≤10 A) y la carga a baja línea pueden abrir F300; se pierde la alimentación completa. |
| C6 | 🔴 Crítico (AFE) | `FB100` deja el banco de desacople `NetC101_2` **desconectado del RN8302B**: C101/C102/C103/C104/C105/C109 no llegan a ningún pin del RN. | El RN solo tiene C203 (4.7 µF) lejos; faltan los 0.1 µF locales en AVCC/DVCC. Es un error de conexión, no solo de layout. |
| C7 | 🔴 Crítico (térmico) | El **SY6280** se usa como cargador de un banco de **15 F**; con 0.83 A y 4.6 V disipa hasta **3.8 W** en SOT-23-5 (0.6 W, θJA 200 °C/W). | Entra en thermal shutdown; la carga de los supercaps se vuelve intermitente y la placa puede no estar lista para el *last gasp*. |
| C8 | 🔴 Crítico (fabricación) | Los **exports CSV/XLSX del BOM son del 31/10 22:59** y todavía tienen MPN incorrectos (100 nF → 15 pF; 10 µF → 165 kΩ; 22 µF → cristal). El `.BomDoc` sí está corregido (01/11 06:17). | El ensamblador coloca componentes equivocados. Hay que reexportar y verificar línea por línea. |

**Altos:** D200/D201/D202 térmicos y con caída que reduce el respaldo; energía real del *last gasp* ~6 s y no 9 s; USB-C/header 200 no alimentan la placa como se cree; los dos HLK cuelgan de la fase A; falta desacople local del ISO7741, del ESP32 y de la microSD; precisión del divisor (1 kΩ 1 %, X7R, 0603 75 V); falta filtro EMI de entrada de los HLK; huella `3` del RN8302B por verificar; no hay señal de *power fail*.

**Medios:** pin 21 del RN debe ir a AGND; REFV 10 µF vs 1 µF; INTN1/RSTN no llegan al ESP32; bias RS-485 marginal con 120 Ω; C501 del RSM en el lado equivocado; 120 Ω de terminación permanente; falta 0.1 µF en las salidas de los HLK; sin fusible en VBUS; sin botón BOOT; headers HaLow provisionales; MAIN sin sheet entries; supercaps con poco margen; descarga de 150 Ω del SY6280; modelo de CT indefinido; mapeo de fases sin documentar; IntLib ausente; nombres de huellas `R0805`; etc.

---

## 1. Resumen ejecutivo

El diseño tiene una **arquitectura conceptual correcta**: dos dominios (digital y analógico), AFE RN8302B, ISO7741, ESP32-S3, RS-485 aislado, microSD, respaldo con supercaps. La Revisión 2 confirma que la conectividad básica ya está mucho mejor que en la Revisión 1.

Los problemas que quedan son de **tres tipos**:

1. **Seguridad y arquitectura de puesta a tierra.** `AGND = N` es una decisión válida para un medidor 3P4W, pero convierte todo el AFE en primario. La placa no tiene PE, la bornera es de 250 V, los CT entran por jacks de audio y el HLK-5M03B perdió su aislamiento. Esto debe resolverse antes de conectar 230 V.
2. **Integridad de la alimentación y del respaldo.** El desacople del RN está cortado por FB100; el SY6280 no es un cargador; los diodos OR-ing caen 0.4–0.5 V y reducen la energía útil; los HLK comparten fase y fusible.
3. **Fabricación y documentación.** El BOM exportado está viejo; la huella del RN se llama `3`; el README dice “puente rectificador” donde hay una bornera y promete 3P3W que el hardware no soporta.

**No se modificó ningún archivo de hardware.** Este informe y los datasheets son los únicos artefactos nuevos. Las correcciones son propuestas para que las ejecute el equipo en Altium.

---

## 2. Qué se corrigió de la Revisión 1 (y qué se retracta)

### 2.1 Hallazgos de la Revisión 1 que ya están corregidos

| ID v1 | Estado | Evidencia en el netlist nuevo |
|---|---|---|
| C1 | ✅ Corregido | `PS200-1` y `PS201-2` están en `NetF300_2`; `PS200-2` y `PS201-1` en `AGND`; `U301-4/3/2` → `F300/F301/F302`. Ya no hay red AC flotante. |
| C2 | ✅ Corregido | `U100-3` (REFV) está en `REF` con C110/C111 a AGND; `U100-9` (AVCC) está en `AVCC_3v3`. Ya no hay REFV a 3.3 V ni AVCC flotante. |
| C3 | ✅ Corregido | `U101-2/8` = `DGND`; `U101-9/15` = `AGND`. La barrera del ISO7741 ya no está cortocircuitada. |
| C4 | ✅ Corregido | `U500-1` = `NetC502_2` (a DVCC por FB500); `U500-2` = `DGND`. |
| C5 | ✅ Corregido | `U500-10`, `J500-1` y `D500-3` forman `RGND`, aislada de DGND/AGND. |
| C6 | ✅ Corregido (separación) | `PS200-3` = `DGND`; `PS201-3` = `AGND`. Ya no comparten el mismo riel. La nueva conexión `AGND = N` se trata en C1. |
| C7 | ✅ Corregido | FB200/FB201 ya no existen. La entrada AC usa F300/F301/F302 + RV300–RV302 + U301. |
| C8 | ⚠️ Abierto | El `.BomDoc` está corregido, pero los exports `.csv`/`.xlsx` siguen del 31/10 22:59 con MPN incorrectos. Reexportar. |

### 2.2 Hallazgos de la Revisión 1 que se retractan (eran falsos)

| ID v1 | Por qué se retracta | Fuente correcta |
|---|---|---|
| **H1** — “falta 10 MΩ entre XI y XO” | El RN8302B **V3 integra** el resistor de 10 MΩ. El datasheet dice: “晶体8.192MHz，芯片集成10MΩ偏置电阻” y “推荐外部无需跨接10MΩ电阻”. No hay que agregarlo. | `RN8302B_Datasheet_v3.pdf`, p. 6 y p. 13. |
| **M12** — “RS-485 sin bias” | El RSM3485PCT **trae 22 kΩ de pull-up/pull-down internos** (“内置上下拉电阻 22 kΩ”). No necesita bias externo; con 120 Ω el idle queda ~9 mV, apenas por encima del umbral de −10 mV (ver M4). | `RSM3485PCT_Datasheet.pdf`, §6.4 y §8.2. |
| **L1** — “pin 22 del RN es CTT, no CF5” | En el RN8302B **V3** el pin 22 es **CF5** (salida de pulso configurable). El nombre del símbolo es correcto. | `RN8302B_Datasheet_v3.pdf`, tabla 3-1, p. 12. |
| **L5** — “C401/C403 son Y5V” | El esquemático y el netlist los declaran **X7R**: `CAP CER 100nF 25V X7R 0603`. No son Y5V. | `MEASURES/MCU` parámetros de C401/C403. |
| **H3** — “Ilim 0.83 A no alcanza para el respaldo” | Durante el respaldo el SY6280 está **apagado**; la corriente de backup va por D201, no por el switch. El límite de 0.83 A afecta la **carga** de los supercaps, no la descarga. El problema real es térmico (C7). | `SY6280AAC_Datasheet.pdf`, §Operation; netlist D201/U200. |
| **C6 v1 (SPI)** — “CLK de la SD en el net del CS del RN” | Falso positivo. `NetU101_5` es el **CLK** (INC→OUTC) y `NetU101_4` es el **CS** (INB→OUTB). El bus compartido es correcto. | Netlist líneas 1206–1215; Anexo B. |

### 2.3 Correcciones de valores de la Revisión 1

La Revisión 1 decía “REFV 10 µF + 0.1 µF” y “AVCC 10 µF + 0.1 µF”. El datasheet V3 dice:

- **REFV:** 1 µF + 0.1 µF a AGND.
- **AVCC:** 4.7 µF + 0.1 µF a AGND.
- **DVCC:** 4.7 µF + 0.1 µF a DGND.
- **VO:** 4.7 µF + 0.1 µF a DGND, sin carga externa.

El diseño tiene C110 = 10 µF en REFV (mayor que 1 µF, aceptable pero no idéntico), C203 = 4.7 µF en AVCC/DVCC (correcto) y C106 = 10 µF en VO (mayor que 4.7 µF). No es crítico, pero conviene alinearlo al datasheet.

---

## 3. Metodología, conteo y limitaciones

### 3.1 Fuentes

1. Netlist Protel `Analizador_trifasico_IoT_pcb.NET` del **01/11/2026 01:16:33** (12 430 bytes).
2. Registros `RECORD=1/2/34/41` de los cinco `.SchDoc` para obtener designador, `LibReference`, pines, nombres y parámetros.
3. Datasheets de `references/datasheets/`, en particular:
   - `RN8302B_Datasheet_v3.pdf` y `RN8302B_User_Manual_v1.1.pdf`.
   - `ISO7741DWR_Datasheet.pdf`.
   - `RSM3485PCT_Datasheet.pdf`.
   - `HLK-10M05_Datasheet.pdf` y `HLK-5M03B_Datasheet.pdf`.
   - `AP63203WU-7_Datasheet.pdf`, `SY6280AAC_Datasheet.pdf`.
   - `ESP32-S3-WROOM_Module.pdf`, `ESP32-S3_Datasheet_en.pdf`.
   - `USBLC6-2SC6_Datasheet.pdf`, `SM712_Datasheet.pdf`, `TF-CARD-9P_Datasheet.pdf`.
   - `JFC2410-0200TS_Datasheet.pdf`, `MOV-14D471K_Datasheet.pdf`.
4. Cálculos propios de divisores, burden, corriente, energía y térmica.

### 3.2 Conteo del netlist nuevo

| Métrica | Valor |
|---|---:|
| Componentes | **141** |
| Redes | **103** |
| Pines con net | **397** |
| Pines sin net | **39** |
| Redes de un solo pin | **0** |
| Redes sin ningún IC (solo pasivos) | 2 relevantes: `NetC101_2` (muerta) y `NetC201_2` (midpoint de supercaps, correcta) |

### 3.3 Los 39 pines sin net (clasificados)

| Componente | Pines sin net | Clasificación |
|---|---|---|
| `U100` RN8302B | 1, 2, 30, 44 | `NC` del datasheet; flotar es correcto. |
| `U100` RN8302B | **21** | `NC` que el datasheet V3 pide **conectar a AGND**. → **M1** |
| `U100` RN8302B | 22, 23, 24, 25, 26 | `CF5…CF1`, salidas de pulso; no se usan. Correcto. |
| `U401` ESP32 | 4, 8, 12, 15, 16, 26, 27, 28, 29, 30, 32, 33, 34, 35, 36, 37, 38, 39 | GPIO libres / strapping / UART0. Ver §4.4. |
| `j400` USB-C | A8, B8 | SBU1/SBU2; no se usan. Correcto. |
| `500` header | 5, 6, 7 | Sin conectar; documentar. |
| `501` header | 1 | Sin conectar; documentar. |
| `U300/U302/U303/U304` | 4 | Pin 4 (sleeve/switch del jack) sin conectar; ver M13. |
| `U500` RSM3485 | 7 | `VO` (salida aislada 5 V) no usada; dejarlo flotante es correcto. |

**Conclusión:** no hay pines de alimentación flotantes. Los únicos dos que requieren acción son **U100-21** (debe ir a AGND) y **U300/U302/U303/U304-4** (verificar si es sleeve y si debe ir a AGND).

### 3.4 Red muerta detectada

`NetC101_2` contiene exactamente:

```
C101-2, C102-2, C103-2, C104-2, C105-2, C109-2, FB100-1
```

No contiene ningún pin de U100. Es el banco de desacople de 1 µF + 100 nF + 2×10 µF + 100 nF + 100 nF, pero **no está conectado al RN8302B**. `FB100-2` sí está en `AVCC_3v3`, y los pines 9/28/40 del RN también están en `AVCC_3v3`, pero el banco queda del otro lado del ferrite, sin carga. Es un error de conexión (C6), no solo de layout.

### 3.5 Limitaciones

- No se abrió Altium; la conectividad es la del netlist exportado. Si el netlist no se reexporta después de un cambio, este informe queda desactualizado.
- No hay `.PcbDoc` en el repositorio: no se puede verificar la huella `3` de U100, el creepage, el plano de AGND, ni la térmica real.
- No se midió ningún prototipo; los cálculos de potencia/térmica son analíticos.
- El modelo de CT/Rogowski sigue sin definirse; sin ese dato no se puede cerrar el diseño analógico.

---

## 4. Auditoría hoja por hoja, pin a pin

### 4.1 `POWER.SchDoc`

#### 4.1.1 Árbol de potencia real (según netlist)

> **Nota:** la bornera U301 no está rotulada en el esquemático. La asignación **U301-1 = N/AGND, U301-2 = L3, U301-3 = L2, U301-4 = L1** es la inferida por el netlist y por el orden de los divisores; confirmar contra el diagrama/cableado antes de energizar.

```
U301-4 (L1) ── F300 ── NetF300_2 ─┬─ PS200-1 (AC1)
                                   ├─ PS201-2 (AC2)
                                   ├─ R303-2 (divisor fase A)
                                   └─ RV300-1 (MOV)
U301-3 (L2) ── F301 ── NetF301_2 ─┬─ R314-2 (divisor fase B)
                                   └─ RV301-1
U301-2 (L3) ── F302 ── NetF302_2 ─┬─ R326-2 (divisor fase C)
                                   └─ RV302-1
U301-1 (N) ── AGND ─┬─ PS200-2 (AC2)
                     ├─ PS201-1 (AC1)
                     ├─ PS201-3 (−VO)
                     └─ referencia de los divisores/CT/RN

PS200 (HLK-10M05, 5 V/2 A, aislado) ── Vout_5V ── D200 ── Vin_buck_5V
Vin_buck_5V ─┬─ FB202 ── NetC207_1 ── U201 (AP63203) ── DVCC_3v3
             ├─ U200 (SY6280) ── NetC201_1 ── C201/C202 (15 F)
             └─ FB502 ── 501-7 (5 V de header)

Net200_2 (header 200-2) ── D202 ── NetC207_1
5V_USB (USB-C VBUS + header 200-1) ── U400-5 / 200-1
```

**Observación clave:** las dos fuentes cuelgan de **F300 / fase A**. No hay redundancia de fase; si se pierde L1, la placa completa se apaga (H4).

#### 4.1.2 HLK-10M05 (PS200) — pin a pin

| Pin | Nombre | Net | Requisito datasheet | Veredicto |
|---:|---|---|---|---|
| 1 | AC1 | `NetF300_2` | 85–265 VAC, fase | ✅ |
| 2 | AC2 | `AGND` | 85–265 VAC, neutro | ✅ si U301-1 = N; ⚠️ C1 |
| 3 | −VO | `DGND` | Salida negativa, aislada 3000 VAC | ✅ (DGND aislado de AGND) |
| 4 | +VO | `Vout_5V` | 5 V / 2 A | ✅ |

- **Falta capacitor de 0.1 µF en `Vout_5V`**: C200 (10 µF) está después de D200, no en el pin del módulo. El datasheet recomienda 10 µF + 0.1 µF a la salida. → M6.
- El módulo está aislado, pero su entrada AC2 está referenciada a AGND/N. La barrera de 3000 VAC queda entre N y DGND; es la única que separa el dominio digital del neutro. Debe cuidarse el creepage en el layout.

#### 4.1.3 HLK-5M03B (PS201) — pin a pin

| Pin | Nombre | Net | Requisito datasheet | Veredicto |
|---:|---|---|---|---|
| 1 | AC | `AGND` | 85–265 VAC, neutro | ⚠️ **AC1 = −VO = AGND** (C1) |
| 2 | AC | `NetF300_2` | 85–265 VAC, fase | ✅ |
| 3 | −VO | `AGND` | Salida negativa | 🔴 **Une la salida con la entrada AC**; anula el aislamiento del módulo |
| 4 | +VO | `AVCC_3v3` | 3.3 V / 1.5 A | ✅ |

- El HLK-5M03B es un módulo **aislado de 2500 VAC**, pero al conectar su pin 1 (AC) y su pin 3 (−VO) al mismo net `AGND`, la isolación se bypassa. El módulo sigue funcionando, pero ya no es una fuente aislada: es una fuente **referenciada a neutro**. Es una decisión de arquitectura, no un error de pinout; debe documentarse y asumirse (C1).
- Si el neutro se abre o se intercambia con la fase, `AGND`, el RN8302B y los jacks de CT quedan a potencial de fase. La bornera no tiene PE ni keying (C4).

#### 4.1.4 AP63203WU-7 (U201) — pin a pin

| Pin | Nombre | Net | Requisito datasheet | Veredicto |
|---:|---|---|---|---|
| 1 | FB | `DVCC_3v3` | FB a VOUT en versión fija 3.3 V | ✅ |
| 2 | EN | `NetC207_1` | EN alto o a VIN | ✅ |
| 3 | VIN | `NetC207_1` | 3.8–32 V; 5 V nominal | ✅ |
| 4 | GND | `DGND` | GND | ✅ |
| 5 | SW | `NetC204_1` | Nodo de conmutación | ✅ |
| 6 | BST | `NetC204_2` | 100 nF a SW | ✅ |

- C204 = 100 nF entre BST y SW; correcto.
- L200 = 3.9 µH, 2.3 A; a 2 A la corriente pico es ~2.13 A, margen 8 %. La carga real es <1.2 A, así que el margen práctico es bueno.
- C207 = 4.7 µF y C208 = 10 µF en la entrada; C205/C206/C400 = 22 µF y C401 = 100 nF en la salida. Correcto.
- **No hay problema de pinout.** El lazo de conmutación (C207/C208–U201–L200–C205/C206) debe ser corto en el layout.

#### 4.1.5 SY6280AAC (U200) — pin a pin

| Pin | Nombre | Net | Requisito datasheet | Veredicto |
|---:|---|---|---|---|
| 1 | OUT | `NetC201_1` | Salida; capacitor de salida recomendado | ⚠️ **sin capacitor local**; C7 |
| 2 | GND | `DGND` | GND | ✅ |
| 3 | ISET | `NetR201_2` (R201 8.2 kΩ a DGND) | Ilim = 6800/Rset | ✅ 0.83 A |
| 4 | EN | `Vin_buck_5V` | Activo alto; no flotar | ✅ |
| 5 | IN | `Vin_buck_5V` | 2.4–5.5 V | ✅ |

- **C7:** el SY6280 es un *load switch* con límite de corriente, no un cargador. Al conectar un banco de 15 F descargado, el switch ve una carga capacitiva enorme y trabaja en límite de corriente; la potencia disipada es (Vin − Vout)·Ilim. Al inicio, con Vin ≈ 4.6 V y Vout ≈ 0 V, son ~3.8 W. El SOT-23-5 disipa 0.6 W máx (θJA 200 °C/W) y entra en thermal shutdown (130 °C). La carga se vuelve intermitente.
- **No hay capacitor de salida** junto al pin 1; el datasheet recomienda uno para estabilidad/transitorios. Agregar 1 µF + 10 µF, pero eso no resuelve la disipación inicial.
- **Corrección:** usar un cargador de supercaps dedicado (con regulación de corriente y thermal foldback), o una resistencia/inductor serie que reparta la disipación, o cargar a corriente mucho menor. No usar el SY6280 como cargador.
- La descarga interna de 150 Ω del SY6280 (cuando EN = 0) consume ~30 mA del banco durante el respaldo; es ~3 % de la carga. → M12.

#### 4.1.6 Diodos, supercaps y header 200

| Componente | Pines / valor | Net | Veredicto |
|---|---|---|---|
| D200 | K→`Vin_buck_5V`, A→`Vout_5V` | OR-ing HLK 5 V | ⚠️ H1: 2 A SOD-323, ~0.65 W a 1.44 A |
| D201 | K→`Vin_buck_5V`, A→`NetC201_1` | Backup de supercaps | ⚠️ H1/H2: 0.45 V de caída reduce la energía útil |
| D202 | K→`NetC207_1`, A→`Net200_2` | OR-ing header 200 | ⚠️ H1: 0.25 W a 0.5 A |
| C201/C202 | 30 F / 2.7 V cada uno | Serie, midpoint `NetC201_2` | ✅ 15 F / 5.4 V; ⚠️ M11 margen |
| R200/R202 | 1 kΩ | Balanceo de C201/C202 | ✅ 2.3 mA; ⚠️ descarga lenta (~8 h) |
| C200 | 10 µF | `Vin_buck_5V`/`DGND` | ✅ |
| C203 | 4.7 µF | `AVCC_3v3`/`AGND` | ✅; ⚠️ falta 0.1 µF |
| C205/C206 | 22 µF | `DVCC_3v3`/`DGND` | ✅ |
| C207/C208 | 4.7 µF + 10 µF | `NetC207_1`/`DGND` | ✅ |
| C204 | 100 nF | BST/SW | ✅ |
| FB202 | 0603 6 A | `Vin_buck_5V` ↔ `NetC207_1` | ✅ |
| L200 | 3.9 µH / 2.3 A | SW → DVCC | ✅ |
| R201 | 8.2 kΩ | ISET → DGND | ✅ 0.83 A |
| 200 | 2 pines | 1 = `5V_USB`, 2 = `Net200_2` | ⚠️ **es un jumper USB→buck, no una entrada con GND**; H3 |

- **Header 200 no es una entrada de alimentación con retorno:** sus dos pines son `5V_USB` y el ánodo de D202. No tiene GND. Para alimentar desde USB hay que poner un jumper entre 1 y 2; sin jumper, el USB solo alimenta U400 y el pin 1, no la placa. Si se quiere una entrada externa de 5 V, usar 501-7 (5 V) y 501-6 (GND), no el header 200.
- **D200/D201/D202:** el MS2A40LWS es de 2 A y SOD-323. A 1.44 A, D200 disipa ~0.65 W; θJA de un SOD-323 ronda 250–300 °C/W, así que la unión supera los 125 °C. Usar SMA/SMB de 3 A o un ideal diode. → H1.
- **Energía real del respaldo:** el banco se carga a `Vin_buck_5V` menos la caída de U200 (~4.5–4.6 V), y durante el respaldo D201 cae ~0.45 V. El AP63203 necesita ~3.8 V de entrada para mantener 3.3 V, así que el supercap solo entrega desde ~4.6 V hasta ~4.25 V. La energía útil es ~20–25 J, no los 83 J teóricos; a 3.2 W son ~6 s, no 9 s. → H2.

---

### 4.2 `THREE PHASES.SchDoc`

#### 4.2.1 Entrada de red y protección

| Componente | Valor | Conexión | Veredicto |
|---|---|---|---|
| U301 | Bornera 4 pines, 10 A, **250 V** | 1→AGND (N), 2→F302, 3→F301, 4→F300 | 🔴 C4: 250 V para 400 V entre fases; sin PE; sin etiquetas |
| F300 | 200 mA / 250 V, time-lag | U301-4 → `NetF300_2` (HLK + divisor A + RV300) | 🔴 C5: insuficiente para los HLK |
| F301 | 200 mA / 250 V | U301-3 → `NetF301_2` (divisor B + RV301) | ⚠️ sobredimensionado para 0.23 mA; 250 V marginal |
| F302 | 200 mA / 250 V | U301-2 → `NetF302_2` (divisor C + RV302) | ⚠️ ídem |
| RV300 | MOV-14D471K (470 V, 4.5 kA) | `NetF300_2` ↔ AGND | ✅ para 230 V L-N; ⚠️ después del fusible |
| RV301 | MOV-14D471K | `NetF301_2` ↔ AGND | ✅ ídem |
| RV302 | MOV-14D471K | `NetF302_2` ↔ AGND | ✅ ídem |

- **U301 no es un puente rectificador.** El símbolo se llama `BR_50126v-4p0g56` y el README lo describe como “puente rectificador”, pero la pieza es una **bornera de 4 pines** (BOM: `1x4P 10A 250V`, LCSC C49291885). Los HLK tienen su propio rectificador interno. → M15.
- **No hay PE.** Los MOV y los HLK referencian a neutro; no hay borne de tierra. Si el gabinete es metálico, debe conectarse a PE; si es plástico, debe ser doble aislamiento. → C4.
- **No hay etiquetas N/L1/L2/L3.** El pin 1 es AGND por netlist, pero la bornera no lo indica. Un error de cableado deja AGND a fase. → C4/M15.
- **MOV después del fusible:** un pico de 4.5 kA a través de RV300 pasa por F300 y puede abrirlo antes de que el MOV actúe. Coordinar MOV/fusible (MOV antes del fusible o fusible con capacidad de pulso). → M17.

#### 4.2.2 Divisores de tensión — pin a pin

| Fase | Cadena superior | Nodo de salida | R inferior | C de filtro | Pin del RN | Veredicto |
|---|---|---|---|---|---|---|
| A | R303…R308: 6 × 165 kΩ 0.1 % desde `NetF300_2` | `NetC302_2` | R310 1 kΩ a AGND | C302 33 nF | U100-12 VAP | ✅ ratio; ⚠️ H7 |
| B | R314…R319: 6 × 165 kΩ desde `NetF301_2` | `NetC306_2` | R320 1 kΩ a AGND | C306 33 nF | U100-14 VBP | ✅ ratio; ⚠️ H7 |
| C | R326…R331: 6 × 165 kΩ desde `NetF302_2` | `NetC309_2` | R332 1 kΩ a AGND | C309 33 nF | U100-16 VCP | ✅ ratio; ⚠️ H7 |
| A− | — | `NetC303_1` | R312 1 kΩ a AGND | C303 33 nF | U100-13 VAN | ✅ |
| B− | — | `NetC307_1` | R323 1 kΩ a AGND | C307 33 nF | U100-15 VBN | ✅ |
| C− | — | `NetC311_1` | R335 1 kΩ a AGND | C311 33 nF | U100-17 VCN | ✅ |

- Cadena exacta de la fase A: `NetF300_2 → R303 → R304 → R305 → R306 → R307 → R308 → NetC302_2`; R310 de `NetC302_2` a AGND. La fase B usa R314–R319; la C, R326–R331. Correcto.
- **Cálculo:** Rtop = 990 kΩ, Rbottom = 1 kΩ; ratio = 1/991 = 1.009×10⁻³.
  - 230 Vrms → 232 mVrms = **0.656 Vpp**.
  - 277 Vrms → 280 mVrms = **0.790 Vpp** (cerca del límite de 0.8 Vpp).
  - 300 Vrms → 303 mVrms = **0.856 Vpp** (clipea).
  - Máximo medible ≈ **280 Vrms**; para 230 V L-N está bien; para 400 V L-N no.
- **H7 (precisión):** el resistor inferior de 1 kΩ es **1 % / 100 ppm**, mientras que los 165 kΩ son 0.1 % / 25 ppm. La deriva térmica del 1 kΩ domina el error de relación; para clase 0.5S usar 1 kΩ 0.1 % / 25 ppm. Los capacitores de 33 nF son **X7R 5 %**; su coeficiente de tensión/temperatura afecta fase y ganancia; usar C0G/NP0 1 %.
- **H7 (tensión):** los 165 kΩ son 0603 con 75 V de working voltage. A 230 V L-N cada uno ve ~38 V (OK). Si el MOV clamp a ~775 V, cada uno ve ~129 V (excede 75 V). A 400 V L-N, cada uno ve ~67 V (cerca del límite). Usar 0805/1206 o más resistencias en serie.
- **Filtro:** fc = 1/(2π·(990 kΩ || 1 kΩ)·33 nF) ≈ 4.8 kHz; desfase a 50 Hz ≈ 0.6°. Correcto para anti-alias, pero la tolerancia X7R degrada la fase.

#### 4.2.3 Entradas de corriente — pin a pin

| Canal | Jack | Terminal + | Red a IAP/IBP/ICP/INP | Terminal − | Red a IAN/IBN/ICN/INN | Veredicto |
|---|---|---|---|---|---|---|
| A | U300 | pin 2 | R300 1 kΩ → `NetC300_2` (U100-4 IAP); C300 33 nF; R301 10 Ω a AGND | pin 3 | R309 1 kΩ → `NetC301_1` (U100-5 IAN); C301 33 nF; R302 10 Ω a AGND | ✅ burden 20 Ω |
| B | U302 | pin 2 | R311 1 kΩ → `NetC304_2` (U100-7 IBP); C304 33 nF; R313 10 Ω a AGND | pin 3 | R322 1 kΩ → `NetC305_1` (U100-8 IBN); C305 33 nF; R321 10 Ω a AGND | ✅ |
| C | U303 | pin 2 | R324 1 kΩ → `NetC308_2` (U100-10 ICP); C308 33 nF; R325 10 Ω a AGND | pin 3 | R334 1 kΩ → `NetC310_1` (U100-11 ICN); C310 33 nF; R333 10 Ω a AGND | ✅ |
| N | U304 | pin 2 | R336 1 kΩ → `NetC312_2` (U100-18 INP); C312 33 nF; R337 10 Ω a AGND | pin 3 | R339 1 kΩ → `NetC313_1` (U100-19 INN); C313 33 nF; R338 10 Ω a AGND | ✅ |

- **Burden diferencial:** R301 + R302 = **20 Ω** (cada uno de 10 Ω a AGND). A 41.5 mA pico, la tensión diferencial es 0.83 Vp (límite del RN). La potencia en cada 10 Ω es ~17 mW; correcto.
- **Filtro:** 1 kΩ + 33 nF ≈ 4.8 kHz; desfase ~0.6° a 50 Hz. Correcto.
- **M13 (modelo de CT):** no está definido el CT/Rogowski. Con 20 Ω de burden, un CT de 100 A/20 mA daría 0.4 Vrms = **1.13 Vpp**, por encima del límite de 0.83 Vp; un CT de 100 A/10 mA daría 0.566 Vpp (OK). Hay que definir relación, clase y carga antes de elegir el burden.
- **C2 (CT abierto):** el jack permite desconectar el CT con corriente. El secundario abierto puede generar cientos de voltios; el RN tiene absoluto máximo ±2 V y no hay TVS. Agregar BAT54S/TVS y un jack cortocircuitador, o usar bornera con cortocircuito.
- **M14 (pin 4 del jack):** U300/U302/U303/U304 pin 4 está sin conectar. Si es el sleeve/switch, el cableado debe documentarse; un plug mono puede cortocircuitar ring y sleeve. Verificar el pinout real y, si es blindaje, conectar a AGND.

#### 4.2.4 Mapeo de fases

| Fase | Tensión | Corriente | Terminal U301 |
|---|---|---|---|
| A | VAP (U100-12) ← R303…R308 | U300 → IAP/IAN | U301-4 / F300 |
| B | VBP (U100-14) ← R314…R319 | U302 → IBP/IBN | U301-3 / F301 |
| C | VCP (U100-16) ← R326…R331 | U303 → ICP/ICN | U301-2 / F302 |
| N | — | U304 → INP/INN | U301-1 / AGND |

- **M14:** no hay etiquetas L1/L2/L3 ni correspondencia documentada entre U300/U302/U303 y las tensiones A/B/C. Si se cruza una fase de tensión con una de corriente, la potencia/energía sale mal. Etiquetar en el esquemático y en el layout.
- **C3 (3P3W):** en 3P3W no hay neutro. Los divisores referencian a AGND/N y los HLK se alimentan fase-neutro; sin N, AGND flota y los HLK verían 400 V entre fases. El hardware es **3P4W solamente**. El README debe dejar de prometer 3P3W o se debe agregar una fuente trifásica y un acondicionamiento de tensión fase-fase.

---

### 4.3 `MEASURES.SchDoc`

#### 4.3.1 RN8302B V3 (U100, LQFP-44) — pin a pin

Datasheet: `RN8302B_Datasheet_v3.pdf`, tabla 3-1 (páginas 9–14). **No** se usó la versión genérica.

| Pin | Nombre | Net | Requisito V3 | Veredicto |
|---:|---|---|---|---|
| 1 | NC | — | NC, flotar | ✅ |
| 2 | NC | — | NC, flotar | ✅ |
| 3 | REFV | `REF` (C110 10 µF + C111 100 nF a AGND) | Salida/entrada de referencia 1.25 V; **1 µF + 0.1 µF a AGND** | ✅ funcional; ⚠️ M2: 10 µF en vez de 1 µF |
| 4 | IAP | `NetC300_2` (R300/C300) | Entrada diferencial de corriente A, ≤830 mVp | ✅ |
| 5 | IAN | `NetC301_1` (R309/C301) | Entrada diferencial de corriente A | ✅ |
| 6 | AGND | `AGND` | Tierra analógica | ✅ |
| 7 | IBP | `NetC304_2` (R311/C304) | Corriente B | ✅ |
| 8 | IBN | `NetC305_1` (R322/C305) | Corriente B | ✅ |
| 9 | AVCC | `AVCC_3v3` | 3.3 V ±10 %; **4.7 µF + 0.1 µF a AGND** | ✅ conectado; 🔴 C6: falta 0.1 µF local |
| 10 | ICP | `NetC308_2` (R324/C308) | Corriente C | ✅ |
| 11 | ICN | `NetC310_1` (R334/C310) | Corriente C | ✅ |
| 12 | VAP | `NetC302_2` (R308/R310/C302) | Tensión A | ✅ |
| 13 | VAN | `NetC303_1` (R312/C303) | Tensión A | ✅ |
| 14 | VBP | `NetC306_2` (R319/R320/C306) | Tensión B | ✅ |
| 15 | VBN | `NetC307_1` (R323/C307) | Tensión B | ✅ |
| 16 | VCP | `NetC309_2` (R331/R332/C309) | Tensión C | ✅ |
| 17 | VCN | `NetC311_1` (R335/C311) | Tensión C | ✅ |
| 18 | INP | `NetC312_2` (R336/C312) | Corriente de neutro | ✅ |
| 19 | INN | `NetC313_1` (R339/C313) | Corriente de neutro | ✅ |
| 20 | RA | `AGND` | Reservado; **conectar a AGND** | ✅ |
| 21 | NC | — | **NC; conectar a AGND** | ❌ **M1: flotante** |
| 22 | CF5 | — | Salida de pulso configurable; no usada | ✅ (el nombre `CF5` es correcto en V3) |
| 23 | CF4 | — | Salida; no usada | ✅ |
| 24 | CF3 | — | Salida; no usada | ✅ |
| 25 | CF2 | — | Salida; no usada | ✅ |
| 26 | CF1 | — | Salida; no usada | ✅ |
| 27 | RSTN | `NetR103_1` (R103 1 kΩ a `AVCC_3v3`) | Activo bajo; interno flotante; **1 kΩ de pull-up o a VCC** | ✅ |
| 28 | DVCC | `AVCC_3v3` | 3.3 V ±10 %; **4.7 µF + 0.1 µF a DGND** | ✅ conectado; 🔴 C6: falta 0.1 µF local |
| 29 | DGND | `AGND` | Tierra digital | ✅ (el lado digital del RN está referenciado a AGND) |
| 30 | NC | — | NC; flotar o a DGND | ✅ |
| 31 | INTN1 | `NetR102_2` (R102 10 kΩ a `AVCC_3v3`) | Salida de interrupción; pull-up opcional | ⚠️ **M3: no llega al ESP32** |
| 32 | SDO | `SPI_MISO_RN` → U101-11 | Salida SPI; **alta impedancia cuando SCSN = 1** | ✅ |
| 33 | SCLK | `SPI_CLK_RN` → U101-12 | Entrada de reloj SPI | ✅ |
| 34 | SCSN | `SPI_CS_RN` + R104 10 kΩ a `AVCC_3v3` | Entrada de selección; pull-up recomendado | ✅ (R104 ya está) |
| 35 | SDI | `SPI_MOSI_RN` → U101-14 | Entrada de datos SPI | ✅ |
| 36 | XO | `XO` (X100-2, C108) | Salida del cristal | ✅ |
| 37 | XI | `XI` (X100-1, C100) | Entrada del cristal; **10 MΩ interno** | ✅ (no se necesita externo; H1 v1 retractado) |
| 38 | VO | `VO` (C106 10 µF + C107 100 nF) | Salida del regulador interno; **4.7 µF + 0.1 µF a DGND, sin carga** | ✅; ⚠️ M2: 10 µF en vez de 4.7 µF |
| 39 | DGND | `AGND` | Tierra digital | ✅ |
| 40 | DVCC | `AVCC_3v3` | 3.3 V ±10 %; 4.7 µF + 0.1 µF a DGND | ✅ conectado; 🔴 C6 |
| 41 | RB | `AVCC_3v3` | RN8302B: **a DVCC o a DGND** | ✅ (AVCC_3v3 = DVCC) |
| 42 | PM | `AGND` | PM = 0 → EMM (medición); 1 kΩ a GND o directo | ✅ |
| 43 | RC | `AGND` | Reservado; **a DGND** | ✅ (AGND = DGND en el chip; ver layout) |
| 44 | NC | — | NC; flotar | ✅ |

**Conclusión RN8302B:** el pinout funcional es correcto salvo **pin 21** (debe ir a AGND) y el **desacople local** (C6). La referencia, AVCC, DVCC, VO, RSTN, RB y PM están bien conectados. El cristal no necesita 10 MΩ externo.

#### 4.3.2 ISO7741DWR (U101, SOIC-16) — pin a pin

| Pin | Nombre | Net | Requisito datasheet | Veredicto |
|---:|---|---|---|---|
| 1 | VCC1 | `DVCC_3v3` | 2.25–5.5 V; **0.1 µF a GND1** | ✅; ⚠️ **H5: sin 0.1 µF local** |
| 2 | GND1 | `DGND` | GND1 (lado digital) | ✅ |
| 3 | INA | `NetR502_1` (MOSI) | Entrada canal A | ✅ |
| 4 | INB | `NetU101_4` (CS RN) | Entrada canal B | ✅ |
| 5 | INC | `NetU101_5` (CLK RN + SD) | Entrada canal C | ✅ |
| 6 | OUTD | `NetR505_2` (MISO) | Salida canal D | ✅ |
| 7 | EN1 | `NetR101_1` (R101 10 kΩ a DVCC) | Alto o abierto = habilitado | ✅ |
| 8 | GND1 | `DGND` | GND1 | ✅ |
| 9 | GND2 | `AGND` | GND2 (lado RN) | ✅ |
| 10 | EN2 | `NetR100_1` (R100 10 kΩ a AVCC) | Alto o abierto = habilitado | ✅ |
| 11 | IND | `SPI_MISO_RN` (RN SDO) | Entrada canal D | ✅ |
| 12 | OUTC | `SPI_CLK_RN` | Salida canal C | ✅ |
| 13 | OUTB | `SPI_CS_RN` | Salida canal B | ✅ |
| 14 | OUTA | `SPI_MOSI_RN` | Salida canal A | ✅ |
| 15 | GND2 | `AGND` | GND2 | ✅ |
| 16 | VCC2 | `AVCC_3v3` | 2.25–5.5 V; **0.1 µF a GND2** | ✅; ⚠️ **H5: sin 0.1 µF local** |

- **Mapa de canales (correcto):**
  - A: `INA` (3) ← IO14/MOSI → `OUTA` (14) → RN SDI (35).
  - B: `INB` (4) ← IO21/CS → `OUTB` (13) → RN SCSN (34).
  - C: `INC` (5) ← IO47/CLK → `OUTC` (12) → RN SCLK (33).
  - D: RN SDO (32) → `IND` (11) → `OUTD` (6) → IO48/MISO.
- **H5:** el ISO7741 es un aislador de alta velocidad; el datasheet pide 0.1 µF en cada VCC. En la placa, C500/C501 están en `DVCC` (INTERFACES) y C203 en `AVCC` (POWER), pero no hay 0.1 µF junto a los pines 1 y 16. Agregar 0.1 µF a DGND y AGND respectivamente.
- **Aislamiento:** GND1/GND2 separados correctamente. El creepage del SOIC-16 y el corte en el plano de masa deben verificar >8 mm; el ISO7741 es el único puente entre DGND y AGND.

#### 4.3.3 Cristal X100 — verificación

| Parámetro | Valor | Requisito RN8302B V3 | Veredicto |
|---|---|---|---|
| Frecuencia | 8.192 MHz | 8.192 MHz típico | ✅ |
| Carga | 12 pF | 15 pF típico | ✅/⚠️ verificar |
| C100/C108 | 15 pF NP0 | El datasheet pide CL típica 15 pF; con 15 pF + stray se obtiene ~10–12 pF | ⚠️ verificar con el cristal real |
| ESR | 60 Ω máx | <100 Ω recomendado | ✅ |
| R feedback | **No instalada** | **10 MΩ interno**; el datasheet recomienda no ponerlo externo | ✅ **H1 v1 retractado** |

- No agregar el resistor de 10 MΩ: el RN8302B V3 lo integra. Si se agrega, el datasheet dice que la oscilación aún arranca con margen >5, pero no es necesario.
- Los capacitores de 15 pF son NP0, correctos; verificar el CL real del cristal (12 pF) y el stray del PCB. Si el cristal no arranca, subir a 22 pF.

#### 4.3.4 Desacople del RN8302B — estado real

| Rail | Capacitores en el netlist | Requisito V3 | Veredicto |
|---|---|---|---|
| AVCC (pin 9) | C203 4.7 µF en `AVCC_3v3`; C101–C105/C109 en `NetC101_2` **sin conexión al RN** | 4.7 µF + 0.1 µF a AGND | 🔴 **C6** |
| DVCC (pines 28/40) | Igual `AVCC_3v3`; mismo banco desconectado | 4.7 µF + 0.1 µF a DGND | 🔴 **C6** |
| REFV (pin 3) | C110 10 µF + C111 100 nF a AGND | 1 µF + 0.1 µF | ✅; ⚠️ M2 |
| VO (pin 38) | C106 10 µF + C107 100 nF a AGND | 4.7 µF + 0.1 µF a DGND, sin carga | ✅; ⚠️ M2 |

- **C6 es un error de conexión:** el banco C101/C102/C103/C104/C105/C109 está en `NetC101_2`, y `FB100-1` también; `FB100-2` está en `AVCC_3v3`, pero ningún pin del RN está en `NetC101_2`. El ferrite queda como una rama abierta. La corrección es mover los pines 9/28/40 del RN a `NetC101_2` (con FB100 en serie desde `AVCC_3v3`) o eliminar FB100 y conectar el banco a `AVCC_3v3`.
- C203 (4.7 µF) está en `POWER.SchDoc`, lejos del RN; no sustituye el 0.1 µF local.

#### 4.3.5 Pasivos de `MEASURES` — pin a pin

| Componente | Valor | Pines / net | Veredicto |
|---|---|---|---|
| C100 | 15 pF NP0 | 1 AGND, 2 XI | ✅ |
| C101 | 1 µF X7R | 1 AGND, 2 `NetC101_2` | ⚠️ C6 (banco muerto) |
| C102 | 100 nF X7R | 1 AGND, 2 `NetC101_2` | ⚠️ C6 |
| C103 | 10 µF X5R | 1 AGND, 2 `NetC101_2` | ⚠️ C6 |
| C104 | 10 µF X5R | 1 AGND, 2 `NetC101_2` | ⚠️ C6 |
| C105 | 100 nF X7R | 1 AGND, 2 `NetC101_2` | ⚠️ C6 |
| C106 | 10 µF X5R | 1 AGND, 2 VO | ✅/⚠️ M2 |
| C107 | 100 nF X7R | 1 AGND, 2 VO | ✅ |
| C108 | 15 pF NP0 | 1 AGND, 2 XO | ✅ |
| C109 | 100 nF X7R | 1 AGND, 2 `NetC101_2` | ⚠️ C6 |
| C110 | 10 µF X5R | 1 AGND, 2 REF | ✅/⚠️ M2 |
| C111 | 100 nF X7R | 1 AGND, 2 REF | ✅ |
| FB100 | 0603 6 A | 1 `NetC101_2`, 2 `AVCC_3v3` | 🔴 C6 (rama abierta) |
| R100 | 10 kΩ | 1 `NetR100_1` (EN2), 2 AVCC | ✅ |
| R101 | 10 kΩ | 1 `NetR101_1` (EN1), 2 DVCC | ✅ |
| R102 | 10 kΩ | 1 AVCC, 2 `NetR102_2` (INTN1) | ✅ pull-up; ⚠️ M3 |
| R103 | 1 kΩ | 1 `NetR103_1` (RSTN), 2 AVCC | ✅ |
| R104 | 10 kΩ | 1 `SPI_CS_RN`, 2 AVCC | ✅ pull-up de SCSN |

---

### 4.4 `MCU.SchDoc`

#### 4.4.1 ESP32-S3-WROOM-1-N4 (U401, 41 pines) — pin a pin

| Pin | Nombre | Net | Función / requisito | Veredicto |
|---:|---|---|---|---|
| 1 | GND | `DGND` | GND | ✅ |
| 2 | 3V3 | `NetFB400_1` (FB400 → DVCC) | 3.0–3.6 V; 22 µF + 0.1 µF en el pin | ⚠️ **H6: C400/C401 están del lado DVCC, no del pin** |
| 3 | EN | `EN` (R400 10 kΩ a DVCC, C402 1 µF, C403 100 nF, SW400 a DGND) | Reset activo bajo | ✅ |
| 4 | IO4 | — | GPIO libre | ✅ |
| 5 | IO5 | `Net500_1` | Header 500-1 | ✅ |
| 6 | IO6 | `Net500_2` | Header 500-2 | ✅ |
| 7 | IO7 | `Net500_3` | Header 500-3 | ✅ |
| 8 | IO15 | — | GPIO libre | ✅ |
| 9 | IO16 | `NetR500_2` (R500 10 kΩ a DVCC + U500-5 CON) | GPIO; CON del RSM (activo bajo = TX) | ✅ (reposo = RX) |
| 10 | IO17 | `NetU401_10` → U500-4 RXD | U1TXD del ESP32 → RXD del módulo | ✅ |
| 11 | IO18 | `NetU401_11` → U500-3 TXD | U1RXD del ESP32 ← TXD del módulo | ✅ |
| 12 | IO8 | — | GPIO libre | ✅ |
| 13 | IO19 | `DN_USB` (U400-4) | USB_D− | ✅ |
| 14 | IO20 | `DP_USB` (U400-6) | USB_D+ | ✅ |
| 15 | IO3 | — | Strapping JTAG; pull interno/flotante | ✅ (default) |
| 16 | IO46 | — | Strapping boot; pull-down interno | ✅ (default SPI boot) |
| 17 | IO9 | `NetR507_2` (R507 10 kΩ + U501-9 CD) | Card detect | ✅ |
| 18 | IO10 | `Net500_4` | Header 500-4 | ✅ |
| 19 | IO11 | `Net501_4` | Header 501-4 | ✅ |
| 20 | IO12 | `Net501_2` | Header 501-2 | ✅ |
| 21 | IO13 | `Net501_3` | Header 501-3 | ✅ |
| 22 | IO14 | `NetR502_1` (U101-3 INA + U501-3 CMD) | MOSI compartido RN/SD | ✅ |
| 23 | IO21 | `NetU101_4` (U101-4 INB) | **CS del RN** | ✅ |
| 24 | IO47 | `NetU101_5` (U101-5 INC + U501-5 CLK) | **CLK compartido RN/SD** | ✅ |
| 25 | IO48 | `NetR505_2` (U101-6 OUTD + U501-7 DAT0) | MISO compartido RN/SD | ✅ |
| 26 | IO45 | — | Strapping VDD_SPI; pull-down interno → 3.3 V | ✅ (default) |
| 27 | IO0 | — | Strapping boot; pull-up interno → SPI boot | ⚠️ **M8: sin botón BOOT** |
| 28 | IO35 | — | GPIO libre (N4 usa flash quad; IO35–37 disponibles) | ✅ |
| 29 | IO36 | — | GPIO libre | ✅ |
| 30 | IO37 | — | GPIO libre | ✅ |
| 31 | IO38 | `NetR503_1` (R503 10 kΩ + U501-2 CS) | **CS de la microSD** | ✅ |
| 32 | IO39 | — | GPIO libre | ✅ |
| 33 | IO40 | — | GPIO libre | ✅ |
| 34 | IO41 | — | GPIO libre | ✅ |
| 35 | IO42 | — | GPIO libre | ✅ |
| 36 | RXD0 | — | UART0 RX; no traído a header | ✅ (USB-JTAG) |
| 37 | TXD0 | — | UART0 TX; no traído a header | ✅ (USB-JTAG) |
| 38 | IO2 | — | GPIO libre | ✅ |
| 39 | IO1 | — | GPIO libre | ✅ |
| 40 | GND | `DGND` | GND | ✅ |
| 41 | GND/EPAD | `DGND` | GND | ✅ |

**Verificación del bus SPI compartido — correcto (falso positivo v1 retractado).**

| Señal | RN8302B (vía ISO7741) | microSD | GPIO | Net | Veredicto |
|---|---|---|---|---|---|
| MOSI | `INA` (3) → `OUTA` (14) → RN SDI (35) | U501-3 CMD | IO14 | `NetR502_1` | ✅ compartido |
| CLK | `INC` (5) → `OUTC` (12) → RN SCLK (33) | U501-5 CLK | IO47 | `NetU101_5` | ✅ compartido |
| CS RN | `INB` (4) → `OUTB` (13) → RN SCSN (34) | — | IO21 | `NetU101_4` | ✅ separado |
| MISO | RN SDO (32) → `IND` (11) → `OUTD` (6) | U501-7 DAT0 | IO48 | `NetR505_2` | ✅ compartido |
| CS SD | — | U501-2 CD/DAT3 | IO38 | `NetR503_1` | ✅ separado |

- El RN8302B V3 dice explícitamente: “SCSN 为高时，高阻输出” (SDO en alta impedancia cuando SCSN = 1). Por eso compartir MISO con DAT0 de la SD es seguro, siempre que el firmware no active los dos CS a la vez.
- El ISO7741 agrega ~10.7 ns; a 3.5 Mbps (periodo 286 ns) es ~3.7 %, despreciable. El modo SPI del RN (datos válidos en flanco de bajada) debe configurarse en el firmware.
- **No hay error de SPI en el esquemático.** La Revisión 1 confundió los canales B/C del ISO7741; ver Anexo B.

#### 4.4.2 USB-C (j400) y USBLC6 (U400) — pin a pin

| Pin j400 | Nombre | Net | Veredicto |
|---|---|---|---|
| 0 | SHLD | `DGND` | ✅ (directo; opcional RC/ferrita) |
| A5 | CC1 | `A5` → R401 5.1 kΩ a DGND | ✅ sink 5 V |
| B5 | CC2 | `B5` → R402 5.1 kΩ a DGND | ✅ |
| A6/B6 | DP1/DP2 | `Netj400_A6` → U400-1/6 | ✅ |
| A7/B7 | DN1/DN2 | `Netj400_A7` → U400-3/4 | ✅ |
| A4/B9, B4/A9 | VBUS | `5V_USB` | ✅; ⚠️ **M7: sin fusible/PTC** |
| A1/B12, B1/A12 | GND | `DGND` | ✅ |
| A8, B8 | SBU1/SBU2 | — | ✅ (no usados) |

| Pin U400 | Nombre | Net | Veredicto |
|---:|---|---|---|
| 1 | I/O1 | `Netj400_A6` (D+) | ✅ |
| 2 | GND | `DGND` | ✅ |
| 3 | I/O2 | `Netj400_A7` (D−) | ✅ |
| 4 | I/O2 | `DN_USB` | ✅ |
| 5 | Vbus | `5V_USB` | ✅ |
| 6 | I/O1 | `DP_USB` | ✅ |

- **H3:** el USB-C está configurado como *sink* con R401/R402 = 5.1 kΩ, lo que pide 5 V y el límite por defecto (500 mA USB 2.0 / 900 mA USB 3.x). La carga de la placa es ~1.44 A (buck + carga de supercaps); el USB no alcanza. Además, el VBUS del USB-C **no llega al buck** salvo que se instale un jumper en el header 200 (200-1 = 5V_USB, 200-2 = D202). Sin jumper, el USB solo alimenta U400 y el pin 1 del header; la placa no arranca.
- **M7:** no hay fusible/PTC en VBUS. Agregar un PTC de 1 A o un fusible.
- El USBLC6 está bien conectado; su pin 5 (Vbus) toma `5V_USB`. Si la placa se autoalimenta y el USB está desconectado, el pin 5 flota; las líneas D+/D− también están desconectadas, así que no hay problema.

#### 4.4.3 Reset, boot y strapping

| Señal | Componentes | Estado | Veredicto |
|---|---|---|---|
| EN | R400 10 kΩ a DVCC; C402 1 µF; C403 100 nF; SW400 a DGND | Reset manual y RC de power-on | ✅ |
| IO0 | — | Pull-up interno; SPI boot por defecto | ⚠️ **M8: sin botón BOOT** |
| IO3 | — | Flotante; selección de JTAG | ✅ (default) |
| IO45 | — | Pull-down interno; VDD_SPI 3.3 V | ✅ |
| IO46 | — | Pull-down interno; boot SPI | ✅ |
| RXD0/TXD0 | — | UART0 no traído a header | ✅ (USB-JTAG) |

- El módulo ESP32-S3-WROOM tiene pulls internos débiles en los strapping; el datasheet dice que los valores por defecto se determinan por esos pulls si los pines no se conectan. No es obligatorio agregar resistencias externas para el boot por defecto.
- **M8:** no hay botón BOOT en IO0. El USB-JTAG puede descargar sin él, pero si el firmware deshabilita el USB-JTAG o entra en un bucle, no hay forma física de forzar el download mode. Agregar un botón IO0→GND con pull-up 10 kΩ (o un jumper).
- **M3 (RN):** el INTN1 y el RSTN del RN no llegan al ESP32; el ESP32 no puede usar la interrupción ni resetear el RN por hardware. Si el firmware solo hace polling, es aceptable; documentarlo.

#### 4.4.4 Pasivos de `MCU` — pin a pin

| Componente | Valor | Pines / net | Veredicto |
|---|---|---|---|
| C400 | 22 µF X5R | 1 DGND, 2 DVCC | ⚠️ H6 (lado DVCC de FB400) |
| C401 | 100 nF X7R | 1 DGND, 2 DVCC | ⚠️ H6 |
| C402 | 1 µF X7R | 1 DGND, 2 EN | ✅ |
| C403 | 100 nF X7R | 1 EN, 2 DGND | ✅ |
| FB400 | 0603 6 A | 1 `NetFB400_1` (U401-2), 2 DVCC | ⚠️ H6 |
| R400 | 10 kΩ | 1 EN, 2 DVCC | ✅ |
| R401 | 5.1 kΩ | 1 A5 (CC1), 2 DGND | ✅ |
| R402 | 5.1 kΩ | 1 B5 (CC2), 2 DGND | ✅ |
| SW400 | Tactile | 1 DGND, 2 EN | ✅ |

---

### 4.5 `INTERFACES.SchDoc`

#### 4.5.1 RSM3485PCT (U500, módulo de 10 pines; el símbolo tiene 9) — pin a pin

| Pin | Nombre | Net | Requisito datasheet | Veredicto |
|---:|---|---|---|---|
| 1 | VCC | `NetC502_2` (C502 10 µF + FB500 → DVCC) | 3.15–3.45 V; 0.1 µF + 10 µF | ✅; ⚠️ **M5: C501 100 nF está del lado DVCC** |
| 2 | GND | `DGND` | GND | ✅ |
| 3 | TXD | `NetU401_11` (IO18) | Entrada UART 3.3 V | ✅ |
| 4 | RXD | `NetU401_10` (IO17) | Salida UART 3.3 V | ✅ |
| 5 | CON | `NetR500_2` (R500 10 kΩ a DVCC + IO16) | **CON = 0 → TX; CON = 1 → RX** | ✅ (reposo = RX) |
| 6 | NC | — (no está en el símbolo) | No existe/no se saca | ✅ |
| 7 | VO | — | Salida aislada 5 V; si no se usa, dejar flotante | ✅ |
| 8 | B | `B` (J500-2, D500-2, R501-1) | RS-485 B | ✅ |
| 9 | A | `A` (J500-3, D500-1, R501-2) | RS-485 A | ✅ |
| 10 | RGND | `RGND` (J500-1, D500-3) | Tierra aislada del bus | ✅ |

- **CON está bien:** el datasheet del RSM3485PCT dice que CON = 0 transmite y CON = 1 recibe (al revés de un transceptor RS-485 común). R500 a DVCC deja el módulo en **recepción** al arrancar; el ESP32 baja IO16 para transmitir. Correcto.
- **Bias interno:** el módulo trae 22 kΩ de pull-up/pull-down internos; no necesita bias externo. Con R501 = 120 Ω, el idle diferencial es ~3.3 V × 120/(22 k + 22 k + 120) ≈ **9 mV**. El umbral de recepción alta es ≥ −10 mV; 9 mV es válido pero el margen es de solo 19 mV. Con dos terminaciones de 120 Ω en el bus, baja a ~4.5 mV; sigue por encima de −10 mV, pero el margen es pequeño. → **M4**.
- **M5:** C502 (10 µF) está en el pin VCC; C501 (100 nF) está en `DVCC` antes de FB500. El 0.1 µF debe estar junto al pin 1. Mover/agregar.
- **Terminación permanente:** R501 de 120 Ω siempre conectada. Si el medidor no está en un extremo del bus, carga el bus; hacerla seleccionable con jumper. → M5.
- **Aislamiento:** RGND está separada de DGND/AGND; el módulo mantiene sus 2500 VDC. Correcto.
- **D500 SM712:** pin 1 = A, pin 2 = B, pin 3 = RGND; correcto para el TVS asimétrico de RS-485.
- **J500:** pin 1 = RGND, pin 2 = B, pin 3 = A. Correcto. No hay pin de shield/PE; el cable blindado tendría que referenciarse a RGND o a tierra en un solo punto (no implementado).

#### 4.5.2 microSD (U501) — pin a pin

| Pin | Nombre | Net | Requisito | Veredicto |
|---:|---|---|---|---|
| 1 | DAT2 | `NetR504_1` (R504 10 kΩ a DVCC) | Pull-up | ✅ |
| 2 | CD/DAT3 | `NetR503_1` (R503 10 kΩ + IO38 CS) | CS con pull-up | ✅ |
| 3 | CMD | `NetR502_1` (R502 10 kΩ + IO14 MOSI) | MOSI compartido | ✅ |
| 4 | VDD | `NetFB501_1` (FB501 → DVCC) | 3.3 V; 10 µF + 0.1 µF local | ⚠️ **H6: C500/C501 están del lado DVCC** |
| 5 | CLX/CLK | `NetU101_5` (IO47 + U101-5) | CLK compartido | ✅ |
| 6 | VSS | `DGND` | GND | ✅ |
| 7 | DAT0 | `NetR505_2` (R505 10 kΩ + IO48 MISO) | MISO compartido | ✅ |
| 8 | DAT1 | `NetR506_2` (R506 10 kΩ a DVCC) | Pull-up | ✅ |
| 9 | CD | `NetR507_2` (R507 10 kΩ + IO9) | Card detect | ✅ |
| 10 | GND/shell | `DGND` | GND | ✅ |

- **H6:** el conector no tiene capacitor local en VDD; C500 (10 µF) y C501 (100 nF) están en `DVCC`, antes de FB501. La microSD consume picos de ~200 mA al escribir; el ferrite + la inductancia de la traza pueden hacer caer VDD. Agregar 10 µF + 0.1 µF en `NetFB501_1`.
- **MISO compartido:** el RN SDO queda en alta impedancia con SCSN = 1 (datasheet V3); la SD DAT0 también. Es seguro si el firmware nunca activa los dos CS a la vez.
- **L2:** el símbolo llama `CLX` al pin 5; el datasheet dice `CLK`. Corregir el nombre en la librería (no afecta la conexión).

#### 4.5.3 Headers 500/501 (HaLow) — pin a pin

| Header | Pin | Net | Observación |
|---|---:|---|---|
| 500 | 1 | `Net500_1` (IO5) | — |
| 500 | 2 | `Net500_2` (IO6) | — |
| 500 | 3 | `Net500_3` (IO7) | — |
| 500 | 4 | `Net500_4` (IO10) | — |
| 500 | 5, 6, 7 | — | Sin conectar; documentar |
| 501 | 1 | — | Sin conectar; documentar |
| 501 | 2 | `Net501_2` (IO12) | — |
| 501 | 3 | `Net501_3` (IO13) | — |
| 501 | 4 | `Net501_4` (IO11) | — |
| 501 | 5 | `Net501_5` (FB503 → DVCC, 3.3 V) | Salida 3.3 V; sin fusible |
| 501 | 6 | `DGND` | GND |
| 501 | 7 | `Net501_7` (FB502 → `Vin_buck_5V`, 5 V) | Salida/entrada 5 V; sin fusible |

- **M9:** el módulo Quectel FGH100M **no está** en `MCU.SchDoc`; los headers son provisionales. El pinout no coincide con el header XIAO estándar (XIAO usa D0–D10 = GPIO1–GPIO11; aquí se usan IO12/IO13). Definir el mapa del módulo antes de fabricar.
- **M9b:** los pines 5 V y 3.3 V de 501 no tienen fusible/PTC; un corto en el módulo externo puede tumbar los rieles. Agregar un PTC de 0.5–1 A.
- **M9c:** 500-5/6/7 y 501-1 quedan sin conectar; si el módulo HaLow los necesita, el header no alcanza. Confirmar.

#### 4.5.4 Pasivos de `INTERFACES` — pin a pin

| Componente | Valor | Pines / net | Veredicto |
|---|---|---|---|
| C500 | 10 µF X5R | 1 DGND, 2 DVCC | ⚠️ H6 (lado DVCC de FB501) |
| C501 | 100 nF X7R | 1 DGND, 2 DVCC | ⚠️ M5/H6 |
| C502 | 10 µF X5R | 1 DGND, 2 `NetC502_2` (VCC U500) | ✅ |
| D500 | SM712 | 1 A, 2 B, 3 RGND | ✅ |
| FB500 | 0603 6 A | 1 `NetC502_2`, 2 DVCC | ✅ |
| FB501 | 0603 6 A | 1 `NetFB501_1` (U501-4), 2 DVCC | ⚠️ H6 |
| FB502 | 0603 6 A | 1 `Vin_buck_5V`, 2 `Net501_7` | ✅ |
| FB503 | 0603 6 A | 1 DVCC, 2 `Net501_5` | ✅ |
| J500 | 3 pines 5 mm | 1 RGND, 2 B, 3 A | ✅ |
| R500 | 10 kΩ | 1 DVCC, 2 `NetR500_2` (CON) | ✅ |
| R501 | 120 Ω | 1 B, 2 A | ✅; ⚠️ permanente |
| R502 | 10 kΩ | 1 `NetR502_1` (CMD), 2 DVCC | ✅ |
| R503 | 10 kΩ | 1 `NetR503_1` (CS), 2 DVCC | ✅ |
| R504 | 10 kΩ | 1 `NetR504_1` (DAT2), 2 DVCC | ✅ |
| R505 | 10 kΩ | 1 DVCC, 2 `NetR505_2` (DAT0) | ✅ |
| R506 | 10 kΩ | 1 DVCC, 2 `NetR506_2` (DAT1) | ✅ |
| R507 | 10 kΩ | 1 DVCC, 2 `NetR507_2` (CD) | ✅ |

---

### 4.6 `MAIN.SchDoc`

- Contiene los 5 sheet symbols (`THREE PHASES`, `POWER`, `MEASURES`, `MCU`, `INTERFACES`) pero **no tiene sheet entries** (`RECORD=16`). La conexión entre hojas depende de etiquetas globales/power ports.
- El netlist nuevo demuestra que las etiquetas globales funcionan (la entrada AC ya no está flotante), pero la jerarquía sigue siendo frágil: un nombre de puerto mal escrito desconecta una hoja sin que el ERC lo note. → **M10**.
- **M18:** `hardware/libraries/Library_Analizador.IntLib` no está en la raíz de `hardware/libraries/`; los `.SchDoc` referencian `Library_Analizador.IntLib`. Sin esa IntLib, `Tools → Update from Library` no funciona. Es la decisión A/B del `AGENTS.md` §9; no se tocó.
- **M22:** no hay `.PcbDoc` en el repositorio; el layout no se puede revisar.

---

## 5. Hallazgos ordenados por criticidad

> **Criterio:** Crítico = no funciona, daña un componente o viola seguridad/aislamiento. Alto = funciona mal o margen insuficiente. Medio = degrada precisión/robustez. Bajo = documentación/mejora.

### 5.1 🔴 Críticos

#### C1 — `AGND = N` es necesario para medir; el problema es que el AFE queda como primario y el HLK-5M03B perdió su aislamiento

> **Aclaración importante:** para medir tensión fase-neutro, el AGND del RN **debe** estar referenciado al neutro. Eso es correcto y **no se debe quitar**. El hallazgo no es la referencia a N, sino que el HLK-5M03B tiene su entrada AC1 y su salida −VO en el mismo net AGND, con lo que su aislamiento de 2500 VAC deja de existir, y que la placa no está diseñada como primaria (sin PE, bornera de 250 V, jacks de CT expuestos). Si se elige aislar el AFE, no basta con desconectar AGND de N: hay que cambiar los divisores a medición diferencial/aislada; si no, el RN no puede medir fase-neutro.

**Evidencia (netlist):**

- `AGND`: `U301-1`, `PS200-2` (AC2 del HLK-10M05), `PS201-1` (AC del HLK-5M03B), `PS201-3` (−VO del HLK-5M03B), `U100-6/20/29/39/42/43`, `U101-9/15`, todos los divisores y CT.
- `PS201` (HLK-5M03B) tiene **AC1 = AGND** y **−VO = AGND**. El módulo es aislado de 2500 VAC, pero al unir su entrada AC con su salida negativa, el aislamiento se bypassa.
- `U301-1` es el cuarto conductor de la bornera; por el netlist es AGND. No hay etiqueta N/L1/L2/L3.

**Consecuencia:**

- Si U301-1 es el neutro y el cableado es correcto, el AFE queda **referenciado a neutro**. Es una arquitectura válida para un medidor 3P4W, pero **no es SELV**: el RN8302B, los divisores y los jacks de CT están al potencial del neutro.
- Si el neutro se abre, o si N y L se intercambian, `AGND` puede quedar a potencial de fase a través de los divisores/HLK. Los jacks de CT (30 V/0.5 A) y el AFE quedan expuestos; la corriente de los divisores está limitada a ~0.23 mA, pero la tensión es alta y el aislamiento del jack no está especificado para red.
- El HLK-5M03B ya no aporta aislamiento; su certificación de 2500 VAC no aplica a esta conexión.

**Corrección (elegir una arquitectura):** no se trata de quitar la unión `AGND–N` (eso rompería la medición fase-neutro), sino de elegir cómo se protege ese AFE primario.

- **A) Aceptar AFE referenciado a neutro (3P4W):** usar bornera de **600 V** con etiquetas N/L1/L2/L3 y keying; agregar borne de **PE para el gabinete/shield** (no unir N y PE en la placa); tratar todo el AFE como primario; usar bornera de CT con cortocircuito (no jacks 3.5 mm); mantener creepage/clearance de 400 V; gabinete doblemente aislado o metálico con PE. Documentar que el HLK-5M03B no es una fuente aislada en esta placa. **Es la opción que mantiene la medición fase-neutro tal como está.**
- **B) Aislar el AFE:** no basta con desconectar `AGND` de N; hay que cambiar los divisores a **medición diferencial/aislada** (amplificador de aislamiento, transformador de tensión o sigma-delta aislado) y usar una fuente 3.3 V aislada dedicada para AVCC. Si solo se desconecta AGND de N, el RN deja de tener referencia y no mide fase-neutro. Es más complejo y costoso.
- **C) Fuente trifásica aislada:** alimentar los HLK desde una fuente auxiliar aislada o un transformador trifásico; mantener AGND separada de N y medir la tensión de neutro con un canal aislado.

Para el proyecto académico, la opción A es la más simple, pero **exige** cambiar la bornera, los jacks de CT, agregar PE y rotular. No se puede dejar como está.

#### C2 — Entradas de CT por jack 3.5 mm: CT abierto, sin TVS y sin cortocircuito

**Evidencia:**

- `U300/U302/U303/U304` = HX PJ-320A-3P DIP, 3.5 mm, **30 V / 0.5 A**; pines 2 y 3 al CT, pin 4 sin conectar.
- El burden (R301/R302, etc.) está en la placa, después del jack. Si se desenchufa el CT con corriente, el secundario queda **abierto**.
- No hay TVS/clamp en `NetC300_2`, `NetC301_1`, etc. El RN8302B tiene máximo diferencial ±830 mVp y absoluto ±2 V.

**Consecuencia:** un CT abierto puede generar cientos de voltios en el secundario; el jack de 30 V y el RN de 2 V no están protegidos. Es un riesgo de daño al AFE y de seguridad para el usuario. El jack de audio no es un conector de CT: se puede tirar accidentalmente.

**Corrección:**

- Reemplazar los jacks por una **bornera de CT con cortocircuito** (shorting link) o un conector que cortocircuite el secundario al desenchufar.
- Poner el burden en el conector, de modo que el CT siempre vea carga.
- Agregar TVS/BAV99/zeners en las entradas del RN (clamp a AGND/AVCC) y una resistencia serie adicional si es necesario.
- Etiquetar la polaridad del CT y usar cables con conector keyed; nunca desconectar un CT con corriente.

#### C3 — El hardware es 3P4W; el README promete 3P3W

**Evidencia:**

- Los tres divisores de tensión van de fase a **AGND/N** (R303…R308, R314…R319, R326…R331).
- Los HLK se alimentan de **fase A a neutro** (`NetF300_2` y `AGND`), con entrada 85–265 VAC.
- En 3P3W no hay neutro. Si se deja flotante, `AGND` flota y las mediciones no tienen referencia. Si se ata a una fase, los HLK ven **400 V entre fases** y se dañan; los divisores también cambian de escala.

**Consecuencia:** el instrumento no puede operar en 3P3W como dice el README. Es una promesa funcional que el hardware no cumple.

**Corrección:** quitar 3P3W de la documentación y del alcance, o agregar una fuente de alimentación trifásica y un acondicionamiento de tensión fase-fase (divisores diferenciales o transformadores). No conectar este hardware a 3P3W 400 V.

#### C4 — U301 de 250 V, sin PE y sin etiquetas de fase/neutro

**Evidencia:**

- BOM: U301 `C50126V-4P0G56`, 1×4P, 10 A, **250 V** (LCSC C49291885).
- Sistema declarado: 3P4W 230/400 V. Entre polos adyacentes de U301 hay 400 V (L-L), no 230 V.
- No hay borne de PE; los MOV RV300–RV302 y los HLK referencian a neutro.
- El esquemático no rotula N/L1/L2/L3; U301-1 es AGND por netlist.

**Consecuencia:** la bornera puede no soportar 400 V entre polos; si se invierte N/L, AGND queda vivo; si el gabinete es metálico y no hay PE, puede quedar flotante. Es un problema de seguridad y de cumplimiento.

**Corrección:** usar bornera de **600 V** (o mayor) con separación entre polos; agregar borne de PE; rotular N/L1/L2/L3 y usar keying; verificar creepage/clearance de 400 V; usar fusibles de 500 V si se mantiene la tensión L-L. Revisar el símbolo `BR_...` (parece un puente rectificador, pero es una bornera). **No confundir N con PE:** el neutro es un conductor de corriente; el PE es protección. No unir N y PE en la placa (salvo una instalación TN-C/PEN diseñada para eso); el borne de PE va al gabinete/shield, no al retorno de neutro.

#### C5 — F300 de 200 mA compartido por los dos HLK

**Evidencia:**

- `F300` = JFC2410-0200TS, **200 mA / 250 V, time-lag**; alimenta `PS200-1` y `PS201-2` (ambos HLK) y el divisor A.
- HLK-10M05 y HLK-5M03B datasheets: “外接保险丝推荐 **1A/250Vac** 或者 10Ω 的线绕电阻，慢熔断”; inrush ≤10 A; max input current ≤0.2 A cada uno.
- El HLK-10M05 a plena carga (1.44 A × 5 V ≈ 7.2 W) consume ~100–140 mA a 85 V; el HLK-5M03B suma poco, pero el inrush de ambos puede abrir un fusible de 200 mA.

**Consecuencia:** F300 puede abrirse en el arranque o a baja línea; se pierde la alimentación de los dos HLK y del divisor A. La placa queda muerta aunque el resto de fases esté presente.

**Corrección:** usar **1 A slow-blow** por HLK (recomendación del datasheet) o un fusible de 1.5–2 A slow-blow para ambos; separar el fusible del divisor (F301/F302 pueden ser de 50 mA o mantenerse). Coordinar con el MOV (M17) y verificar la tensión de interrupción.

#### C6 — El banco de desacople del RN8302B está desconectado (FB100)

**Evidencia (netlist):**

```
NetC101_2: C101-2, C102-2, C103-2, C104-2, C105-2, C109-2, FB100-1
AVCC_3v3:  C203-1, FB100-2, PS201-4, R100-2, R102-1, R103-2, R104-2,
           U100-9, U100-28, U100-40, U100-41, U101-16
```

`NetC101_2` no tiene ningún pin de U100. El banco de 1 µF + 100 nF + 2×10 µF + 100 nF + 100 nF queda colgando de FB100, sin carga. Los pines 9/28/40 del RN están en `AVCC_3v3`, del otro lado del ferrite.

**Consecuencia:** el RN8302B solo tiene C203 (4.7 µF) en la hoja POWER, lejos; no tiene los 0.1 µF locales que el datasheet exige en AVCC y DVCC. Es un error de conexión, no solo de layout; el AFE puede funcionar pero con peor ruido/precisión y más EMI.

**Corrección:** mover los pines 9/28/40 del RN a `NetC101_2` y dejar FB100 entre `AVCC_3v3` y `NetC101_2`; o eliminar FB100 y conectar el banco directamente a `AVCC_3v3`. Agregar 0.1 µF junto a cada pin de AVCC/DVCC. Verificar que C101–C105/C109 queden en el lado del RN, no del lado de la fuente.

#### C7 — El SY6280 no es un cargador de supercaps: 3.8 W en SOT-23-5

**Evidencia:**

- U200 SY6280AAC: OUT → `NetC201_1` (banco de 15 F), IN → `Vin_buck_5V` (~4.6 V), ISET → R201 8.2 kΩ (0.83 A).
- Datasheet: SOT-23-5, PD 0.6 W @ 25 °C, θJA 200 °C/W, thermal shutdown 130 °C.
- Al inicio de la carga, Vout ≈ 0 V, Vin ≈ 4.6 V, I = 0.83 A → P = 3.8 W. El pass FET entra en límite de corriente y disipa la diferencia.

**Consecuencia:** thermal shutdown; la carga de los supercaps se vuelve intermitente (hiccup). El banco puede tardar mucho en cargarse o no alcanzar la tensión de respaldo antes de un corte. Es un uso indebido del load switch.

**Corrección:** usar un **cargador de supercaps dedicado** (con regulación de corriente y thermal foldback), o una resistencia/inductor serie que reparta la disipación, o cargar a una corriente mucho menor (p. ej. 100 mA) con un resistor adecuado. Agregar 1 µF + 10 µF en OUT; el datasheet también lo pide. No aumentar R201 para “resolver” el respaldo: el problema es la disipación, no solo el límite.

#### C8 — Los exports del BOM están viejos y tienen MPN incorrectos

**Evidencia:**

- `Analizador_trifasico_IoT_pcb.csv` y `.xlsx`: **31/10/2026 22:59**.
- `.BomDoc`: **01/11/2026 06:17**, con part choices corregidos (R201 FOJAN 8.2 kΩ, R303 Yageo 165 kΩ 0.1 %, etc.).
- El CSV todavía tiene:
  - C102/C104/C105/C107/C204/**C501** (100 nF) → `HGC0603G0150J500NTHJ` (**15 pF**).
  - C103/C106/C200/C208/C500/C502 (10 µF) → `RT0603BRD07165KL` (**165 kΩ**).
  - C205/C206/C400 (22 µF) → `049SS2-8.192F12DZLAL` (**cristal 8.192 MHz**).
- El CSV es el que usa el ensamblador; el `.BomDoc` no se envía a fábrica.

**Consecuencia:** el ensamblador coloca 15 pF donde van 100 nF, 165 kΩ donde van 10 µF, etc. La placa no funciona.

**Corrección:** reexportar el BOM desde Altium (BomDoc) y verificar **cada línea** contra el valor del esquemático; actualizar los comentarios de librería (R201 dice 10 Ω, R303 dice Bourns 1 %, etc.) para que el export no vuelva a confundir. Revisar también U301 (250 V), F300 (200 mA) y el jack HX (30 V) en el BOM.

---

### 5.2 🟠 Altos

#### H1 — D200/D201/D202: 2 A en SOD-323 y caída que reduce el respaldo

- D200 conduce la carga completa del buck (~1.44 A): Vf ≈ 0.45 V → **0.65 W**. D201 conduce el backup (~0.8 A) → **0.36 W**. D202 conduce USB/header (~0.5 A) → **0.25 W**.
- MS2A40LWS es de 2 A y SOD-323; θJA típica 250–300 °C/W. D200 supera 125 °C de unión.
- **Corrección:** usar SMA/SMB de 3 A (o dos diodos en paralelo con reparto), o un ideal diode/PMOS. Verificar la temperatura en placa.

#### H2 — La energía real del *last gasp* es ~6 s, no 9 s

- El banco se carga a `Vin_buck_5V` menos la caída de U200 (~4.5–4.6 V). Durante el respaldo, D201 cae ~0.45 V; el AP63203 necesita ~3.8 V de entrada para mantener 3.3 V. El supercap solo entrega desde ~4.6 V hasta ~4.25 V.
- Energía útil: 0.5 × 15 F × (4.6² − 4.25²) ≈ **23 J**; a 3.2 W / 0.9 ≈ **6.4 s**. La cifra de 9 s del README es optimista.
- **Corrección:** usar un ideal diode/PMOS en lugar de D201, o un buck con menor dropout, o cargar el banco a 5.0 V (eliminar la caída de D200 con un ideal diode). Verificar el tiempo real con la carga de *last gasp*.

#### H3 — USB-C y header 200 no alimentan la placa como se cree

- El USB-C está configurado como sink (R401/R402 5.1 kΩ), pero el VBUS **no llega al buck** salvo que se instale un jumper en el header 200 (200-1 = 5V_USB, 200-2 = D202). Sin jumper, el USB solo alimenta U400 y el pin 1 del header; la placa no arranca.
- Aun con jumper, el USB 2.0 pide 500 mA; la carga es ~1.44 A. El USB no alcanza.
- **Corrección:** usar el header 501-7/6 para una entrada externa de 5 V, o un controlador PD que negocie 1.5–3 A, o limitar la carga cuando `5V_USB` esté presente. Documentar que el header 200 es un jumper, no una entrada con GND.

#### H4 — Los dos HLK cuelgan de la fase A

- `PS200-1` y `PS201-2` comparten `NetF300_2`; si se pierde L1, se apagan los dos HLK, el divisor A y la placa completa. El respaldo solo mantiene el riel digital; el riel analógico (AVCC) se cae con el HLK-5M03B.
- **Corrección:** alimentar los HLK desde dos o tres fases (OR-ing de fuentes o una fuente trifásica), o al menos desde fases distintas; agregar detección de fase perdida. Para un analizador trifásico, la pérdida de una fase no debería apagar el instrumento.

#### H5 — Falta 0.1 µF local en VCC1/VCC2 del ISO7741

- C500/C501 están en `DVCC` (INTERFACES) y C203 en `AVCC` (POWER); no hay 0.1 µF junto a U101-1 (VCC1) ni U101-16 (VCC2).
- El ISO7741 es un aislador de alta velocidad; el datasheet pide bypass de 0.1 µF en cada lado. Sin él, puede haber jitter/EMI o fallos en los flancos.
- **Corrección:** agregar 0.1 µF de VCC1 a DGND (pin 1–2) y de VCC2 a AGND (pin 16–15), lo más cerca posible.

#### H6 — Desacople local del ESP32 y de la microSD en el lado equivocado del ferrite

- ESP32: U401-2 (`3V3`) → FB400 → DVCC; C400 (22 µF) y C401 (100 nF) están en DVCC, no en el pin del módulo. El datasheet del módulo recomienda 22 µF + 0.1 µF en 3V3.
- microSD: U501-4 (`VDD`) → FB501 → DVCC; C500/C501 están en DVCC, no en el conector. La SD consume picos de ~200 mA al escribir.
- **Corrección:** agregar 10 µF + 0.1 µF en `NetFB400_1` (lado módulo) y 10 µF + 0.1 µF en `NetFB501_1` (lado conector), o eliminar los ferrites si no son necesarios.

#### H7 — Precisión y protección del frente analógico

- **1 kΩ 1 % / 100 ppm** como resistor inferior del divisor, frente a 165 kΩ 0.1 % / 25 ppm: la deriva térmica del 1 kΩ domina. Usar 0.1 % / 25 ppm.
- **33 nF X7R 5 %** en los filtros de tensión y corriente: el coeficiente de tensión/temperatura y la distorsión dieléctrica afectan fase/ganancia. Usar C0G/NP0 1 %.
- **165 kΩ 0603 75 V**: a 230 V L-N cada uno ve ~38 V (OK), pero con el MOV clampando a ~775 V ve ~129 V; a 400 V L-N ve ~67 V. Usar 0805/1206 o más resistencias en serie.
- **Ratio 990k/1k**: a 230 V da 0.656 Vpp; a 277 V, 0.790 Vpp; a 300 V clipea. El máximo medible es ~280 Vrms. Para 230 V L-N está bien; para 400 V L-N no.
- **Corrección:** definir la clase de precisión (0.5S/1S) y ajustar los componentes; si no se necesita 400 V L-N, documentar el rango de 230 V.

#### H8 — Falta el filtro EMI de entrada de los HLK

- Los datasheets de HLK recomiendan, para EMC: fusible 1 A slow-blow, MOV 10D561K, capacitor X 0.1 µF/275 VAC y inductor de modo común. La placa solo tiene fusibles de 200 mA y MOV 14D471K; no hay X cap ni choke.
- **Consecuencia:** las emisiones conducidas de los HLK pueden exceder los límites; el instrumento puede fallar EMC.
- **Corrección:** agregar un filtro de entrada (X2 0.1 µF/275 VAC + CM choke) antes de los HLK, y/o usar un módulo/filtro certificado. Verificar con pre-escaneo EMC.

#### H9 — La huella de U100 se llama `3`; verificar que sea el LQFP-44

- Netlist: `U100` tiene `Footprint = 3`. En `PcbLib1.PcbLib` existe un patrón llamado `3` (35 KB, área no nula), pero la descripción está vacía y el nombre no es descriptivo.
- No hay `.PcbDoc` en el repositorio, así que no se puede confirmar que `3` sea el LQFP-44 correcto.
- **Corrección:** abrir la librería, verificar que el patrón `3` tenga 44 pads con el pin 1 en la esquina correcta, renombrarlo a `LQFP-44_10x10_P0.8` y actualizar el símbolo/PCB. Si no es el LQFP-44, el layout será imposible.

#### H10 — No hay señal de *power fail* para el *last gasp*

- No hay comparador, ADC ni GPIO monitoreando `Vin_buck_5V`/`Vout_5V`. El ESP32 no sabe cuándo empieza el respaldo hasta que el riel de 3.3 V cae; para entonces puede ser tarde para guardar contadores/notificar.
- **Corrección:** agregar un divisor + comparador (o ADC) desde `Vin_buck_5V` a un GPIO, con histéresis; o usar el PGOOD/UVLO del buck si está disponible. Probar el tiempo de detección vs el tiempo de respaldo.

---

### 5.3 🟡 Medios

| ID | Hallazgo | Evidencia | Corrección |
|---|---|---|---|
| M1 | **U100-21 (NC) flotante** | El datasheet V3 dice “NC 管脚，接模拟地” (NC, conectar a AGND). | Conectar U100-21 a AGND. |
| M2 | **REFV 10 µF vs 1 µF; VO 10 µF vs 4.7 µF; RC a AGND** | C110 = 10 µF; C106 = 10 µF; U100-43 = AGND. El datasheet pide 1 µF/4.7 µF y RC a DGND. | Cambiar C110 a 1 µF; C106 a 4.7 µF; llevar RC al nodo DGND (hoy AGND = DGND en el chip, pero el layout debe distinguirlos). |
| M3 | **INTN1/RSTN del RN no llegan al ESP32** | U100-31 solo R102 10 kΩ a AVCC; U100-27 solo R103 1 kΩ a AVCC. | Conectar INTN1 a un GPIO (requiere otro canal aislado o usar el ISO7741 con canales libres; no hay) o documentar que se usa polling. RSTN puede quedar con pull-up si no se necesita reset por hardware. |
| M4 | **Bias RS-485 marginal con 120 Ω** | RSM3485PCT tiene 22 kΩ internos; con R501 120 Ω el idle es ~9 mV; el umbral alto es ≥ −10 mV. | Verificar el margen; agregar bias externo de 560 Ω a 3.3 V/GND si el bus es largo, o quitar la terminación en nodos intermedios. |
| M5 | **C501 100 nF en el lado DVCC; R501 siempre conectada** | C501 está antes de FB500; R501 120 Ω fija entre A/B. | Mover/agregar 0.1 µF en U500-1; hacer R501 seleccionable con jumper. |
| M6 | **Faltan 0.1 µF en las salidas de los HLK** | C200 10 µF después de D200; C203 4.7 µF en AVCC; no hay 0.1 µF en Vout_5V/AVCC. | Agregar 10 µF + 0.1 µF en Vout_5V y 0.1 µF en AVCC; el datasheet de los HLK lo recomienda. |
| M7 | **Sin fusible/PTC en VBUS y sin ESD en CC/SBU** | j400 VBUS directo a 5V_USB; U400 solo protege D+/D−. | Agregar PTC 1 A en VBUS; ESD en CC/SBU si el conector es accesible. |
| M8 | **Sin botón BOOT en IO0** | IO0 solo tiene el pull-up interno. | Agregar botón IO0→GND con pull-up 10 kΩ o jumper; útil para recuperación. |
| M9 | **Headers HaLow provisionales; 5 V/3.3 V sin fusible** | FGH100M no está en MCU; 500-5/6/7 y 501-1 sin conectar; 501-5/7 salen sin protección. | Definir el pinout del FGH100M; agregar PTC en 501-5/7; confirmar que los pines no usados no floten en el módulo. |
| M10 | **MAIN sin sheet entries** | `MAIN.SchDoc` solo tiene sheet symbols; la conexión es por etiquetas globales. | Agregar puertos/sheet entries para las señales inter-hoja, o documentar formalmente las etiquetas globales y revisar el ERC. |
| M11 | **Margen de sobretensión de los supercaps** | 2×2.7 V = 5.4 V; con 5.25 V USB y D200/D202, el banco puede llegar a ~4.9–5.0 V (2.45–2.5 V por cap); margen 0.2–0.25 V. | Agregar clamp/TVS de 5.1 V o verificar la tensión máxima de la fuente; el balanceo 1 kΩ ya está. |
| M12 | **Descarga de 150 Ω del SY6280 durante el respaldo** | El SY6280 descarga OUT con 150 Ω al apagarse; a 4.6 V son ~31 mA. | Aceptar (~3 % del respaldo) o usar un load switch sin descarga; documentar. |
| M13 | **Modelo de CT/Rogowski indefinido** | Burden 20 Ω; el README dice 150 mVpp, pero el RN admite 830 mVp; no hay CT definido. | Definir relación, clase, carga y burden; recalcular la señal máxima. Un CT 100 A/20 mA con 20 Ω da 1.13 Vpp (excede); 100 A/10 mA da 0.566 Vpp (OK). |
| M14 | **Mapeo de fases/polaridad sin documentar** | No hay etiquetas L1/L2/L3 ni correspondencia U300/U302/U303 ↔ VAP/VBP/VCP. | Etiquetar y documentar; verificar en el layout y en la calibración. |
| M15 | **Símbolo `BR_...` y README confunden U301 con un puente rectificador** | U301 es una bornera 1×4P; el README dice “puente rectificador”. | Renombrar el símbolo a `CONN_4P_5mm` y corregir el README; los HLK ya rectifican. |
| M16 | **Comentarios de librería obsoletos** | R201 comenta `HP05W3F100JT5E` (10 Ω) pero el valor/MPN es 8.2 kΩ; R303 comenta Bourns 1 % pero el MPN es Yageo 0.1 %. | Actualizar los comentarios para que el export del BOM no confunda. |
| M17 | **MOV después del fusible** | RV300–RV302 están en `NetF300_2`/`NetF301_2`/`NetF302_2`, después de F300–F302. | Coordinar MOV/fusible; mover el MOV antes del fusible o usar un fusible con capacidad de pulso. |
| M18 | **`Library_Analizador.IntLib` ausente** | `hardware/libraries/` no tiene la IntLib; los `.SchDoc` la referencian. | Decidir A/B del AGENTS.md §9; si se restaura, recompilar y copiar a la raíz. |
| M19 | **Sin test points** | No hay TP en 5V, DVCC, AVCC, AGND, DGND, SPI, UART, RESET. | Agregar test points para bring-up y diagnóstico. |
| M20 | **Huellas `R0805` para capacitores de 0805; D200 “duplicate”** | C103/C104/C106/C110/C200/C205/C206/C208/C400/C500/C502 usan `R0805`; D200 usa `SOD-323... - duplicate`. | Verificar el land pattern (es 0805, pero el nombre es de resistor); renombrar a `C0805` y limpiar la huella duplicada. |

### 5.4 🟢 Bajos

| ID | Hallazgo | Corrección |
|---|---|---|
| L1 | El símbolo de la TF card llama `CLX` al pin 5; los jacks tienen pines numéricos 2/3/4; U301 se llama `BR_...`. | Corregir nombres en `Schlib1.SchLib` (sin cambiar números de pin). |
| L2 | Los CF1–CF5 y el INTN1 del RN no se usan. | Documentar que no se usan; si se necesita pulso/interrupción, agregar el circuito. |
| L3 | No hay ESD en los jacks de CT ni en CC/SBU del USB-C. | Agregar TVS/ESD si el entorno lo requiere (ver C2/M7). |
| L4 | No hay test points ni puntos de medida en los rieles. | Agregar TP (ver M19). |
| L5 | Varios capacitores usan huella `R0805`. | Renombrar/verificar (ver M20). |
| L6 | El footprint de D200 incluye “- duplicate”. | Limpiar la biblioteca. |
| L7 | 500-5/6/7 y 501-1 sin conectar. | Documentar el pinout o conectar según el módulo HaLow. |
| L8 | El BOM dice `LSCS` en vez de `LCSC` en C101. | Corregir el proveedor. |

---

## 6. Cálculos de verificación

### 6.1 Presupuesto de corriente

**Riel DVCC 3.3 V (salida del AP63203):**

| Carga | Típico | Máximo | Nota |
|---|---:|---:|---|
| ESP32-S3-WROOM-1 | 250 mA | 500 mA | Pico Wi-Fi TX |
| microSD | 50 mA | 200 mA | Escritura |
| RSM3485PCT | 30 mA | 130 mA | Datasheet |
| ISO7741 lado 1 | 3 mA | 5.2 mA | 3.5 Mbps |
| USBLC6 | <1 mA | <1 mA | — |
| **Total sin HaLow** | **~283 mA** | **~836 mA** | — |
| AP63203 | — | 2 000 mA | Margen 58 % |

**Riel AVCC 3.3 V (salida del HLK-5M03B):**

| Carga | Máximo | Nota |
|---|---:|---|
| RN8302B | 4.4 mA | EMM |
| ISO7741 lado 2 | 5.7 mA | 3.5 Mbps |
| Divisores de tensión | 0.7 mA | 3 × 0.23 mA |
| **Total** | **~11 mA** | HLK-5M03B 1.5 A; margen enorme |

**Riel de 5 V (salida del HLK-10M05 / USB):**

| Carga | Sin HaLow | Con HaLow |
|---|---:|---:|
| Entrada del buck (3.3 V/5 V, η=0.9) | 613 mA | 870 mA |
| Carga de supercaps (SY6280) | 830 mA | 830 mA |
| **Total** | **1 443 mA** | **1 700 mA** |
| HLK-10M05 | 2 000 mA | 2 000 mA |
| Margen | 557 mA (28 %) | 300 mA (15 %) |

**Corriente de entrada de los HLK:**

- HLK-10M05 a 1.44 A × 5 V = 7.2 W; η ≈ 0.8; a 85 V: 7.2/(0.8×85) ≈ **106 mA**.
- HLK-5M03B a 11 mA × 3.3 V = 36 mW; η ≈ 0.75; a 85 V: **~0.6 mA**.
- Total ≈ **107 mA** < 200 mA (F300) en régimen, pero el inrush de ambos es ≤10 A y el fusible recomendado es 1 A slow-blow. **C5.**

**USB-C:** 500 mA (USB 2.0) o 900 mA (USB 3.x) < 1.44 A. **H3.**

### 6.2 Divisor de tensión

- Rtop = 6 × 165 kΩ = **990 kΩ**; Rbottom = **1 kΩ**.
- Ratio = 1 kΩ / (990 kΩ + 1 kΩ) = **1.009×10⁻³**.
- 230 Vrms → 232 mVrms = **0.656 Vpp**.
- 277 Vrms → 280 mVrms = **0.790 Vpp** (cerca del límite de 0.8 Vpp).
- 300 Vrms → 303 mVrms = **0.856 Vpp** (clipea).
- Máximo medible ≈ **280 Vrms**.
- Corriente: 230 V / 991 kΩ = **232 µA**.
- Potencia por 165 kΩ: (232 µA)² × 165 kΩ = **8.9 mW** (<100 mW).
- Potencia en 1 kΩ: **54 µW**.
- Filtro: fc = 1/(2π·(990 kΩ || 1 kΩ)·33 nF) ≈ **4.8 kHz**; desfase a 50 Hz ≈ **0.6°**.
- **Precisión:** el 1 kΩ 1 %/100 ppm domina la deriva; usar 0.1 %/25 ppm. Los 33 nF X7R 5 % afectan fase; usar C0G 1 %.
- **Tensión:** los 165 kΩ 0603 de 75 V ven ~38 V a 230 V, pero ~129 V con el clamp del MOV a 775 V; usar 0805/1206 o más en serie.

### 6.3 Entradas de corriente

- Burden diferencial = 10 Ω + 10 Ω = **20 Ω**.
- Vmax = 0.83 Vp → Ipk = 41.5 mA → **29.3 mA rms**.
- Para un CT 100 A/20 mA: a 100 A, 20 mA × 20 Ω = 0.4 Vrms = **1.13 Vpp** → excede el RN (0.83 Vp).
- Para un CT 100 A/10 mA: 0.2 Vrms = **0.566 Vpp** → OK.
- Para un CT 100 A/5 A: imposible; se requiere CT de baja corriente o Rogowski con integrador.
- Potencia en cada burden a 20 mA: (20 mA)² × 10 Ω = **4 mW** (<333 mW).
- Filtro: fc ≈ 1/(2π·(1 kΩ+10 Ω)·33 nF) ≈ **4.8 kHz**; desfase a 50 Hz ≈ **0.6°**.

### 6.4 Energía del respaldo (corregida)

| Supuesto | Valor |
|---|---:|
| Banco | 2 × 30 F en serie = **15 F** |
| Tensión de carga (5 V HLK − D200 − U200) | ~**4.5–4.6 V** |
| Caída de D201 durante backup | ~**0.45 V** |
| VIN mínimo del AP63203 para 3.3 V | ~**3.8 V** |
| Tensión mínima del supercap para regular | ~**4.25 V** |
| Energía útil (4.6 → 4.25 V) | **~23 J** |
| Tiempo a 3.2 W / η 0.9 | **~6.4 s** |
| Si se usa ideal diode (4.6 → 3.8 V) | ~38 J, **~10.8 s** |
| Si se carga a 4.9 V y ideal diode | ~45 J, **~12.5 s** |

**Conclusión:** la cifra de 9 s del README es alcanzable solo con un ideal diode o una carga menor; con D201 y 3.2 W, el tiempo real es ~6 s. **H2.**

### 6.5 Térmica del SY6280

- P = (Vin − Vout) × Ilim. Peor caso: (4.6 − 0) × 0.83 = **3.8 W**.
- SOT-23-5: PD 0.6 W @ 25 °C, θJA 200 °C/W, TSD 130 °C.
- ΔT = 3.8 × 200 = **760 °C** (teórico); el thermal shutdown actúa mucho antes. La carga se vuelve hiccup.
- Incluso a Vout = 3 V: P = 1.6 × 0.83 = **1.33 W**, ΔT = 266 °C. Sigue siendo demasiado.
- Tiempo ideal de carga: 15 F × 4.6 V / 0.83 A ≈ **83 s**; con hiccup, más. **C7.**

### 6.6 Térmica de D200/D201/D202

- D200: P = 0.45 V × 1.44 A ≈ **0.65 W**; θJA 250–300 °C/W → ΔT 162–195 °C; Tj > 125 °C.
- D201: P = 0.45 V × 0.8 A ≈ **0.36 W**; ΔT 90–108 °C; Tj cercana a 125 °C.
- D202: P = 0.4 V × 0.5 A ≈ **0.20 W**; ΔT 50–60 °C; aceptable pero caliente.
- **Conclusión:** D200 es el más crítico; usar SMA/SMB de 3 A o ideal diode. **H1.**

### 6.7 Fusibles y coordinación

- HLK-10M05/5M03B: fusible recomendado **1 A/250 VAC slow-blow** o 10 Ω wirewound; inrush ≤10 A.
- F300 actual: **200 mA time-lag**. A 200 % (400 mA) abre en ≤60 s; a 1000 % (2 A) abre en ≥10 ms. El inrush de 10 A puede abrirlo.
- F301/F302: 200 mA para divisores de 0.23 mA; sobredimensionados, pero no dañan. Pueden ser 50 mA.
- MOV después del fusible: un pico de 4.5 kA puede abrir F300 antes de que el MOV actúe; coordinar. **C5/M17.**

### 6.8 Aislamiento

| Barrera | Componente | Valor | Observación |
|---|---|---|---|
| AGND ↔ DGND | HLK-10M05 | 3000 VAC | Es la barrera principal; el ISO7741 también aísla. |
| AGND ↔ DGND | ISO7741 | 5000 Vrms | Refuerza la barrera; el creepage del PCB es crítico. |
| DGND ↔ RGND | RSM3485PCT | 2500 VDC | Correcto; RGND separada. |
| AGND ↔ tierra | **No hay** | — | No hay PE; el gabinete debe ser doblemente aislado o llevar PE. **C4.** |
| AGND ↔ neutro | **Unida** | 0 V | Decisión de arquitectura; no es SELV. **C1.** |

---

## 7. Auditoría del BOM

### 7.1 Estado de los archivos

| Archivo | Fecha | Estado |
|---|---|---|
| `Analizador_trifasico_IoT_pcb.BomDoc` | 01/11/2026 06:17 | Corregido; contiene los part choices buenos (R201 8.2 kΩ, R303 165 kΩ 0.1 %, etc.). |
| `Analizador_trifasico_IoT_pcb.csv` | 31/10/2026 22:59 | **Viejo**; MPN incorrectos. |
| `Analizador_trifasico_IoT_pcb.xlsx` | 31/10/2026 22:59 | **Viejo**; mismo problema. |

### 7.2 MPN que no coinciden con el valor (CSV viejo)

| Designador(es) | Valor según descripción | MPN en el CSV | Qué se colocaría | Criticidad |
|---|---|---|---|---|
| C102, C104, C105, C107, C204, C501 | 100 nF | `HGC0603G0150J500NTHJ` | 15 pF | 🔴 |
| C103, C106, C200, C208, C500, C502 | 10 µF | `RT0603BRD07165KL` | 165 kΩ | 🔴 |
| C205, C206, C400 | 22 µF | `049SS2-8.192F12DZLAL` | Cristal 8.192 MHz | 🔴 |

**Corrección:** reexportar desde el `.BomDoc`; verificar cada línea. El `.BomDoc` ya tiene los part choices correctos para R201/R303, pero el CSV no se ha regenerado.

### 7.3 Piezas con rating insuficiente o por verificar

| Designador | Pieza | Rating | Problema |
|---|---|---|---|
| U301 | C50126V-4P0G56 | **250 V**, 10 A | 400 V entre fases; **C4** |
| F300–F302 | JFC2410-0200TS | **200 mA**, 250 V | HLK recomienda 1 A; **C5** |
| U300/U302/U303/U304 | HX PJ-320A-3P | **30 V**, 0.5 A | CT abierto; **C2** |
| D200–D202 | MS2A40LWS | 2 A, SOD-323 | Térmica; **H1** |
| R303–R331 | 165 kΩ 0603 | 75 V | 129 V con clamp; **H7** |
| RV300–RV302 | MOV-14D471K | 385 V MCOV | OK para 230 V L-N; no para 400 V L-N |
| U100 | RN8302B | LQFP-44 | Huella `3` por verificar; **H9** |

### 7.4 Observaciones generales

- El BOM es plano (una fila por designador); para comprar, agrupar por valor y sumar cantidades.
- Faltan precios/proveedor en muchas líneas; no es bloqueante, pero complica la compra.
- Los conectores 200/500/501 están en stock (según `AGENTS.md`); no requieren MPN.
- Varios capacitores de 0805 usan la huella llamada `R0805`; el land pattern es 0805, pero el nombre es de resistor. Verificar y renombrar.
- El BOM de D500 es SM712 (FUXINSEMI); el símbolo/part choice es correcto. La descripción del catálogo dice “bidirectional 7 V”, pero el MPN es SM712; verificar que el proveedor entregue el asimétrico 7 V/12 V.

---

## 8. Checklist para el layout (no revisado: no hay `.PcbDoc`)

1. **Creepage/clearance de red:** U301, F300–F302, RV300–RV302, primario de los HLK. Para 400 V L-L, mínimo 8 mm entre polos y 6 mm a partes accesibles; usar ranuras si hace falta.
2. **Barrera AGND/DGND:** el ISO7741 es el único puente; no rutear AGND y DGND bajo el cuerpo del ISO7741; mantener >8 mm de creepage. Lo mismo para la barrera del HLK-10M05 y del RSM3485 (RGND).
3. **Estrella de AGND:** U301-1 es el punto de unión de neutro, HLK, MOV y AFE. Las corrientes de entrada de los HLK y de los MOV **no** deben pasar por el plano de AGND del RN; llevar un return de potencia separado y unirlo en U301-1.
4. **CT:** trazas diferenciales cortas y apareadas, lejos de las fases y del buck; guard rings; no pasar por debajo de los jacks; burden junto al conector; TVS junto al RN.
5. **Cristal:** X100 y C100/C108 junto al RN; sin trazas debajo; guard ring; no rutear SPI cerca.
6. **Buck:** C207/C208 junto a VIN/GND; L200 junto a SW; C205/C206/C400 junto a la salida; lazo de conmutación mínimo; SW con cobre corto.
7. **Supercaps:** trazas de alta corriente cortas y anchas; R200/R202 junto a los caps; térmica del SY6280; no rutear el nodo de 15 F cerca de AGND sensible.
8. **USB:** D+/D− como par de 90 Ω; USBLC6 junto al conector; VBUS con PTC; CC cortos a R401/R402.
9. **Antena ESP32:** keepout de la antena; no cobre, ni plano, ni componentes bajo la antena; el módulo en el borde.
10. **Térmica:** D200/D201/D202 con cobre; SY6280 con cobre y vías; AP63203 con cobre en SW/VIN; HLK con separación.
11. **Test points:** 5V, DVCC, AVCC, AGND, DGND, REFV, VO, SPI (CLK/MOSI/MISO/CS), UART, EN, RESET del RN.
12. **Headers:** 500/501 con pines 1 marcados; 5V/3.3V con PTC; no dejar pines flotantes en el módulo HaLow.

---

## 9. Verificación recomendada antes de fabricar

### 9.1 En Altium (lo debe hacer el humano)

1. Decidir la arquitectura de C1 (AGND = N con seguridad, o AFE aislado).
2. Corregir, como mínimo, C1–C8 y H1–H3:
   - Cambiar U301 por bornera de 600 V, agregar PE y etiquetas N/L1/L2/L3.
   - Reemplazar los jacks de CT por bornera con cortocircuito; agregar TVS.
   - Cambiar F300 por 1 A slow-blow (o separar fusibles).
   - Corregir FB100/NetC101_2 y agregar 0.1 µF en AVCC/DVCC del RN.
   - Reemplazar el SY6280 por un cargador de supercaps adecuado.
   - Reexportar el BOM y verificar cada línea.
3. Recompilar (`Project → Compile Project`) y revisar `Messages`/ERC.
4. Reexportar el netlist y el BOM; comparar contra este informe.
5. Verificar la huella `3` de U100 (LQFP-44) y actualizar la librería.
6. Revisar el layout con el checklist §8.

### 9.2 En laboratorio (con fuente limitada, sin 230 V al principio)

1. **No conectar 230 V** hasta resolver C1/C2/C4. Alimentar con 5 V limitada a 1 A por el header 501-7/6 (no por el 200, que es jumper) o por una fuente de laboratorio.
2. Medir DVCC = 3.3 V, AVCC = 3.3 V, REFV = 1.25 V, VO = valor del datasheet; verificar que el RN no se caliente.
3. Verificar aislamiento: con la placa apagada, medir resistencia entre AGND y DGND; debe ser >1 GΩ (solo el HLK-10M05/ISO7741). Si es baja, hay un corto o un componente mal colocado.
4. Comunicar con el RN por SPI a 1 MHz y luego 3.5 MHz; leer el `DeviceID` (0x830200) y registros de versión.
5. Leer/escribir la microSD con el RN deseleccionado; verificar que no haya contención en MISO (RN SDO alta impedancia).
6. Probar RS-485 a 9600 bps: CON en recepción/transmisión, terminación 120 Ω, bias interno; verificar A/B y el aislamiento de RGND.
7. Verificar USB-C: enumeración, D+/D−, CC, y que el riel de 5 V no caiga al transmitir Wi-Fi.
8. Probar las entradas de CT con una fuente de corriente alterna de baja tensión y un CT de prueba; verificar burden, filtro y linealidad; **nunca** abrir el CT con corriente.
9. Medir la carga de los supercaps: tiempo, temperatura del SY6280 (o del cargador nuevo), y el tiempo real de *last gasp* a 3.2 W.
10. Agregar/verificar la señal de *power fail* (H10) y el tiempo de detección.

### 9.3 Seguridad

- No conectar 230/400 V sin gabinete, PE y bornera de 600 V.
- Tratar AGND como primaria: no tocar los jacks de CT ni el AFE durante la operación.
- Usar fuente aislada y limitada para las primeras pruebas.
- Verificar hipot entre primario y secundario (HLK-10M05, ISO7741, RSM3485) según los ratings, con el equipo adecuado.

---

## Anexo A — Evidencia del netlist (redes clave)

### A.1 Entrada AC y AGND

```
( NetF300_1   F300-1  U301-4 )
( NetF300_2   F300-2  PS200-1  PS201-2  R303-2  RV300-1 )
( NetF301_1   F301-1  U301-3 )
( NetF301_2   F301-2  R314-2  RV301-1 )
( NetF302_1   F302-1  U301-2 )
( NetF302_2   F302-2  R326-2  RV302-1 )
( AGND        ...  PS200-2  PS201-1  PS201-3  U301-1  U100-6/20/29/39/42/43  U101-9/15 ... )
```

### A.2 Alimentación del RN

```
( REF        C110-2  C111-2  U100-3 )
( AVCC_3v3   C203-1  FB100-2  PS201-4  R100-2  R102-1  R103-2  R104-2
              U100-9  U100-28  U100-40  U100-41  U101-16 )
( NetC101_2  C101-2  C102-2  C103-2  C104-2  C105-2  C109-2  FB100-1 )
( VO         C106-2  C107-2  U100-38 )
```

`NetC101_2` no contiene ningún pin de U100: **C6**.

### A.3 SPI compartido

```
( SPI_MOSI_RN  U100-35  U101-14 )
( SPI_MISO_RN  U100-32  U101-11 )
( SPI_CS_RN    R104-1  U100-34  U101-13 )
( SPI_CLK_RN   U100-33  U101-12 )
( NetU101_4    U101-4  U401-23 )          # CS RN = IO21
( NetU101_5    U101-5  U401-24  U501-5 )  # CLK RN/SD = IO47
( NetR502_1    R502-1  U101-3  U401-22  U501-3 )  # MOSI
( NetR505_2    R505-2  U101-6  U401-25  U501-7 )  # MISO
( NetR503_1    U401-31  U501-2 )          # CS SD = IO38
```

### A.4 RSM3485

```
( NetC502_2  C502-2  FB500-1  U500-1 )    # VCC
( DGND       ...  U500-2 ... )            # GND
( NetU401_11  U401-11  U500-3 )           # TXD módulo
( NetU401_10  U401-10  U500-4 )           # RXD módulo
( NetR500_2   R500-2  U401-9  U500-5 )    # CON
( RGND       D500-3  J500-1  U500-10 )    # RGND aislada
```

### A.5 Respaldo

```
( Vout_5V    D200-2  PS200-4 )
( Vin_buck_5V  C200-2  D200-1  D201-1  FB202-2  FB502-1  U200-4  U200-5 )
( NetC201_1  C201-1  D201-2  R200-2  U200-1 )
( NetC201_2  C201-2  C202-1  R200-1  R202-2 )
( NetC207_1  C207-1  C208-2  D202-1  FB202-1  U201-2  U201-3 )
```

---

## Anexo B — Falsos positivos de la Revisión 1 (corregidos)

### B.1 SPI: canales B/C del ISO7741

La Revisión 1 leyó `SPI_CLK_RN = U101-12` como “OUTB” y `SPI_CS_RN = U101-13` como “OUTC”. El pinout correcto del ISO7741 es:

| Canal | Entrada | Salida | Señal |
|---|---|---|---|
| A | INA (3) | OUTA (14) | MOSI |
| B | INB (4) | OUTB (13) | CS del RN |
| C | INC (5) | OUTC (12) | CLK |
| D | IND (11) | OUTD (6) | MISO |

Con eso, `NetU101_5` (INC + IO47 + SD CLK) es el **CLK**, y `NetU101_4` (INB + IO21) es el **CS**. No hay cruce. El bus compartido es correcto.

### B.2 Cristal: 10 MΩ interno

El RN8302B V3 integra el resistor de 10 MΩ. El datasheet dice: “晶体8.192MHz，芯片集成10MΩ偏置电阻” y “推荐外部无需跨接10MΩ电阻”. No agregar R externa.

### B.3 RS-485: bias interno y CON activo bajo

El RSM3485PCT trae 22 kΩ de pull-up/pull-down internos y **CON = 0 transmite, CON = 1 recibe**. R500 a DVCC deja el módulo en recepción; no falta bias. El margen con 120 Ω es bajo (M4), pero no es “sin bias”.

### B.4 Pin 22 del RN: CF5, no CTT

En el RN8302B V3 el pin 22 es **CF5** (salida de pulso). El símbolo está bien. La Revisión 1 confundió la versión.

### B.5 C401/C403: X7R, no Y5V

El esquemático y el netlist los declaran `CAP CER 100nF 25V X7R 0603`. No son Y5V.

### B.6 SY6280: el límite de 0.83 A no limita el backup

Durante el respaldo, el SY6280 está apagado y la corriente va por D201. El límite de 0.83 A afecta la **carga** del banco, no la descarga. El problema real es la disipación (C7).

---

## Anexo C — Estado de archivos y trazabilidad

| Archivo | Fecha / estado |
|---|---|
| `hardware/altium/Project Outputs for .../Analizador_trifasico_IoT_pcb.NET` | **01/11/2026 01:16:33**; usado en esta revisión. |
| `POWER.SchDoc`, `THREE PHASES.SchDoc`, `MCU.SchDoc`, `INTERFACES.SchDoc` | 01/11/2026 00:41:46. |
| `MEASURES.SchDoc` | 01/11/2026 01:13:01. |
| `Analizador_trifasico_IoT_pcb.BomDoc` | 01/11/2026 06:17 (corregido). |
| `Analizador_trifasico_IoT_pcb.csv` / `.xlsx` | **31/10/2026 22:59 (viejos)**. |
| `hardware/libraries/Library_Analizador.IntLib` | **Ausente**; los `.SchDoc` la referencian. |
| `Analizador_*.PcbDoc` | **No está en el repositorio**; layout no revisado. |
| `REPORT.md` | Esta Revisión 2. |
| `REPORT_v1.md` | Revisión 1 conservada como historial. |

**Git (este agente):** no se modificó ningún `.SchDoc`, `.PcbDoc`, `.SchLib`, `.PcbLib` ni `.IntLib`. Solo se agregó `REPORT.md`, `REPORT_v1.md` y datasheets en `references/datasheets/` (estado sin commit). Los cambios en `.SchDoc`, `.BomDoc`, `.PrjPcb` y `Status Report.Txt` que aparecen en `git status` son del usuario/exportación, no de esta auditoría.

---

## Anexo D — Resumen de acciones por prioridad

| Prioridad | Acción | Archivo/hoja |
|---|---|---|
| 1 | Decidir y documentar C1 (AGND=N vs AFE aislado); agregar PE, bornera 600 V y etiquetas | `THREE PHASES`, `POWER` |
| 2 | Reemplazar jacks de CT por bornera con cortocircuito + TVS | `THREE PHASES` |
| 3 | Cambiar F300 por 1 A slow-blow; coordinar MOV/fusible | `THREE PHASES` |
| 4 | Corregir FB100/NetC101_2; agregar 0.1 µF en RN AVCC/DVCC | `MEASURES` |
| 5 | Reemplazar SY6280 por cargador de supercaps; agregar caps de salida | `POWER` |
| 6 | Reexportar BOM y verificar MPN | `BomDoc`/CSV/XLSX |
| 7 | Cambiar D200/D201/D202 por SMA/SMB 3 A o ideal diode | `POWER` |
| 8 | Agregar 0.1 µF en ISO7741, ESP32 y microSD | `MEASURES`, `MCU`, `INTERFACES` |
| 9 | Verificar huella `3` de U100 (LQFP-44) | `PcbLib1`, `Schlib1` |
| 10 | Agregar *power fail* y botón BOOT; Documentar headers/HaLow | `MCU`, `POWER` |

---

**Fin de la Revisión 2.** Si se cambia un `.SchDoc`, reexportar el netlist y el BOM antes de volver a confiar en este informe.







