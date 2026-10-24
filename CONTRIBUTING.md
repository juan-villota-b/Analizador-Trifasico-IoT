# Guía de contribución

Cómo trabajar en este repositorio sin pisar el trabajo de los demás.

> **Regla de oro:** los archivos de Altium (`.SchDoc`, `.PcbDoc`, `.SchLib`, `.PcbLib`) son **binarios**. Git no puede fusionarlos automáticamente. Por eso hay que coordinarse.

---

## 1. Configuración inicial (solo una vez)

### 1.1 Instalar Git

```powershell
winget install --id Git.Git -e --source winget
```

Cierra y vuelve a abrir la terminal después de instalar.

### 1.2 Generar tu clave SSH

```powershell
ssh-keygen -t ed25519 -C "tu-email@ejemplo.com"
```

Presiona `Enter` tres veces (ruta por defecto, sin passphrase).

### 1.3 Copiar la clave pública

**PowerShell:**
```powershell
Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub | Set-Clipboard
```

**cmd:**
```cmd
type %USERPROFILE%\.ssh\id_ed25519.pub | clip
```

**Git Bash:**
```bash
cat ~/.ssh/id_ed25519.pub | clip
```

**O la que siempre funciona:**
```cmd
notepad %USERPROFILE%\.ssh\id_ed25519.pub
```
Selecciona todo (`Ctrl+E`), copia (`Ctrl+C`).

### 1.4 Registrarla en GitHub

Ve a https://github.com/settings/keys → **New SSH key** → ponle un título (ej. "PC portátil") → pega la clave → **Add SSH key**.

Verifica:
```powershell
ssh -T git@github.com
```
Debe responder: `Hi TU-USUARIO! You've successfully authenticated...`

### 1.5 Clonar el repositorio

```powershell
git clone git@github.com:TU-USUARIO/Analizador-Trifasico-IoT.git
cd Analizador-Trifasico-IoT
```

### 1.6 Configurar tu identidad

```powershell
git config user.name "Tu Nombre"
git config user.email "tu-email@ejemplo.com"
```

> Usa el **mismo email** que tienes en GitHub, si no tus commits no se te atribuyen.

### 1.7 Instalar las librerías en Altium ⚠️

Sin esto no funciona *Update from Library*.

1. En Altium: `Preferences → Data Management → Libraries` → **Add** → seleccionar
   `hardware/libraries/Library_Analizador.LibPkg`
2. `Preferences → Data Management → Project-based Libraries` → **Add** → seleccionar la carpeta
   `hardware/libraries/`
3. Reiniciar Altium

---

## 2. Flujo diario

```bash
git pull
git add .
git commit -m "descripcion del cambio"
git push
```

### ⚠️ Siempre, en este orden

| Paso | Acción |
|---|---|
| 1 | `git pull` — **con Altium cerrado** |
| 2 | Abrir Altium y trabajar |
| 3 | Guardar y **cerrar Altium** |
| 4 | `git status` — revisar qué cambió |
| 5 | `git add .` |
| 6 | `git commit -m "..."` |
| 7 | `git push` |
| 8 | Avisar al equipo |

> **Si Altium está abierto al hacer `git pull`**, el archivo se reemplaza en disco pero Altium lo sobrescribe al guardar → se pierde el trabajo del otro.

---

## 3. Caso A — Modificaste un esquemático

Ejemplo: cambiaste el divisor de tensión en `MEASURES.SchDoc`.

```bash
git pull
```

**En Altium:**
1. Abrir `hardware/altium/Analizador_trifasico_IoT_pcb.PrjPcb`
2. Editar la hoja
3. `Project → Compile Project` (verificar que no haya errores)
4. Guardar (`Ctrl+S`) y **cerrar Altium**

**En la terminal:**
```bash
git status
```
Debe mostrar solo lo que tocaste:
```
modified:   hardware/altium/MEASURES.SchDoc
```

```bash
git add .
git commit -m "MEASURES: ajusta divisor de tension VA a 1M/1k"
git push
```

**Avisa al equipo:** *"Subí cambio en MEASURES.SchDoc"*

---

## 4. Caso B — Modificaste una librería ⚠️ (requiere un paso extra)

