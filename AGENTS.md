# AGENTS.md — Instrucciones para agentes de IA

Este archivo describe cómo debe trabajar un agente de IA dentro de este repositorio.
Léelo completo antes de tocar cualquier archivo. Está escrito para un proyecto de
**hardware con archivos binarios**, donde un error de Git puede costar días de trabajo.

---

## 1. Contexto del proyecto

| Dato | Valor |
|---|---|
| Proyecto | **Analizador Trifásico IoT** — instrumento de medición eléctrica trifásica con conectividad IoT |
| Contexto | Proyecto académico, Universidad Nacional de Colombia, Facultad de Ingeniería |
| Equipo | 2 personas (`juan-villota-b` + un compañero) |
| Herramienta EDA | **Altium Designer 26** (`C:\Program Files\Altium\AD26`) |
| Repositorio | `git@github.com:juan-villota-b/Analizador-Trifasico-IoT.git`, rama por defecto `main` |
| Raíz local | `C:\Users\ASUS\Documents\Semestre_VIII\Analizador trifasico IoT` |
| Idioma | **Todo en español**: respuestas, documentación, mensajes de commit, nombres de rama sin tildes |

El proyecto tiene 5 hojas jerárquicas más un PCB, y una única biblioteca integrada.
No hay build system, ni tests, ni CI: la "compilación" es el *Compile Project* de Altium.

---

## 2. Fuentes de verdad (en orden de prioridad)

1. **`documentation/Diagrama de bloquesv2.pdf`** (07/10/2026) → **diseño vigente**.
2. **`hardware/altium/*.SchDoc`** → lo realmente capturado. Si el diagrama y el
   esquemático discrepan, **no corrijas el esquemático por tu cuenta**: repórtalo.
3. **`README.md`** → arquitectura por bloque, presupuesto de corriente, mapa de interfaces.
4. **`CONTRIBUTING.md`** → flujo de Git del equipo (léelo antes de proponer comandos).

### Componentes obsoletos: no los reintroduzcas

| En la arquitectura anterior | En el diseño V2 |
|---|---|
| Mornsun LD10-26B05 | **Hi-Link HLK-10M05** |
| TLV75733 como LDO del AFE | *(eliminado)* |
| THVD1450 + ISO7731 + B0503S-1WR3 | **VISOM RSM3485PCT** (módulo integrado) |
| ISO7721 / ISO7731 | **ISO7741** |
| PCF85063A (RTC I²C) | *(no está en el diseño)* |
| MCU "pendiente / STM32" | **ESP32-S3-WROOM-1-N4** *(decidido)* |
| SM712, MOV-20D821K, GDT | **MOV-14D471K** + fusibles |

---

## 3. Mapa del repositorio

```
Analizador trifasico IoT/
├── AGENTS.md                       ← este archivo
├── README.md                       ← documentación principal
├── CONTRIBUTING.md                 ← guía de Git para el equipo
├── .gitignore / .gitattributes
│
├── hardware/
│   ├── altium/                     ← PROYECTO ALTIUM (fuente de verdad del hardware)
│   │   ├── Analizador_trifasico_IoT_pcb.PrjPcb        ← punto de entrada
│   │   ├── Analizador_trifasico_IoT_pcb.PrjPcbStructure
│   │   ├── MAIN.SchDoc             ← hoja raíz (solo sheet symbols)
│   │   ├── THREE PHASES.SchDoc     ← ⚠️ el espacio en el nombre es intencional
│   │   ├── POWER.SchDoc
│   │   ├── MEASURES.SchDoc
│   │   ├── MCU.SchDoc
│   │   └── Analizador_PCB.PcbDoc   ← layout (monolítico, un solo dueño)
│   │
│   └── libraries/
│       ├── Library_Analizador.LibPkg   ← proyecto de biblioteca
│       ├── Schlib1.SchLib              ← símbolos esquemáticos (fuente)
│       ├── PcbLib1.PcbLib              ← footprints (fuente)
│       └── Library_Analizador.IntLib   ← compilada (⚠️ hoy ausente, ver §9)
│
├── documentation/
│   └── Diagrama de bloquesv2.pdf       ← diagrama vigente
│
└── references/
    ├── datasheets/
    ├── application-notes/
    └── reference-designs/
```

---

## 4. Reglas duras (no negociables)

### 4.1 Archivos binarios de Altium

`.SchDoc`, `.PcbDoc`, `.SchLib`, `.PcbLib` e `.IntLib` son contenedores **OLE2 binarios**.

- **Nunca** los edites a mano, con scripts, ni "arreglando" bytes.
- **Nunca** intentes resolver un conflicto de merge editando el binario.
- Git no puede diffearlos ni fusionarlos: `Binary files differ` es lo esperado.
- La única forma válida de cambiarlos es **abrir Altium, editar, guardar, cerrar**.

### 4.2 Cerrar Altium antes de cualquier operación de Git

`git pull`, `git checkout`, `git merge` con Altium abierto = el archivo se reemplaza
en disco pero Altium lo sobrescribe al guardar → **se pierde el trabajo del compañero**.
Esto ya ocurrió dos veces en este proyecto.

