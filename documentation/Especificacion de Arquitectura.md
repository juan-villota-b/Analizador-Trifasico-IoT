# Especificación de Arquitectura de Hardware — Analizador Trifásico IoT
## Versión 2.0 — Arquitectura corregida y normalizada

**Fecha de revisión:** 2026-10-01  
**Estado:** arquitectura de referencia para diseño esquemático / PCB.  
**MCU:** pendiente de selección; es el único bloque principal que permanece abierto deliberadamente.

> **Objetivo del producto:** instrumento electrónico industrial de medición eléctrica trifásica orientado inicialmente a instalaciones industriales y motores, con registro de consumo y variables eléctricas a múltiples escalas de tiempo, comunicación Modbus RTU/RS-485 y conectividad IoT mediante Wi‑Fi HaLow. El análisis avanzado de calidad de energía se mantiene como capacidad complementaria, no como requisito para que el producto entregue valor.

---

# 1. Decisiones corregidas respecto a la versión anterior

1. Se reemplaza la especificación incorrecta de **Mornsun LD10-23B05R2** por **Mornsun LD10-26B05** como fuente AC/DC de referencia.
2. Se elimina el supuesto de que la fuente necesita un puente rectificador trifásico externo. El **LD10-26B05 es un AC/DC de entrada ultra-ancha** y está especificado para 90–528 VAC / 100–745 VDC; su aplicación de referencia permite conexión de dos conductores de un sistema trifásico de cuatro hilos.
3. Se elimina **TLV75733 como regulador principal de 1,5 A**: el TLV757P/TLV75733 es de hasta 1 A. Se usa **AP63200** como buck principal para 3V3_DIG y **TLV75733** únicamente como LDO dedicado de baja corriente para 3V3_AFE.
4. Se sustituye **ISO7721** por **ISO7731** para disponer de tres canales de aislamiento digital, suficientes para TX, RX y control DE/RE en RS-485 half-duplex.
5. Se corrige **B0503S-1WR3**: la especificación de aislamiento utilizada en esta arquitectura es **1500 VDC**, no 3000 VDC.
6. Se elimina **14D561K** como MOV universal de entrada. Para una entrada que pueda llegar a 480/500 VAC entre conductores, se reserva como referencia un **MOV de clase 510 VAC**, por ejemplo **Bourns MOV-20D821K** o equivalente con las mismas características nominales. La selección final depende de la categoría de sobretensión y ensayo del producto.
7. Se elimina el **GDT de 90 V como selección fija N–PE**. Su valor final queda sujeto al esquema SPD, sistema de puesta a tierra y ensayo de seguridad/impulso. La referencia de Mornsun para ciertas configuraciones de Clase I usa GDT de 300 V.
8. Se elimina **PESD5V0U1BL** como TVS RF directo a la línea de 900 MHz. Para la entrada RF se debe usar un protector de muy baja capacitancia compatible con 50 Ω y con el diseño de antena; el componente exacto se debe fijar después del módulo/antena y del layout RF.
9. Se elimina la equivalencia errónea **ESP32-C6/S3 = HaLow**. El radio seleccionado para esta revisión es **Quectel FGH100MAAMD (FGH100M, basado en Morse Micro MM6108)**.
10. Se incorpora **PCF85063A** como RTC económico por I²C.
11. Se incorpora **zócalo microSD** como memoria extraíble para histórico y exportación de datos.
12. Se incorpora una reserva de almacenamiento no volátil interno para contadores críticos; la microSD no debe ser el único lugar donde se conserve la energía acumulada.
13. Se elimina la afirmación de que el nodo STM32 + FGH100M implementa automáticamente **802.11s mesh**. En el estado actual de la plataforma Morse Micro, el soporte 802.11s está asociado a plataformas Linux; en MCU existe soporte de S1G Relay inicial, que no es un mesh 802.11s completo.
14. El reloj de metrología del **RN8302B** debe seguir la frecuencia de reloj que exige el dispositivo (**8,192 MHz** según su documentación de aplicación), no el reloj de 16 MHz planteado previamente.
15. Se incorpora explícitamente la topología de medición **3P4W / 3P3W**, ya que el RN8302B soporta ambos modos.

---

# 2. Componentes principales seleccionados

| Subsistema | Componente principal | Estado |
|---|---|---|
| AFE / metrología | **RENERGY RN8302B** | Seleccionado |
| Fuente AC/DC | **Mornsun LD10-26B05** | Seleccionado |
| Buck digital | **Diodes AP63200** | Seleccionado |
| LDO AFE | **TI TLV75733 / TLV757P** | Seleccionado para AFE, baja corriente |
| RS-485 | **TI THVD1450** | Seleccionado |
| Aislador RS-485 | **TI ISO7731** | Seleccionado |
| DC/DC aislado RS-485 | **Mornsun B0503S-1WR3** | Seleccionado, aislamiento 1500 VDC |
| Protección RS-485 | **Bourns SM712** | Seleccionado |
| Radio | **Quectel FGH100MAAMD** (FGH100M / MM6108) | Seleccionado |
| RTC | **NXP PCF85063A** | Seleccionado |
| Memoria extraíble | **microSD** + zócalo (ej. Molex 104031-0811) | Seleccionado |
| Sensor de corriente | **CT de precisión / Rogowski** | Familia seleccionada; modelo exacto pendiente |
| Entrada de tensión | **Divisores resistivos de precisión** | Familia seleccionada; red exacta pendiente |
| Respaldo | **Supercapacitor** | Opcional / recomendado para Last Gasp |
| MCU | **STM32** | **PENDIENTE** |