### Entiende la cadena primero

```
Schlib1.SchLib  ──┐
                  ├──► Library_Analizador.LibPkg ──► Library_Analizador.IntLib
PcbLib1.PcbLib  ──┘                                        │
                                                     (compilada)
                                                           ▼
                                    Las 5 hojas .SchDoc referencian esta
```

- **`Schlib1.SchLib`** y **`PcbLib1.PcbLib`** → son las **fuentes editables**
- **`Library_Analizador.LibPkg`** → proyecto que empaqueta las dos fuentes
- **`Library_Analizador.IntLib`** → **archivo compilado** que usan los esquemáticos

> ❌ **Error más común:** editar el `.SchLib` y subirlo sin recompilar la `.IntLib`. Los esquemáticos siguen viendo el símbolo viejo y nadie entiende por qué.

### Procedimiento

**1. Sincronizar y avisar**
```bash
git pull
```
Avisa: *"Voy a tocar la librería, no la editen"*

**2. En Altium: abrir el LibPkg (no el PrjPcb)**
```
File → Open → hardware/libraries/Library_Analizador.LibPkg
```
Si abres el `.PrjPcb` no podrás compilar la biblioteca.

**3. Editar**
- Símbolo esquemático → doble clic en `Schlib1.SchLib`
- Footprint → doble clic en `PcbLib1.PcbLib`

**4. Guardar las fuentes** (`Ctrl+S` en cada una)

**5. Recompilar la integrada**
```
Project → Compile Integrated Library Library_Analizador.LibPkg
```

Se genera:
```
hardware/libraries/Project Outputs for Library_Analizador/Library_Analizador.IntLib
```

**6. Copiar la IntLib nueva a su lugar** ⚠️ paso obligatorio
```powershell
cd hardware\libraries
Copy-Item "Project Outputs for Library_Analizador\Library_Analizador.IntLib" "Library_Analizador.IntLib" -Force
```

> El `.gitignore` excluye `Project Outputs for*/`, así que **solo se versiona la copia de la raíz**. Si no copias, el repo se queda con la IntLib vieja.

**7. Verificar que están las dos**
```bash
git status
```
```
modified:   hardware/libraries/Schlib1.SchLib
modified:   hardware/libraries/Library_Analizador.IntLib   ← debe estar
```

**8. Subir**
```bash
git add hardware/libraries/
git commit -m "LIB: agrega simbolo CT 100A y recompila IntLib"
git push
```

**9. Avisar al equipo:** *"Actualicé la librería — hagan pull y refresquen la biblioteca en Altium"*

### Lo que hacen los demás al recibir el cambio

```bash
git pull
```

Y en Altium: `Preferences → Data Management → Libraries` → seleccionar `Library_Analizador.LibPkg` → **Refresh** → reiniciar Altium.

### Después de cambiar un símbolo o un footprint

| Cambiaste | Qué falta hacer |
|---|---|
| Un símbolo | En cada hoja: `Tools → Update from Library` (los componentes ya colocados no se actualizan solos) |
| Un footprint | En el PCB: `Tools → Update From PCB Libraries` |

⚠️ Cambiar la geometría de un footprint puede romper el ruteo existente. Revisa el PCB después.

---

## 5. Si el `push` es rechazado

```
! [rejected] main -> main (fetch first)
error: failed to push some refs
```

Significa que alguien subió cambios mientras trabajabas:

```bash
git pull --rebase
git push
```

### Si hay conflicto en un archivo binario

Git dirá `CONFLICT (content): Merge conflict in ...MEASURES.SchDoc`.

**Nunca edites el `.SchDoc` a mano.** Elige un lado:

```bash
# Quedarte con la versión de GitHub (la del compañero)
git checkout --theirs hardware/altium/MEASURES.SchDoc
git add hardware/altium/MEASURES.SchDoc
git rebase --continue

# O quedarte con la tuya
git checkout --ours hardware/altium/MEASURES.SchDoc
git add hardware/altium/MEASURES.SchDoc
git rebase --continue
```

Después, **quien perdió su cambio lo vuelve a aplicar manualmente en Altium** y hace un commit nuevo. Con binarios no hay forma automática.