### 4.3 No reescribir historia

- **Prohibido** `git push --force` / `--force-with-lease`.
- **Prohibido** `git reset --hard` sobre `main` o sobre ramas publicadas.
- **Prohibido** `rebase` de ramas ya subidas (el equipo usa `merge`).
- `git revert` sí está permitido, pero **pide confirmación antes**.

### 4.4 Nombres de archivo que no se tocan

- **`THREE PHASES.SchDoc`** conserva el espacio. Renombrarlo rompe
  `Analizador_trifasico_IoT_pcb.PrjPcbStructure` y la jerarquía del proyecto.
- Los datasheets van en **ASCII**: `RN8302B_Datasheet_v3.pdf`, no `RN8302B(v3).pdf`.
  No subir duplicados exactos (verificar SHA256 antes de agregar).

### 4.5 Una sola biblioteca

Existe **un único concepto de biblioteca**: `Library_Analizador`
(`Schlib1.SchLib` + `PcbLib1.PcbLib` → `LibPkg` → `IntLib`).
**No crees** `Schlib2`, `PcbLib2`, `Library_B`, ni bibliotecas paralelas.
No borres ni "dedupliques" ninguno de estos archivos: no son duplicados, son
etapas distintas de la misma cadena.

### 4.6 Qué no se versiona

Ya está en `.gitignore`; no lo fuerces con `git add -f`:
`History/`, `__Previews/`, `Project Logs for*/`, `Project Outputs for*/`,
`*.LOG`, `*.Cache`, `*.bak`, `*.lck`, `*.tmp`.

Sí se versionan: `.SchDoc`, `.PcbDoc`, `.SchLib`, `.PcbLib`, `.IntLib`, PDFs de
datasheets y diseños de referencia.

### 4.7 No inventar hardware

- No agregues componentes, footprints, pines ni valores que no estén en el
  diagrama V2 o en un datasheet de `references/`.
- Si falta información (modelo de CT, red exacta del divisor, versión del módulo
  HaLow), **dilo**; no rellenes con suposiciones.
- No afirmes que algo "ya está en el esquemático" sin verificarlo.

---

## 5. Cadena de bibliotecas (el error más caro del repo)

```
Schlib1.SchLib  ──┐
                  ├──► Library_Analizador.LibPkg ──► Library_Analizador.IntLib
PcbLib1.PcbLib  ──┘                                        │
                                                    (compilada)
                                                           ▼
                              Las 5 hojas .SchDoc referencian esta IntLib
```

Los esquemáticos tienen `SourceLibraryName=Library_Analizador.IntLib`. Sin esa
IntLib instalada, Altium muestra los símbolos pero **`Tools → Update from Library`
no funciona**.

### Procedimiento al modificar la biblioteca

1. `git pull` con Altium cerrado. Avisar al compañero.
2. Abrir **`hardware/libraries/Library_Analizador.LibPkg`** (no el `.PrjPcb`).
3. Editar `Schlib1.SchLib` (símbolo) y/o `PcbLib1.PcbLib` (footprint).
4. `Ctrl+S` en cada fuente.
5. `Project → Compile Integrated Library Library_Analizador.LibPkg`.
6. **Copiar la salida a la raíz** (paso obligatorio, si no el repo queda con la vieja):
   ```powershell
   cd hardware\libraries
   Copy-Item "Project Outputs for Library_Analizador\Library_Analizador.IntLib" "Library_Analizador.IntLib" -Force
   ```
7. `git status` debe mostrar **las fuentes y la IntLib** modificadas.
8. `git add hardware/libraries/` → commit `LIB: ...` → `git push`.

### Después del cambio

| Cambiaste | Qué falta |
|---|---|
| Un símbolo | En cada hoja: `Tools → Update from Library` |
| Un footprint | En el PCB: `Tools → Update From PCB Libraries` |

---

## 6. Flujo de Git del equipo

### Reglas

| Regla | Motivo |
|---|---|
| Una rama = una tarea | Permite revertir una sola cosa |
| Nunca dos personas en la misma rama | Se pisan los commits |
| Nunca el mismo archivo en dos ramas | Al mergear, uno pierde su cambio |
| Mergear de a un PR | Dos PRs simultáneos = conflictos de binarios |
| Nunca trabajar en `main` | `main` debe abrir y compilar siempre |

Los `.md` y `.PrjPcb` **sí** se pueden editar en paralelo (son texto).

### Ciclo

```bash
git checkout main
git pull
git checkout -b feature/mi-tarea
# ... trabajar en Altium, guardar, CERRAR ...
git status
git add .
git commit -m "MEASURES: ajusta rango de ADC de corriente"
git push -u origin feature/mi-tarea
# → PR en GitHub → revisión → Merge → borrar rama
```

Si `main` avanzó antes del merge:

```bash
git checkout main && git pull
git checkout feature/mi-tarea
git merge main          # NO rebase
git push
```

### Nombres de rama

`feature/...`, `fix/...`, `lib/...`, `docs/...` — minúsculas, sin tildes, sin espacios.

### Commits

```
<bloque>: <descripción corta en imperativo>
```