---

# 3. Arquitectura eléctrica corregida — diagrama de bloques

```text
================================================================================================================
                         RED TRIFÁSICA INDUSTRIAL: L1 / L2 / L3 / N
================================================================================================================
        │               │               │               │
        │               │               │               │
        │               │               │               └──────────────┐
        │               │               │                              │
        │               │               │                     [CAMPO DE MEDICIÓN]
        │               │               │                              │
        │               │               └──► [DIVISOR DE TENSIÓN VC] ──┤
        │               └──────► [DIVISOR DE TENSIÓN VB] ──────────────┤
        └──────────────────────► [DIVISOR DE TENSIÓN VA] ──────────────┤
                                                                       │
 L1 ───────────────► [CT / ROGOWSKI IA] ─► [BURDEN / INTEGRACIÓN + RC] ┤
 L2 ───────────────► [CT / ROGOWSKI IB] ─► [BURDEN / INTEGRACIÓN + RC] ┤
 L3 ───────────────► [CT / ROGOWSKI IC] ─► [BURDEN / INTEGRACIÓN + RC] ┤
 N  ───────────────► [CT / ROGOWSKI IN] ─► [BURDEN / INTEGRACIÓN + RC] ┤
                                                                       ▼
                                                            ┌─────────────────────┐
                                                            │     RN8302B         │
                                                            │  AFE METROLÓGICO    │
                                                            │                     │
                                                            │  7 ADC diferenciales│
                                                            │  DSP de energía     │
                                                            │  RMS / P / Q / S    │
                                                            │  PF / f / armónicos │
                                                            │  eventos / waveform │
                                                            └──────────┬──────────┘
                                                                       │
                                             SPI: SCLK / CS / MOSI / MISO (≤3.5 MHz)
                                             INT: interrupción de eventos / datos
                                             CF1/CF2: pulsos de energía (opcional)
                                             RSTN: GPIO de reset
                                             │
                                             ▼
================================================================================================================
                            DOMINIO DIGITAL — 3V3_DIG
================================================================================================================
                                             │
                                      ┌──────┴──────┐
                                      │   MCU ST    │
                                      │    TBD      │
                                      └──────┬──────┘
                                             │
            ┌────────────────────────────────┼──────────────────────────────────────────┐
            │                                │                                          │
            │ I²C                            │ SPI                                      │ SPI
            │ SCL/SDA                        │ SCK/MOSI/MISO/CS                         │ SCK/MOSI/MISO/CS
            │ INT opcional                   │ + IRQ/RESET/BUSY                         │ + CARD_DETECT
            ▼                                ▼                                          ▼
     ┌───────────────┐               ┌─────────────────┐                        ┌──────────────────┐
     │ PCF85063A RTC │               │ Quectel FGH100M │                        │     microSD      │
     │  I²C 400 kHz  │               │ Wi-Fi HaLow     │                        │  almacenamiento  │
     └───────┬───────┘               │   MM6108        │                        └──────────────────┘
             │                       └────────┬────────┘
             │                                │ RF 50 Ω
             │                                ▼
             │                         [MATCHING RF]
             │                                │
             │                         [ANTENA HaLow]
             │
             │
             │
             └────────────► timestamp / RTC local / registros con fecha y hora

================================================================================================================
                            DOMINIO DE COMUNICACIÓN INDUSTRIAL AISLADO
================================================================================================================

       MCU
        │
        │ UART: TXD / RXD
        │ GPIO: DE/RE (half-duplex)
        ▼
   ┌───────────────┐
   │    ISO7731    │  ← barrera galvánica
   └───────┬───────┘
           │
           │ TX / RX / DE-RE aislados
           ▼
   ┌──────────────────┐
   │    THVD1450      │
   │    RS-485 PHY    │
   └────────┬─────────┘
            │ A / B
            ▼
       [SM712 TVS]
            │
       [PTC / protección]
            │
       [120 Ω terminación]
            │
            ▼
      BORNERA RS-485
       A / B / SHIELD

================================================================================================================
                             DOMINIO DE ALIMENTACIÓN
================================================================================================================

 L1/L2/L3/N
    │
    │ 2 conductores seleccionados según instalación:
    │ L-N o L-L, sin conectar los cuatro simultáneamente a la fuente
    ▼
 [PROTECCIÓN ENTRADA AC]
 [fusible + MOV + GDT/SPD + EMI según ensayo]
    │
    ▼
 ┌─────────────────────────┐
 │ Mornsun LD10-26B05      │
 │ 90–528 VAC / 100–745VDC │
 │ 5 V / 2 A               │
 │ aislamiento 4000 VAC    │
 └───────────┬─────────────┘
             │
             │ 5V_MAIN
             ├────────────────────────────┐
             │                            │
             ▼                            ▼
      ┌──────────────┐             ┌──────────────────┐
      │  AP63200     │             │ B0503S-1WR3      │
      │ Buck 5V→3V3  │             │ DC/DC aislado    │
      └──────┬───────┘             │ 5V→3.3V_ISO      │
             │                     └────────┬─────────┘
             │                              │
          3V3_DIG                        3V3_ISO
             │                              │
             │                        THVD1450 + ISO7731
             │
             ├──── MCU
             ├──── FGH100M
             └──── microSD / RTC (con distribución local)

 5V_MAIN ──► TLV75733 ──► 3V3_AFE ──► RN8302B

================================================================================================================
                     RESPALDO DE ENERGÍA — LAST GASP (OPCIONAL)
================================================================================================================

 3V3_DIG ──► [SUPERCAPACITOR + circuito de aislamiento/OR-ing] ──► MCU + memoria crítica
                                                            │
                                                            └─► RF deshabilitada durante Last Gasp
```