---

## 6. Reglas de convivencia

| ✅ Se puede a la vez | ❌ NO se puede a la vez |
|---|---|
| Hojas distintas (`POWER.SchDoc` vs `MCU.SchDoc`) | La misma hoja |
| Leer documentación mientras otro edita | El mismo `Analizador_PCB.PcbDoc` |
| | La misma librería (`Schlib1` / `PcbLib1`) |

**Antes de empezar, pregunten: "¿quién toca qué?".** Si los dos necesitan `MEASURES.SchDoc`, uno espera.

Otras reglas:
1. **Commits pequeños y frecuentes.** Revertir 3 commits es fácil; revertir uno de 200 cambios no.
2. **Nunca trabajar directo en `main`** si son más de 2 personas — usa ramas.
3. **Cerrar Altium antes de cualquier operación de Git.**

---

## 7. Ramas y Pull Requests

### ¿Para qué sirven si los binarios no se pueden fusionar?

Las ramas **no** permiten fusionar archivos de Altium. Sirven para otra cosa:

| Beneficio | Explicación |
|---|---|
| **`main` siempre abre y compila** | Si trabajas a medias en `main`, tu compañero recibe un proyecto roto |
| **Descartar experimentos** | Si un enfoque falla, borras la rama y `main` nunca se enteró |
| **Revisión antes de integrar** | El PR muestra qué archivos cambian → se detecta si falta la `.IntLib` |
| **Revertir de golpe** | `git revert -m 1 <merge>` deshace una funcionalidad completa |

### El ciclo completo

```bash
# 1. Actualizar main (Altium cerrado)
git checkout main
git pull

# 2. Crear la rama
git checkout -b feature/etapa-ct

# 3. Trabajar en Altium... guardar... CERRAR

# 4. Verificar y subir
git status
git add .
git commit -m "MEASURES: agrega etapa de entrada para CT"
git push -u origin feature/etapa-ct
```

**5.** En GitHub aparece el banner **Compare & pull request** → clic → título → **Create pull request**

**6.** El otro revisa en **Files changed**:
```
MEASURES.SchDoc                    modified
Schlib1.SchLib                     modified
Library_Analizador.IntLib          modified   ← si tocó librería, debe estar
```

**7.** **Merge pull request** → **Confirm merge**

**8.** Limpiar:
```bash
git checkout main
git pull
git branch -d feature/etapa-ct
git push origin --delete feature/etapa-ct
```

**9.** El otro se actualiza:
```bash
git checkout main
git pull
```

### Antes de pedir el merge, si `main` avanzó

```bash
git checkout main
git pull
git checkout feature/mi-rama
git merge main          # integra lo nuevo de main en tu rama
git push
```

> Usa `git merge main`. No uses `rebase`: obliga a `push --force`, que es riesgoso.

### Reglas

| Regla | Motivo |
|---|---|
| **Una rama = una tarea** | Si mezclas dos, no puedes revertir una sola |
| **Nunca dos personas en la misma rama** | Se pisan los commits |
| **Nunca el mismo archivo en dos ramas** | Al mergear, uno pierde su cambio |
| **Mergear de a uno** | Dos PRs simultáneos = conflictos asegurados |

**Excepción:** los archivos de **texto** (`.md`, `.PrjPcb`) sí se pueden editar en paralelo — Git los fusiona solo.

### Nombres de rama

```bash
feature/etapa-ct        # funcionalidad nueva
fix/divisor-va          # corrección
lib/simbolo-ct-100a     # librerías
docs/actualiza-readme   # documentación
```

Sin tildes, sin espacios, en minúsculas.

### Si hay conflicto al mergear

GitHub dirá *"This branch has conflicts that must be resolved"*. Con binarios no se resuelve en la web:

```bash
git checkout main && git pull
git checkout feature/mi-rama
git merge main

# elegir un lado:
git checkout --ours   hardware/altium/MEASURES.SchDoc   # mi versión
git checkout --theirs hardware/altium/MEASURES.SchDoc   # la de main

git add .
git commit
git push
```

Quien perdió su cambio lo **vuelve a aplicar a mano en Altium**.

### Errores comunes

