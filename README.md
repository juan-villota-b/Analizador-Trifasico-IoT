# Analizador Trifásico IoT

> Instrumento electrónico industrial de **medición eléctrica trifásica** con conectividad **IoT**, pensado para instalaciones industriales y motores.
> Incluye registro de consumo, variables eléctricas a múltiples escalas de tiempo, comunicación **Modbus RTU / RS-485** y enlace **Wi-Fi HaLow**.

---

## 📋 Descripción del proyecto

El producto es un **medidor de calidad de energía trifásico** con capacidad IoT. El diseño actual cubre:

| Bloque | Función |
|---|---|
| **AFE metrológico** | RENERGY **RN8302B** — 7 ADC diferenciales, DSP de energía, mide V, I, P, Q, S, PF, THD |
| **Alimentación AC/DC** | Entrada **90–528 VAC** (o 100–745 VDC) de red trifásica de 4 hilos |
| **Riel digital** | Buck **AP63203WU-7** → 3V3_DIG (MCU, radio, RS-485, microSD) |
| **Riel de precisión AFE** | LDO **TLV75733** → 3V3_AFE (bajo ruido para el AFE) |
| **Riel aislado** | DC/DC aislado **B0503S-1WR3** (1500 VDC) → RS-485 aislado |
| **RS-485** | **THVD1450** + aislador digital **ISO7731** (TX / RX / DE-RE) |
| **Radio** | **Quectel FGH100MAAMD** (FGH100M, Morse Micro MM6108) — Wi-Fi HaLow sub-GHz |
| **Procesamiento** | **ESP32-S3-WROOM-1-N4** + zócalo microSD para histórico |
| **Tiempo** | RTC **PCF85063A** (I²C) + reloj de metrología RN8302B a **8.192 MHz** |
| **Respaldo** | Supercapacitor 30 F para *Last Gasp* |
| **Entrada de potencia** | MOV, fusible, puente rectificador **BR-50126V-4P0G56**, conector **HX PJ-320A-3P DIP** |

**Topología de medición soportada:** `3P4W` y `3P3W`.

> 📄 La especificación completa, con todas las derivaciones de sensado, reglas de convivencia entre bloques, mases (AGND / GND_DIG / GND_ISO) y la lista de compra, está en [`documentation/Especificacion de Arquitectura.md`](documentation/Especificacion%20de%20Arquitectura.md) — **léela antes de tocar el esquemático**.

---

## 🗂️ Estructura del repositorio

```
Analizador trifasico IoT/
├── README.md
├── .gitignore
├── .gitattributes
│
├── hardware/
│   ├── altium/                    ← Proyecto Altium Designer (fuente de verdad del diseño)
│   │   ├── Analizador_trifasico_IoT_pcb.PrjPcb      ← archivo de proyecto (ábrelo con esto)
│   │   ├── Analizador_trifasico_IoT_pcb.PrjPcbStructure
│   │   ├── MAIN.SchDoc            ← hoja raíz (jerarquía)
│   │   ├── THREE PHASES.SchDoc    ← entrada de potencia trifásica
│   │   ├── POWER.SchDoc           ← alimentación AC/DC y riales
│   │   ├── MEASURES.SchDoc        ← AFE RN8302B + sensado
│   │   ├── MCU.SchDoc             ← ESP32-S3, RS-485, microSD
│   │   └── Analizador_PCB.PcbDoc  ← layout de la PCB
│   │
│   └── libraries/                 ← Bibliotecas de componentes (compartidas)
│       ├── Library_Analizador.LibPkg   ← paquete de biblioteca (empaqueta las 3 siguientes)
│       ├── Schlib1.SchLib              ← símbolos esquemáticos (fuente editable)
│       ├── PcbLib1.PcbLib              ← footprints PCB (fuente editable)
│       └── Library_Analizador.IntLib   ← biblioteca integrada compilada
│
├── documentation/                 ← Documentación del producto
│   ├── Especificacion de Arquitectura.md   ← especificación técnica v2.0
│   ├── diagrama de bloques.pdf
│   └── Diagrama de bloquesv2.pdf
│
└── references/                    ← Referencias técnicas (datasheets, notas, diseños de referencia)
    ├── datasheets/                ← datasheets de componentes
    ├── application-notes/         ← notas de aplicación
    └── reference-designs/         ← diseños de referencia y eval boards
```

---

## 🔌 Hojas del esquemático

| Hoja | Archivo | Contenido |
|---|---|---|
| 1 | `MAIN.SchDoc` | Hoja raíz. Solo contiene los *sheet symbols* hacia las demás. |
| 2 | `THREE PHASES.SchDoc` | Entrada de red trifásica: MOV, fusible, puente rectificador, conector, CT/Rogowski. |
| 3 | `POWER.SchDoc` | AC/DC, buck AP63203, LDO, ferrites, supercapacitor, aisladores, RS-485. |
| 4 | `MEASURES.SchDoc` | RN8302B, aislador ISO7741, crystal 8.192 MHz, divisores, CTs. |
| 5 | `MCU.SchDoc` | ESP32-S3-WROOM-1-N4, USB-C, RS-485, zócalo microSD. |

---

## 📚 Referencias técnicas

### `references/datasheets/`

| Archivo | Componente |
|---|---|
| `RN8302B_Datasheet_v3.pdf` | RENERGY RN8302B — AFE metrológico |
| `RN8302B_User_Manual_v1.1.pdf` | RENERGY RN8302B — manual de usuario |
| `ESP32-S3_Datasheet_en.pdf` | Espressif ESP32-S3 — SoC |
| `ESP32-S3_Technical_Reference_Manual_en.pdf` | Espressif ESP32-S3 — manual técnico de referencia |
| `ESP32-S3-WROOM_Module.pdf` | Espressif ESP32-S3-WROOM-1-N4 — módulo |
| `ISO7741DWR_Datasheet.pdf` | TI ISO7741 — aislador digital |
| `Supercapacitor_Datasheet.pdf` | Supercapacitor 30 F |