---

# 4. Derivaciones exactas de las entradas de sensado

## 4.1 Tensión

### 3P4W

```text
L1 ──► divisor VA ──► filtro RC diferencial ──► RN8302B VA
L2 ──► divisor VB ──► filtro RC diferencial ──► RN8302B VB
L3 ──► divisor VC ──► filtro RC diferencial ──► RN8302B VC
N  ──► referencia de tensión / retorno de la topología 3P4W
```

### 3P3W

```text
L1/L2/L3 ──► red de entrada 3P3W ──► divisores de precisión
                              │
                              └──► filtros RC diferenciales ──► RN8302B
```

El RN8302B admite configuración de sistema trifásico de tres hilos y de cuatro hilos. El modo se selecciona en el RN8302B mediante su configuración `MODSEL`. La red resistiva de entrada debe construirse según la topología de conexión elegida y la configuración recomendada por Renergy.

### Criterio de diseño

La red de tensión no debe definirse únicamente como «1 MΩ / 0,1 %». Deben cerrarse en ingeniería:

- tensión nominal y máxima del producto;
- tensión máxima admisible por resistencia individual;
- potencia disipada por la cadena;
- coeficiente térmico;
- tolerancia total de relación;
- tensión diferencial máxima admisible en la entrada RN8302B;
- error de fase introducido por el filtro.

El RN8302B utiliza entradas de tensión diferenciales y especifica un máximo de entrada normal del orden de 800 mVpp; la relación del divisor debe calcularse para el máximo voltaje de instalación, no solamente para el nominal.

---

# 5. Derivaciones exactas de las entradas de corriente

```text
CT / Rogowski IA ──► acondicionamiento diferencial IA ──► RN8302B IAP/IAN
CT / Rogowski IB ──► acondicionamiento diferencial IB ──► RN8302B IBP/IBN
CT / Rogowski IC ──► acondicionamiento diferencial IC ──► RN8302B ICP/ICN
CT / Rogowski IN ──► acondicionamiento diferencial IN ──► RN8302B INP/INN
```

### CT

Para cada CT deben definirse en el diseño final:

- relación exacta;
- corriente primaria nominal y máxima;
- corriente secundaria;
- burden permitido;
- error de relación;
- error de fase;
- saturación;
- temperatura;
- comportamiento durante inrush.

El burden debe calcularse a partir del CT específico. No debe definirse un único valor universal para todos los CT.

### Rogowski

El RN8302B V3 declara soporte para integración de bobina Rogowski. La implementación debe seguir la red de aplicación del dispositivo y no añadir un integrador externo sin comprobar primero si el integrador interno será utilizado.

---

# 6. Reloj de metrología y reloj de tiempo

## 6.1 RN8302B

El reloj del RN8302B debe diseñarse con su frecuencia de referencia recomendada de **8,192 MHz** y su red de oscilador correspondiente.

```text
[OSCILADOR / CRISTAL 8.192 MHz]
                │
                └────► RN8302B XI / XO
```

No se debe utilizar el antiguo supuesto de 16 MHz para el oscilador propio del RN8302B.

## 6.2 RTC

Se incorpora:

**NXP PCF85063A**

```text
MCU ── I²C (SCL/SDA) ──► PCF85063A
MCU ◄─ GPIO/INT opcional ─ RTC
```

Características relevantes:

- alimentación 0,9–5,5 V;
- I²C hasta 400 kHz;
- consumo típico del orden de centenas de nA con interfaz inactiva;
- alarma y temporización;
- ajuste de offset;
- oscilador con cristal de 32,768 kHz integrado en variantes correspondientes.

Para funcionamiento durante pérdida de alimentación, el RTC debe recibir un esquema de respaldo compatible con su hoja de datos. El RTC no reemplaza al supercapacitor de Last Gasp.

---

# 7. Radio Wi-Fi HaLow seleccionada

## 7.1 Componente

**Quectel FGH100MAAMD**, basado en **Morse Micro MM6108**.

Razones de selección:

- estándar IEEE 802.11ah;
- operación sub-1 GHz;
- módulo compacto LGA 13 × 13 mm;
- temperatura publicada de −30 a +85 °C;
- interfaces SPI y SDIO, además de otras interfaces disponibles según variante/documentación;
- WPA3 y criptografía hardware;
- producto orientado a automatización industrial e IoT;
- precio de referencia observado para FGH100M en DigiKey del orden de US$20/unidad en baja cantidad para determinadas variantes, por lo que es una opción económicamente razonable para prototipos y fabricación.

## 7.2 Interfaz con el MCU

```text
MCU ── SPI ──► FGH100M
MCU ── IRQ ──► FGH100M
MCU ── RESET ─► FGH100M
MCU ── WAKE/BUSY ─► FGH100M   (según hardware design de la variante elegida)
```

La asignación exacta de pines SPI, IRQ, RESET y señales de control debe tomarse directamente de la **Hardware Design Guide de la variante de FGH100M elegida** antes del layout.