| Situación | Solución |
|---|---|
| Trabajé en `main` sin querer (sin push) | `git checkout -b feature/mi-tarea` → `git checkout main` → `git reset --hard origin/main` |
| No aparece el botón de PR | **Pull requests** → **New pull request** → `base: main`, `compare: tu-rama` |
| Me equivoqué de nombre | `git branch -m nombre-correcto` |
| Quiero ver en qué rama estoy | `git branch` |

### Resumen imprimible

```
EMPEZAR
  git checkout main
  git pull
  git checkout -b feature/mi-tarea

TERMINAR (Altium cerrado)
  git status
  git add .
  git commit -m "BLOQUE: que hice"
  git push -u origin feature/mi-tarea

EN GITHUB
  Compare & pull request -> Create -> Merge

LIMPIAR
  git checkout main && git pull
  git branch -d feature/mi-tarea
  git push origin --delete feature/mi-tarea

SI main AVANZO ANTES DEL MERGE
  git checkout main && git pull
  git checkout feature/mi-tarea
  git merge main
  git push
```

---

## 8. Convención de mensajes de commit

```
<bloque>: <descripcion corta en imperativo>
```

| Prefijo | Cuándo |
|---|---|
| `THREE PHASES:` | Entrada trifásica, protección |
| `POWER:` | Alimentación, supercaps, rieles |
| `MEASURES:` | RN8302B, ISO7741, acondicionamiento |
| `MCU:` | ESP32-S3, RS-485, microSD, USB |
| `PCB:` | Layout |
| `LIB:` | Librerías |
| `DOC:` | README, especificación, diagramas |
| `REF:` | Datasheets y referencias |

Ejemplos:
```
POWER: dimensiona red de supercapacitores
MCU: conecta SPI de la microSD
LIB: recompila IntLib con simbolo CT 100A
DOC: actualiza presupuesto de corriente
```

---

## 9. Recuperar una versión anterior (salvavidas)

```bash
# Ver el historial de un archivo
git log --oneline -- hardware/altium/MEASURES.SchDoc

# Recuperar la versión de un commit específico
git checkout abc1234 -- hardware/altium/MEASURES.SchDoc

# Ver qué cambió en un commit (para binarios solo dice "Binary files differ")
git show abc1234 --stat
```

Si algo se rompió y no sabes cuándo:
```bash
git log --oneline --all
git checkout abc1234          # ir a ese estado (modo detached)
git checkout main             # volver
```

---

## 10. Alternativa sin terminal: GitHub Desktop

Si prefieres botones:

1. Descargar https://desktop.github.com
2. `File → Clone repository` → `Analizador-Trifasico-IoT`
3. Trabajar en Altium, guardar y **cerrar Altium**
4. En GitHub Desktop:
   - **Changes** → revisar la lista de archivos
   - Escribir el mensaje en **Summary**
   - **Commit to main**
   - **Push origin** ← esto sube
5. Para traer cambios: **Fetch origin** / **Pull origin**

Hace lo mismo que los comandos, pero te muestra visualmente qué archivos tocaste antes de subir. Útil para no subir basura por accidente.

---

## 11. Errores frecuentes

| Síntoma | Causa | Solución |
|---|---|---|
| `Permission denied (publickey)` | Clave SSH no registrada en GitHub | Repetir pasos 1.2–1.4 |
| `'git' no se reconoce` | Git no instalado o terminal sin reiniciar | Instalar y reabrir terminal |
| `fatal: not a git repository` | Estás fuera de la carpeta del repo | `cd` a la carpeta correcta |
| Altium no encuentra símbolos | Falta instalar la librería | Paso 1.7 |
| Cambié la librería y nadie la ve | No recompilaste la `.IntLib` | Sección 4, pasos 5–6 |
| El símbolo cambió pero el esquemático no | Los componentes ya colocados no se actualizan solos | `Tools → Update from Library` |
| Perdí cambios al hacer pull | Altium estaba abierto | Revisar `git log` / `git reflog` |
| `Push rejected` | Alguien subió antes | `git pull --rebase` → `git push` |

---

## ¿Dudas?

Abre un **Issue** en el repositorio o escríbele al dueño del repo.