### `references/application-notes/`

| Archivo | Contenido |
|---|---|
| `TI_DUF27A_Application_Note.pdf` | TI DUF27A — note de aplicación |
| `TI_DUF27A_Layout.pdf` | TI DUF27A — guidelines de layout |
| `wifi-halow-module-for-xiao.md` | Notas del módulo Wi-Fi HaLow para XIAO |

### `references/reference-designs/`

| Carpeta | Contenido |
|---|---|
| `EVAL-ADE9430/` | Analog Devices EVAL-ADE9430 — esquemático, layout y user guide (referencia de AFE trifásico) |
| `WI-FI_HALOW_FGH100M_EXT01_V30/` | Módulo radio HaLow: PCB original en KiCad, esquemático PDF e importación a Altium |
| `HX PJ-320A-3P DIP/` | Conector de audio 3.5 mm (HX PJ-320A-3P DIP) — footprint y símbolo Altium |
| `TI_DCG_v3/` | `TI_DCG_v3_Gerber_ODB.zip` — archivos Gerber/ODB++ de referencia |

---

## 🚀 Cómo empezar a colaborar

### 1. Clonar

```bash
git clone git@github.com:TU-USUARIO/Analizador-Trifasico-IoT.git
cd Analizador-Trifasico-IoT
```

### 2. Configurar las bibliotecas en Altium Designer

Los esquemáticos referencian `Library_Analizador.IntLib`. Sin esta biblioteca, Altium mostrará los símbolos pero **no podrá actualizarlos** (*Update from Library*).

En **Altium Designer 26**:

1. `Preferences → Data Management → Libraries` → botón **Add** → seleccionar
   `hardware/libraries/Library_Analizador.LibPkg`
2. `Preferences → Data Management → Project-based Libraries` → **Add** → seleccionar la carpeta
   `hardware/libraries/`
3. Reiniciar Altium

> 💡 Los **footprints ya están embebidos** dentro de `Analizador_PCB.PcbDoc`, por lo que el layout se abre y se edita correctamente incluso sin instalar `PcbLib1.PcbLib`.

### 3. Abrir el proyecto

`File → Open` → `hardware/altium/Analizador_trifasico_IoT_pcb.PrjPcb`

---

## ⚠️ Reglas de colaboración (importante)

Los archivos `.SchDoc`, `.PcbDoc`, `.SchLib` y `.PcbLib` son **binarios** (contenedores OLE2). Esto implica:

| Git **SÍ** puede | Git **NO** puede |
|---|---|
| Guardar el historial completo | Mostrar diffs de contenido (`Binary files differ`) |
| Revertir a cualquier versión anterior | Fusionar cambios automáticamente |
| Crear ramas independientes | Resolver conflictos de merge |

### Reglas para evitar conflictos

1. **Una persona por archivo a la vez.** En especial `Analizador_PCB.PcbDoc` — es monolítico.
2. **Una rama por tarea**, nunca edites `main` directamente:
   ```bash
   git checkout -b feature/ct-input-stage
   ```
3. **Cierra Altium antes de `git pull` / `git checkout`.** Altium mantiene los archivos abiertos y puede sobrescribirlos al hacer el pull.
4. **Commits pequeños y frecuentes.** Es más fácil revertir 3 commits que 1 commit con 200 cambios.
5. **Si hay conflicto de merge**, no intentes resolverlo a mano sobre el binario. Usa:
   ```bash
   git merge -X ours rama-del-companero
   ```
   y luego aplica los cambios pendientes en Altium manualmente.

### Flujo recomendado

```bash
git pull --rebase origin main      # sincronizar antes de trabajar
git checkout -b feature/mi-tarea
# ... trabajar en Altium ...
git add hardware/altium/
git commit -m "MEASURES: agrega divisor de tension VA"
git push -u origin feature/mi-tarea
# → Pull Request en GitHub → revisión → merge a main
```

---

## 📄 Convenciones de commits

```
<hoja o bloque>: <descripcion corta en imperativo>

THREE PHASES: agrega MOV clase 510 VAC
MEASURES: cambia divisor a 1M/1M
POWER: sustituye LDO por TLV757P
PCB: enrutado de zona de potencia
```

---

## 📊 Estado del proyecto

- [x] Arquitectura eléctrica especificada y normalizada (v2.0)
- [x] Esquemáticos de las 5 hojas
- [x] Layout de PCB
- [x] Bibliotecas de componentes
- [x] Documentación técnica y referencias
- [ ] **MCU definitivo** — pendiente de decisión (la arquitectura deja el bloque abierto a propósito)
- [ ] Modelo exacto de CT / Rogowski — familia seleccionada, modelo por definir
- [ ] Red exacta del divisor de tensión de precisión — familia seleccionada
- [ ] Validaciones obligatorias antes de congelar la PCB (ver §21 de la especificación)
- [ ] Normativa aplicable (ver §22 de la especificación)

---

## 📄 Licencia

Proyecto académico — Universidad Nacional de Colombia, Facultad de Ingeniería.
Uso académico. Verificar autorización institucional antes de cualquier distribución pública.

---

## 🔗 Enlaces útiles

- [Documentación oficial de Altium — Git Version Control](https://www.altium.com/documentation/altium-designer/using-external-version-control/git)
- [KiCad — importación de archivos Altium](https://dev-docs.kicad.org/en/import-formats/altium/index.html)
- [Altium Designer — diferencias entre SVN y Git](https://www.altium.com/documentation/altium-designer/using-external-version-control)