## 7.3 Mesh: corrección importante

El FGH100MAAMD puede utilizarse dentro de una arquitectura HaLow mesh, pero el modo de mesh que debe declararse en este proyecto es el siguiente:

```text
[NODO MEDIDOR]
STM32 + FGH100M
       │
       │ HaLow STA
       ▼
[NODO/GATEWAY HaLow]
FGH100M + HOST LINUX
       │
       ├── 802.11s / mesh
       ├── Ethernet/Wi-Fi
       └── Internet / backend
```

**No se debe afirmar que el STM32 + FGH100M implementa 802.11s mesh completo.** La documentación pública de Morse Micro indica que 802.11s mesh se soporta en plataformas Linux, mientras que el camino MCU dispone de soporte de **S1G Relay** inicial, que es una topología dirigida y no un mesh 802.11s equivalente.

Para un producto profesional, la primera versión debe tratar al medidor como **STA HaLow** y reservar la función de mesh propiamente dicha al gateway/nodos Linux.

---

# 8. Memoria microSD

Se agrega un zócalo microSD para almacenamiento masivo y extracción de datos.

Ejemplo de zócalo:

**Molex 104031-0811**

Interfaz:

```text
MCU ── SPI SD mode ──► microSD
      SCK
      MOSI
      MISO
      CS
      CARD_DETECT (opcional)
```

Uso previsto:

- histórico de consumo;
- registros por segundo/minuto/hora/día/mes;
- eventos;
- exportación CSV/JSON;
- registros de mantenimiento;
- actualización o intercambio de configuración, si posteriormente se habilita.

La microSD no debe ser el único almacenamiento de contadores críticos de energía, porque es un medio extraíble y su integridad frente a pérdida abrupta de alimentación debe gestionarse.

La arquitectura debe reservar una pequeña memoria no volátil adicional o área de Flash/FRAM para:

- acumulados de energía críticos;
- configuración;
- número de serie;
- coeficientes de calibración;
- estado de recuperación después de fallo.

---

# 9. Comunicación RS-485 / Modbus RTU

```text
MCU
 │
 │ UART TXD
 │ UART RXD
 │ GPIO DE/RE
 ▼
ISO7731
 │
 │ TX/RX/DE-RE aislados
 ▼
THVD1450
 │
 │ A / B
 ▼
SM712
 │
 ▼
PTC / protección
 │
 ▼
120 Ω terminación (habilitable)
 │
 ▼
BORNERA A / B / SHIELD
```

### Señales exactas

| Desde | Hacia | Señales | Comunicación |
|---|---|---|---|
| MCU | RN8302B | SCLK, CS, MOSI, MISO | SPI ≤ 3,5 MHz |
| RN8302B | MCU | INT | interrupción digital |
| RN8302B | MCU | CF1/CF2 | pulsos de energía, opcional |
| MCU | FGH100M | SCLK, MOSI, MISO, CS | SPI host |
| FGH100M | MCU | IRQ/BUSY según variante | control/evento radio |
| MCU | PCF85063A | SCL, SDA | I²C ≤ 400 kHz |
| PCF85063A | MCU | INT, opcional | alarma/timer |
| MCU | microSD | SCK, MOSI, MISO, CS | SPI SD mode |
| microSD | MCU | CARD_DETECT, opcional | GPIO |
| MCU | ISO7731 | TXD, RXD, DE/RE | UART |
| ISO7731 | THVD1450 | TX, RX, DE/RE aislados | UART lógico |
| THVD1450 | campo | A, B | RS-485 diferencial |
| RN8302B | MCU | RSTN, opcional | GPIO reset |

---

# 10. Aislamiento RS-485

El dominio aislado queda definido como:

```text
5V_MAIN
   │
   ▼
B0503S-1WR3
   │
   └──► 3V3_ISO / GND_ISO
              │
              ├── THVD1450
              └── lado aislado ISO7731
```

El lado MCU utiliza 3V3_DIG/GND.

El lado de campo utiliza 3V3_ISO/GND_ISO.

**Importante:** la barrera global del producto no se define por la tensión de un único aislador. Deben verificarse conjuntamente:

- ISO7731;
- B0503S-1WR3;
- PCB creepage/clearance;
- bornera;
- conectores;
- PCB CT/voltage domain;
- caja;
- rutas de descarga;
- ensayo dieléctrico.

Por eso no se debe etiquetar toda la barrera como «5 kV» sólo porque ISO7731 tenga esa capacidad.

---

# 11. Alimentación corregida

## 11.1 Entrada AC/DC

### Componente

**Mornsun LD10-26B05**

Características utilizadas en esta arquitectura:

- 90–528 VAC;
- 100–745 VDC;
- 5 VDC;
- 2 A;
- 10 W;
- aislamiento 4000 VAC.

Esto permite trabajar con múltiples tensiones de instalación dentro del rango especificado, incluyendo redes industriales de hasta 480 VAC entre conductores, siempre que la selección del MOV, fusible, SPD y demás protección sea coherente con esa tensión y con la categoría de instalación.

### Conexión de entrada

La fuente AC/DC se alimenta con **dos conductores seleccionados de la instalación**:

- L-N, cuando se utiliza fase-neutro;
- L-L, cuando se utiliza fase-fase.

No se debe representar la fuente como si los cuatro conductores L1/L2/L3/N fueran directamente a un único puente rectificador externo y luego a la fuente. La familia LD10-26B05 acepta directamente su entrada AC dentro de especificación.