Prefijos: `THREE PHASES:`, `POWER:`, `MEASURES:`, `MCU:`, `PCB:`, `LIB:`, `DOC:`, `REF:`.

### Dos conceptos que el usuario suele confundir — explícalos si aparecen

- `git merge main` desde una rama **sin commits propios** = *fast-forward*: no crea
  commit, y un `git commit` posterior dice correctamente **"nothing to commit"**.
- `git push` actualiza **solo la rama actual**. `main` solo cambia al mergear el PR
  en GitHub (o al hacer push estando en `main`).

---

## 7. Entorno (Windows + PowerShell)

| Tema | Detalle |
|---|---|
| Git | `C:\Program Files\Git\cmd\git.exe` (v2.56+) |
| SSH | clave ed25519 en `%USERPROFILE%\.ssh`, ya registrada en GitHub |
| Política de ejecución | bloquea `.ps1`; usar `powershell -ExecutionPolicy Bypass -File script.ps1` |
| UTF-8 | la consola **manglea** las tildes, pero los archivos son UTF-8 sin BOM y están bien |
| `gh` CLI | **no instalado** — no propongas comandos `gh` |
| Rutas con espacios | siempre entre comillas (`"hardware/altium/..."`, `"THREE PHASES.SchDoc"`) |
| Altium | `C:\Program Files\Altium\AD26` (no automatizable desde aquí) |

Comandos de verificación útiles:

```powershell
git status --short --branch
git log --oneline -10
git ls-files hardware/libraries
git diff --stat
```

---

## 8. Checklist antes de decir "listo"

- [ ] `git status` muestra **solo** los archivos que se querían cambiar.
- [ ] No hay `History/`, `__Previews/`, `Project Logs for*/` ni `.LOG` en el commit.
- [ ] Si se tocó una librería: **fuentes + `IntLib` recompilada** en el commit.
- [ ] Si se agregó un archivo, el árbol de `README.md` §"Estructura del repositorio" sigue siendo correcto.
- [ ] El proyecto abre y compila en Altium (lo verifica el humano; dilo explícitamente).
- [ ] El cambio es coherente con el **diagrama V2**, no con la arquitectura anterior.
- [ ] Todo lo escrito está en español.

---

## 9. Estado actual y temas abiertos

### 🔴 Decisión pendiente: `Library_Analizador.IntLib`

El archivo fue borrado en el commit `535a0f2` ("Borrar duplicado") porque se creyó
duplicado de `Schlib1.SchLib` / `PcbLib1.PcbLib`. **No lo es**: es el artefacto
compilado que referencian ~98 componentes en MCU / MEASURES / POWER / THREE PHASES.
Hoy no está ni en disco ni en el índice de Git (aunque `.gitignore` lo tiene
whitelisteado con `!hardware/libraries/*.IntLib`).

Opciones planteadas, **sin decidir**:

- **A) Restaurar:** `git revert 535a0f2` → `git push`, luego recompilar el LibPkg y
  copiar la salida sobre `hardware/libraries/Library_Analizador.IntLib` para que el
  cambio de resistencia de `aad2cb8` se propague.
- **B) Ignorar la IntLib:** agregar `*.IntLib` a `.gitignore` (y quitar la excepción
  `!hardware/libraries/*.IntLib`), actualizar `README.md` y `CONTRIBUTING.md` con el
  paso de "compílala localmente".

**No elijas por tu cuenta.** Pregunta al usuario A o B antes de tocar nada.

### Otros pendientes conocidos

- **Quectel FGH100M** todavía **no está** en `MCU.SchDoc` (sí está en README y en el diagrama).
- `POWER.SchDoc` tiene **`HLK-5M03B`**, mientras el diagrama pide **3.3 V @ 1 A**.
  Es una inconsistencia abierta; repórtala, no la "arregles" sola.
- Modelo exacto de CT / Rogowski y red del divisor de tensión: **por definir**.
- Ruteo del layout de la PCB: en curso.
- Ramas sin mergear que pueden revisarse: `measures/componentes-chip-medicion`,
  `three-phases/actualizacion_de_las_entradas`.

### Origen de las referencias

Los datasheets y diseños de referencia se copian desde
`C:\Users\ASUS\Documents\Semestre_VIII\Analizador de redes`, con nombres
normalizados a ASCII y sin duplicados exactos (comparar SHA256).

---

## 10. Cómo debe responder el agente

- **En español**, claro y conciso. Explica el comando antes de ejecutarlo si es
  destructivo o difícil de deshacer.
- **Pide confirmación explícita** antes de: `revert`, `reset`, borrar o mover archivos,
  renombrar algo, recompilar/copiar la `IntLib`, o cerrar ramas.
- **Nunca** digas que un cambio quedó bien en Altium si no se abrió Altium: di
  "guardado en disco, falta verificar en Altium".
- Cuando el usuario esté aprendiendo Git, explica **por qué** pasa algo
  (fast-forward, push por rama, conflicto binario) en una o dos frases.
- Si detectas una inconsistencia de diseño, **repórtala con rutas y nombres exactos**;
  no la corrijas silenciosamente.
- Usa rutas completas al referirte a archivos.