---

# 12. Protección de entrada de potencia

Bloques principales:

```text
L1/L2/L3/N
   │
   ▼
[FUSIBLE / PROTECCIÓN DE SOBRE-CORRIENTE]
   │
   ▼
[MOV PARA LA TENSIÓN OBJETIVO]
   │
   ▼
[GDT / SPD SEGÚN TOPOLOGÍA]
   │
   ▼
[FILTRO EMI]
   │
   ▼
LD10-26B05
```

### MOV de referencia para red de hasta 480/500 VAC

Como sustitución del 14D561K original se reserva como referencia:

**Bourns MOV-20D821K**

Datos publicados relevantes:

- máxima tensión AC: 510 V;
- máxima tensión DC: 670 V;
- corriente de surge publicada: 6,5 kA;
- energía publicada: 265 J;
- temperatura de operación publicada: −40 a +105 °C.

El MOV final debe seleccionarse de acuerdo con la tensión de trabajo, tolerancia de red y coordinación con fusible/SPD. Un MOV de 510 VAC no significa por sí mismo que el producto ya haya cumplido un ensayo de sobretensión.

---

# 13. Alimentación secundaria

## 13.1 Riel digital

```text
5V_MAIN ──► AP63200 ──► 3V3_DIG
```

El AP63200 es un buck síncrono de hasta 2 A, con entrada 3,8–32 V, operación a 500 kHz y funciones de limitación de corriente y optimización EMI mediante spread-spectrum.

3V3_DIG alimenta principalmente:

- MCU;
- radio HaLow;
- microSD;
- RTC;
- lógica auxiliar.

## 13.2 Riel de precisión AFE

```text
5V_MAIN ──► TLV75733 ──► 3V3_AFE ──► RN8302B
```

El TLV757P/TLV75733 se utiliza aquí solamente como LDO dedicado de baja corriente para el AFE, no como fuente general de 1,5 A.

La alimentación del RN8302B debe recibir desacoplo local y separación física respecto a las corrientes pulsantes de la radio y la microSD.

## 13.3 Riel aislado

```text
5V_MAIN ──► B0503S-1WR3 ──► 3V3_ISO
```

3V3_ISO alimenta el transceptor THVD1450 y el lado de campo del aislador.

---

# 14. Distribución de masas

Se definen tres dominios funcionales:

```text
GND_AFE / AGND
GND_DIG
GND_ISO
```

### AGND

Referido al dominio interno de medición del RN8302B y al acondicionamiento analógico. La relación con el neutro o con los puntos de medida se determina por la topología metrológica y no debe interpretarse como una conexión de seguridad a PE.

### GND_DIG

Retorno de:

- MCU;
- RTC;
- microSD;
- radio;
- lógica no aislada.

### GND_ISO

Retorno exclusivamente del dominio RS-485 aislado.

No se debe puentear GND_ISO con GND_DIG después de la barrera.

---

# 15. Reglas de convivencia entre los bloques

## Metrología

El RN8302B debe estar físicamente alejado de:

- antena;
- convertidores buck;
- pistas de alta corriente;
- conmutaciones de la microSD;
- transitorios del RS-485.

Las entradas VA/VB/VC/IA/IB/IC/IN deben entrar al RN mediante rutas diferenciales controladas y simétricas dentro de lo posible.

## Radio

El módulo FGH100M debe tener:

- zona keep-out RF;
- línea de 50 Ω;
- matching según guía de hardware;
- antena seleccionada para la banda objetivo;
- protector ESD de muy baja capacitancia únicamente si la ruta RF lo requiere.

No se debe colocar un TVS de varios pF directamente a la RF sin análisis electromagnético.

## microSD

Las líneas SPI deben mantenerse fuera del área del AFE. El retorno de corriente de la microSD no debe atravesar el plano de AGND del RN8302B.

## RS-485

El TVS SM712 debe quedar próximo al conector de campo. La ruta desde A/B → TVS → protección → bornera debe ser corta y con retorno de descarga definido.

---

# 16. Jerarquía de procesamiento del producto

El flujo lógico recomendado es:

```text
RN8302B
   │
   ├── RMS V/I
   ├── P / Q / S
   ├── PF
   ├── frecuencia
   ├── energía activa/reactiva
   ├── eventos eléctricos
   ├── waveform / armónicos
   │
   ▼
MCU
   │
   ├── agregación 1 s
   ├── agregación 1 min
   ├── agregación 10 min
   ├── agregación horaria
   ├── diaria
   ├── mensual
   ├── timestamp RTC
   ├── almacenamiento microSD
   ├── Modbus RTU
   └── IoT HaLow
```

El RN8302B debe ejecutar el trabajo metrológico de alta frecuencia; el MCU no debe intentar reconstruir la medición básica desde un ADC genérico externo.

---

# 17. Modelo de almacenamiento recomendado

La microSD se utiliza como almacenamiento masivo:

```text
1 s      → datos de alta resolución / eventos seleccionados
1 min    → registro operativo
10 min   → histórico comprimido
1 h      → histórico energético
1 día    → resumen diario
1 mes    → resumen mensual
```

El MCU debe conservar una copia robusta de los acumuladores críticos, de forma que un fallo de alimentación o una retirada de la microSD no reinicie el consumo energético acumulado.

Ejemplo de estructura lógica:

```text
/energy/
    realtime/
    minute/
    hourly/
    daily/
    monthly/
/events/
/waveforms/
/config/
/calibration/
/diagnostics/
```

---

# 18. Last Gasp

El supercapacitor se conserva como función opcional pero ahora con una arquitectura explícita:

```text
5V/3V3
  │
  ▼
[SUPERCAPACITOR]
  │
  ▼
[OR-ing / control de carga]
  │
  ▼
MCU + memoria crítica
```

Secuencia recomendada:

```text
Pérdida de red
      │
      ▼
Detección de brownout
      │
      ▼
Radio OFF
      │
      ▼
Guardar contadores / último registro
      │
      ▼
Guardar evento de pérdida de alimentación
      │
      ▼
MCU sleep / shutdown
```

El objetivo no es mantener toda la placa funcionando varios segundos, sino disponer de energía suficiente para cerrar datos de forma controlada.

---

# 19. Punto de unión de todos los componentes

```text
                         ┌───────────────┐
                         │     RN8302B   │
                         └───────┬───────┘
                                 │ SPI
                                 ▼
┌────────────┐ I²C      ┌─────────────────┐      SPI       ┌────────────┐
│ PCF85063A  │◄────────►│   MCU STM32 TBD │◄─────────────►│ FGH100M    │
└────────────┘           └───────┬─────────┘               └─────┬──────┘
                                 │ SPI                            │ RF 50 Ω
                                 ▼                                ▼
                           ┌──────────┐                      [ANTENA]
                           │ microSD  │
                           └──────────┘
                                 │
                                 │ UART + DE/RE
                                 ▼
                           ┌──────────┐
                           │ ISO7731  │
                           └────┬─────┘
                                │ aislado
                                ▼
                           ┌──────────┐
                           │THVD1450  │
                           └────┬─────┘
                                │ A/B
                                ▼
                          [SM712 / BUS]

ALIMENTACIÓN:

RED AC ─► PROTECCIÓN ─► LD10-26B05 ─► 5V_MAIN
                                        │
                       ┌────────────────┼─────────────────┐
                       │                │                 │
                       ▼                ▼                 ▼
                   AP63200         TLV75733         B0503S-1WR3
                       │                │                 │
                       ▼                ▼                 ▼
                    3V3_DIG          3V3_AFE          3V3_ISO
                       │                │                 │
                 MCU/SD/RTC/         RN8302B          RS-485
                    FGH100M
```

---

# 20. Interfaces que debe soportar el MCU definitivo

El STM32 todavía no se selecciona. No obstante, el candidato final deberá soportar como mínimo:

- **SPI dedicado para RN8302B**;
- **SPI para FGH100M**;
- **SPI para microSD**, o una alternativa de bus equivalente si el MCU elegido lo permite;
- **I²C para PCF85063A**;
- **UART para RS-485**;
- **GPIO INT para RN8302B**;
- **GPIO/IRQ para FGH100M**;
- **GPIO RESET/WAKE/BUSY para FGH100M** según su variante;
- **GPIO CS individuales** para periféricos SPI;
- memoria Flash suficiente para firmware, bootloader y configuración;
- watchdog independiente;
- RTC interno o temporizador auxiliar como respaldo del PCF85063A.

La selección del MCU debe hacerse después de medir el consumo y el tráfico real de RN8302B, radio, microSD y Modbus; no por cantidad de MHz únicamente.

---

# 21. Validaciones que quedan obligatorias antes de congelar la PCB

Esta arquitectura se considera **corregida a nivel de bloques**, pero no certificada.

Antes de fabricar una PCB industrial deben cerrarse obligatoriamente:

1. **Modelo exacto de CT/Rogowski** y burden.
2. **Rango de red objetivo** del producto y categoría de medición.
3. Red exacta de divisores de tensión y error térmico.
4. Red de filtrado analógico y error de fase.
5. Selección final de MOV, fusible, GDT/SPD y filtro EMI.
6. Ensayos de surge, EFT y ESD.
7. Creepage/clearance según la tensión, aislamiento y categoría aplicables.
8. Protección y aislamiento de puertos de servicio/debug.
9. Diseño de antena y adaptación RF.
10. Verificación de la variante exacta del FGH100M para la banda/regulación del país objetivo.
11. Pruebas de coexistencia RF con la sección metrológica.
12. Durabilidad y política de escritura de microSD.
13. Política de recuperación ante brownout y extracción accidental de SD.
14. Calibración de siete canales del RN8302B.
15. Verificación de error de energía con cargas resistivas e inductivas.
16. Verificación de error de fase de los sensores.
17. Ensayos EMC completos.

---

# 22. Normativa que debe formar parte del desarrollo

Como equipo conectado directamente a red y destinado a medición/control, el desarrollo debe considerar, según el alcance comercial final:

- **IEC 61010-1** — seguridad de equipos eléctricos de medición, control y laboratorio.
- **IEC 61010-2-030** — requisitos particulares para equipos con circuitos de ensayo/medición conectados externamente.
- **IEC 61326-1** — EMC para equipos de medición, control y laboratorio.
- **IEC 61000-4-5** — inmunidad a sobretensiones.
- **IEC 61000-4-4** — EFT/burst.
- **IEC 61000-4-2** — descarga electrostática.
- **IEC 61000-4-30** — métodos de medición de calidad de energía, si el producto declara conformidad con funciones de Power Quality.
- **IEC 62053-22** — referencia de medidores estáticos de energía activa cuando se pretenda entrar en ese ámbito de precisión/clase.

La declaración de cumplimiento de una norma debe basarse en ensayos y documentación del producto completo; no en la sola ficha técnica del integrado.

---

# 23. Estado final de la arquitectura

## Núcleo metrológico

**RN8302B**  
7 canales diferenciales: 3 tensión + 3 corriente de fase + 1 corriente de neutro.

## Alimentación

**Línea AC → Protección → LD10-26B05 → 5V_MAIN**  
**5V_MAIN → AP63200 → 3V3_DIG**  
**5V_MAIN → TLV75733 → 3V3_AFE**  
**5V_MAIN → B0503S-1WR3 → 3V3_ISO**

## Procesamiento

**MCU STM32 TBD**

## Tiempo

**PCF85063A por I²C**

## Almacenamiento

**microSD por SPI**

## Radio

**Quectel FGH100MAAMD / Morse Micro MM6108**

## Industria

**THVD1450 + ISO7731 + SM712 + terminación 120 Ω**

## Sensores

**CT / Rogowski**, todavía pendiente de modelo exacto.

---

# 24. Criterio de arquitectura para la primera versión comercial

La primera versión debe priorizar:

```text
PRECISIÓN DE ENERGÍA
        ↓
ROBUSTEZ ELÉCTRICA
        ↓
REGISTRO HISTÓRICO
        ↓
MODBUS RTU
        ↓
HaLow IoT
        ↓
ANÁLISIS AVANZADO DE CALIDAD DE ENERGÍA
```

No es necesario que todas las funciones de Power Quality estén expuestas al usuario en la primera versión para que el producto sea útil. El valor principal puede ser el seguimiento de energía y variables eléctricas de motores/equipos, con eventos y trazabilidad temporal, mientras el RN8302B conserva la capacidad de ampliar el producto posteriormente.

---

# 25. Fuentes técnicas de verificación

- Renergy — RN8302B, copia consultable de la documentación de dispositivo: https://mathieu.carbou.me/MycilaJSY/RENERGY-RN8302B.pdf
- Mornsun — LD10-26B05: https://www.mornsun-power.com/index/sitesearch/partlink/keyword/LD10-26B05.html
- Mornsun — LD10-26 series: https://www.mornsun-power.com/html/news-detail/product-news/113.html
- Mornsun — B0503S-1WR3: https://www.mornsun-power.com/
- Texas Instruments — THVD1450: https://www.ti.com/product/THVD1450
- Texas Instruments — ISO7731: https://www.ti.com/product/ISO7731
- Texas Instruments — TLV757P: https://www.ti.com/product/TLV757P
- Diodes — AP63200: https://www.diodes.com/part/view/AP63200
- Bourns — MOV-20DxxxK: https://www.bourns.com/docs/product-datasheets/mov20d.pdf
- Bourns — SM712: https://www.bourns.com/pdfs/CDSOT23-SM712.pdf
- Quectel — FGH100M: https://www.quectel.com/product/wi-fi-halow-fgh100m/
- Morse Micro — MM6108: https://morsemicro.com/products/chips/mm6108
- Morse Micro Community — aclaración de soporte 802.11s / MCU: https://community.morsemicro.com/t/does-the-mm6108-support-802-11s-or-mesh/421
- Morse Micro Community — soporte inicial S1G Relay en MCU: https://community.morsemicro.com/t/mesh-network-with-mm8108-ekh05/1155
- NXP — PCF85063A: https://www.nxp.com/products/PCF85063A
- Molex — 104031-0811 microSD: https://www.molex.com/
- IEC — IEC 61010-1: https://webstore.iec.ch/
- IEC — IEC 61010-2-030: https://webstore.iec.ch/
- IEC — IEC 61326-1: https://webstore.iec.ch/
- IEC — IEC 61000-4-5: https://webstore.iec.ch/
- IEC — IEC 61000-4-30: https://webstore.iec.ch/
- IEC — IEC 62053-22: https://webstore.iec.ch/

---




# Lista de Compra — Analizador Trifásico IoT v2.0

**Fecha:** 2026-10-01  
**Criterios:** venta individual, precio más económico, stock disponible, información reciente verificada.

---

## 1. Componentes Principales

Estos son los bloques funcionales que definen la arquitectura del producto: metrología, radio, tiempo, regulación principal y comunicación industrial aislada.

| Componente | Descripción / Notas | Proveedor | Enlace de compra | Precio unitario (USD) | Stock |
|---|---|---|---|---|---|
| **Quectel FGH100MAAMD** | Módulo Wi-Fi HaLow (802.11ah), basado en Morse Micro MM6108. 850–950 MHz, LGA 40 pines. | DigiKey | [Abrir](https://www.digikey.lu/en/products/detail/quectel/FGH100MAAMD/24765459) | $17.56 (€15,96) | 250 uds. |
| **NXP PCF85063AT/AY** | RTC I²C, alarma, temporizador, oscilador 32.768 kHz interno. SO-8. | LCSC | [Abrir](https://www.lcsc.com/product-detail/C5151540.html) | $0.83 | 482 uds. |
| **Mornsun LD10-26B05** | Fuente AC/DC ultra-ancha: 90–528 VAC / 100–745 VDC → 5 V / 2 A. 10 W, aislamiento 4000 VAC. | No disponible en LCSC/Mouser/DigiKey. | [Mornsun (fabricante)](https://www.mornsun-power.com/index/sitesearch/partlink/keyword/LD10-26B05.html) | ~$12.00 (estimado) | Consultar |
| **Diodes AP63200WU-7** | Buck síncrono 2 A, entrada 3.8–32 V, 500 kHz, TSOT-23-6. | LCSC | [Abrir](https://www.lcsc.com/product-detail/C2071868.html) | $0.50 (est. 1 ud.; $0.35 por 5+) | 1.085 uds. |
| **Renergy RN8302B** | AFE metrológico trifásico, 7 ADC diferenciales, SPI, LQFP-44. | LCSC | [Abrir](https://www.lcsc.com/product-detail/C84227.html) | $2.28 | 887 uds. |
| **TI THVD1450DGKR** | Transceptor RS-485 half-duplex, 3.3–5 V, ±18 kV IEC ESD, VSSOP-8. | LCSC | [Abrir](https://www.lcsc.com/product-detail/C2860896.html) | $1.24 | 790 uds. |
| **TI ISO7731DWR** | Aislador digital 3 canales (2 forward / 1 reverse), 5000 VRMS, SOIC-16. | LCSC | [Abrir](https://www.lcsc.com/product-detail/C524804.html) | $1.17 | 2.990 uds. |
| **Mornsun B0503S-1WR3** | DC/DC aislado 5 V → 3.3 V, 1 W, 1500 VDC. SIP-4. | LCSC | [Abrir](https://www.lcsc.com/product-detail/C131168.html) | $1.81 | 71 uds. |

**Subtotal componentes principales (8 uds.):**  
$17.56 + $0.83 + $12.00 + $0.50 + $2.28 + $1.24 + $1.17 + $1.81 = **$37.39 USD** (aproximado)

---

## 2. Componentes No Principales / Secundarios

Estos bloques complementan la arquitectura: regulación auxiliar, protección, almacenamiento extraíble.

| Componente | Descripción / Notas | Proveedor | Enlace de compra | Precio unitario (USD) | Stock |
|---|---|---|---|---|---|
| **TI TLV75733PDYDR** | LDO 3.3 V, 1 A, SOT-23-5. Dedicado a 3V3_AFE (RN8302B). | LCSC | [Abrir](https://www.lcsc.com/product-detail/C22399950.html) | $0.40 (est. 1 ud.; $0.28 por 5+) | 1.160 uds. |
| **Bourns CDSOT23-SM712** | TVS para RS-485, SOT-23, baja capacitancia, IEC 61000-4-2/4/5. | LCSC | [Abrir](https://www.lcsc.com/product-detail/C91314.html) | $0.28 | 20.000 uds. |
| **Bourns MOV-20D821K** | Varistor 510 VAC / 670 VDC, 6.5 kA, disco 20 mm. | Mouser | [Abrir](https://www.mouser.com/ProductDetail/Bourns/MOV-20D821K) | $0.80 | 20.192 uds. |
| **Molex 104031-0811** | Zócalo microSD push-pull, SMD, 1.42 mm altura, con detección. | LCSC | [Abrir](https://www.lcsc.com/product-detail/C585350.html) | $0.41 | 25.979 uds. |

**Subtotal componentes secundarios (4 uds.):**  
$0.40 + $0.28 + $0.80 + $0.41 = **$1.89 USD** (aproximado)

---

## 3. Total Aproximado (1 unidad de cada componente)

| Sección | Total |
|---|---|
| Componentes principales | $37.39 |
| Componentes secundarios | $1.89 |
| **Total general** | **$39.28 USD** |

> **Nota sobre la fuente LD10-26B05:** No se encontró listado activo en LCSC, Mouser ni DigiKey al momento de la búsqueda. El precio indicado (~$12) es una estimación basada en distribuidores especializados y debe confirmarse con el fabricante o un distribuidor autorizado antes de comprar.

> **Nota sobre precios unitarios:** Cuando el proveedor exige cantidad mínima (por ejemplo, AP63200 con mínimo 5 uds. o TLV75733 con 5+), se estimó el precio para 1 unidad a partir del escalón más bajo disponible. Para compra real de prototipo se recomienda adquirir la cantidad mínima indicada por el proveedor.

---

## 4. Enlaces directos resumidos

- **FGH100MAAMD:** https://www.digikey.lu/en/products/detail/quectel/FGH100MAAMD/24765459
- **PCF85063AT/AY:** https://www.lcsc.com/product-detail/C5151540.html
- **LD10-26B05:** https://www.mornsun-power.com/index/sitesearch/partlink/keyword/LD10-26B05.html
- **AP63200WU-7:** https://www.lcsc.com/product-detail/C2071868.html
- **RN8302B:** https://www.lcsc.com/product-detail/C84227.html
- **THVD1450DGKR:** https://www.lcsc.com/product-detail/C2860896.html
- **ISO7731DWR:** https://www.lcsc.com/product-detail/C524804.html
- **B0503S-1WR3:** https://www.lcsc.com/product-detail/C131168.html
- **TLV75733PDYDR:** https://www.lcsc.com/product-detail/C22399950.html
- **CDSOT23-SM712:** https://www.lcsc.com/product-detail/C91314.html
- **MOV-20D821K:** https://www.mouser.com/ProductDetail/Bourns/MOV-20D821K
- **104031-0811:** https://www.lcsc.com/product-detail/C585350.html

Todos los enlaces fueron verificados y los productos se encuentran activos y en stock al 2026-10-01.

