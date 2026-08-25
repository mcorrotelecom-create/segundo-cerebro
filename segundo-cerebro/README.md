# Segundo Cerebro de Ingeniería — Fase 0

Ingesta, clasificación automática y búsqueda con citas sobre los documentos
de un proyecto de ingeniería. Esta es la Fase 0 del roadmap de la propuesta
técnica: la base sobre la que se construye la Fase 1 (cuentas de avance).

## Qué hace esta versión

1. Subes un documento (PDF, Excel o Word) desde la interfaz web.
2. El sistema lo clasifica solo, por su nombre de archivo: tipo de documento
   (reconoce tus formatos F14/F27/F42/F46/F59...), disciplina, nivel/zona y
   fecha cuando el nombre los trae.
3. Extrae el texto y las tablas, lo divide en fragmentos y calcula un
   embedding local de cada uno (sin costo, sin salir a internet).
4. Queda buscable: la pestaña "Buscar" combina búsqueda semántica y de texto
   completo, y cada resultado muestra exactamente de qué documento y de qué
   parte (página / hoja+filas / párrafo) salió.

Lo que **no** hace todavía (llega en fases siguientes, ver la propuesta
técnica): cálculo de cuentas de avance, chat del proyecto, agentes, OCR de
PDFs escaneados, lectura de planos DWG. La Fase 0 es la base de ingesta —
nada más, a propósito.

## Cómo desplegarlo — 3 pasos, todo en la nube

Nada de esto corre en tu computadora. No instalas Docker, ni Python, ni
Node, ni Postgres en tu PC — todo se construye y corre en los servidores de
las empresas de cada paso. Tu computadora solo la vas a usar, al final, para
abrir la URL en el navegador.

Todo es gratis en el nivel que vamos a usar (con la única salvedad honesta
que te explico en "Qué esperar del plan gratis" más abajo).

### Paso 1 — Sube el código a GitHub

1. Entra a https://github.com y crea una cuenta si no tienes una (gratis).
2. Crea un repositorio nuevo (botón verde "New"), **privado**, con
   cualquier nombre (ej. `segundo-cerebro`).
3. En la página del repo recién creado, usa el enlace "uploading an
   existing file" y arrastra ahí toda la carpeta `segundo-cerebro` que te
   entregué (descomprimida). Confirma el "commit" (botón verde al final).

### Paso 2 — Crea la base de datos en Neon

1. Entra a https://neon.tech y crea una cuenta gratis (con GitHub o con tu
   correo — no pide tarjeta).
2. "Create a project" — cualquier nombre, región la más cercana a ti.
3. Neon te muestra una "Connection string" (empieza con `postgresql://...`),
   con un interruptor/casilla que dice **"Connection pooling"** — actívala
   o desactívala según se necesite: **desactívala** (déjala apagada) antes
   de copiar. Con el interruptor apagado, la dirección del servidor en la
   cadena NO trae "-pooler" en el nombre; con él prendido, sí — asegúrate
   de que la tuya NO lo tenga. (El motivo: nuestra aplicación mantiene sus
   propias conexiones abiertas todo el tiempo, y el modo "pooling" de Neon
   está pensado para lo contrario — muchas conexiones cortas tipo
   serverless. Mezclar los dos puede causar errores intermitentes y
   confusos más adelante.) Copia esa cadena tal cual y guárdala en un bloc
   de notas: la necesitas en el paso 3, sin editarla — la aplicación ajusta
   sola el prefijo que necesita.

### Paso 3 — Crea el servicio en Render

1. Entra a https://render.com y crea una cuenta gratis (puedes usar tu
   cuenta de GitHub para entrar directo).
2. "New +" → "Web Service".
3. Conecta tu cuenta de GitHub y elige el repositorio que creaste en el
   paso 1.
4. Render va a detectar el `Dockerfile` en la raíz del proyecto — déjalo en
   **Environment: Docker**. Deja "Root Directory" vacío, **salvo que** al
   subir el proyecto a GitHub (paso 1) haya quedado dentro de una carpeta
   `segundo-cerebro` en vez de suelto en la raíz del repositorio — en ese
   caso, escribe `segundo-cerebro` en "Root Directory" (revisa la página
   principal de tu repositorio en GitHub para saber cuál es tu caso: si ves
   `Dockerfile` directo en la lista, déjalo vacío; si primero hay que
   entrar a una carpeta `segundo-cerebro` para verlo, pon ese nombre).
5. Elige el plan **Free**.
6. Antes de crear el servicio, abre la sección "Environment Variables" y
   agrega:
   - `DATABASE_URL` → pega ahí la cadena de conexión de Neon tal cual te la
     dieron (paso 2), sin editarla.
   - `BASIC_AUTH_USER` → cualquier usuario que inventes (ej. `marlon`).
   - `BASIC_AUTH_PASSWORD` → cualquier contraseña que inventes.
   - `ANTHROPIC_API_KEY` → opcional en esta fase (no la usa todavía); si ya
     tienes una de console.anthropic.com, puedes agregarla de una vez para
     no tener que volver en la Fase 1.
7. "Create Web Service". La primera construcción tarda unos 5-10 minutos
   (compila el frontend y arma la imagen). Cuando termine, Render te da una
   URL propia (`https://algo.onrender.com`) — esa es tu aplicación.

Abre esa URL, el navegador te va a pedir el usuario y contraseña que
pusiste en `BASIC_AUTH_USER`/`BASIC_AUTH_PASSWORD`, y ya estás adentro.

## Qué esperar del plan gratis

Tres cosas reales que conviene saber, sin sorpresas:

- **El servicio "se duerme"** después de 15 minutos sin uso (límite del
  plan gratis de Render). La próxima vez que abras la URL después de estar
  dormido, tarda ~1 minuto en despertar antes de responder — es normal, no
  está roto. La base de datos de Neon hace lo mismo por su lado (se
  "duerme" a los 5 minutos sin uso, en su propio plan gratis) — normalmente
  despierta bastante más rápido que Render, así que no se nota por
  separado, pero si abres la URL después de mucho tiempo sin usarla, esa
  primera carga puede sentirse un poco más lenta de lo normal. Ninguna de
  las dos cosas pierde datos — solo tardan un poco en "prender" de nuevo.
- **El usuario/contraseña es una traba mínima, no seguridad real** — evita
  que cualquiera que encuentre la URL por casualidad entre a ver tus
  documentos, pero no reemplaza un sistema de login de verdad. Suficiente
  para un proyecto personal con una URL que no vas a publicar en ningún
  lado; no lo trates como si guardara información ultra sensible.
- **La búsqueda usa el modo liviano por defecto, no el modelo de IA
  completo.** El plan gratis de Render solo da 512MB de RAM, y el modelo de
  embeddings semántico (el que entiende sinónimos y significado, no solo
  palabras exactas) pesa más que eso él solo — instalarlo ahí hace que el
  servicio se quede sin memoria y se caiga (el error que viste). Por eso el
  despliegue en la nube usa por defecto una búsqueda por palabras/texto
  completo (encuentra términos, códigos de formato, nombres exactos —
  sigue siendo útil), sin la capa semántica de IA. Si más adelante quieres
  la búsqueda semántica completa, hay dos caminos, ninguno urgente ahora:
  correrlo en tu PC (sección de abajo, donde sí sobra RAM), o subir a un
  plan de Render con más memoria. Lo cubro en detalle en la sección
  "Búsqueda semántica completa (opcional)" más abajo.

Si en algún momento el "se duerme" te molesta, Render tiene un plan pagado
(~$7/mes) que lo mantiene siempre despierto — decisión tuya, no hace falta
tomarla ahora.

## Búsqueda semántica completa (opcional)

No hace falta para empezar a usar la Fase 0 — la búsqueda por palabras ya
funciona bien para encontrar documentos por término, código de formato o
nombre. Actívala más adelante si quieres que la búsqueda entienda
significado y no solo palabras exactas, y tienes dónde correrla con RAM de
sobra (tu PC, o un plan de Render con más memoria que el gratuito):

```
pip install -r requirements.txt -r requirements-semantic.txt
```

(en Render, cambiarías esto agregando esa segunda instalación al
Dockerfile — avísame cuando llegues a ese punto y lo ajustamos juntos). La
primera vez que subas un documento después de instalarlo, el backend
descarga el modelo (~470MB, una sola vez) — tarda un par de minutos, es
normal.

## Actualizar la aplicación más adelante

Cuando te entregue cambios nuevos (Fase 1 en adelante): subes los archivos
actualizados a tu repositorio de GitHub (mismo paso de "uploading an
existing file" de arriba, sobrescribiendo lo que cambió) y Render
reconstruye y despliega solo — no hay que repetir los pasos 2 y 3.

## Alternativa: correrlo en tu PC sin Docker (opcional)

Si alguna vez quieres probar cambios en tu propia máquina antes de subirlos
(no es necesario para uso normal), el proyecto trae instaladores directos
de Python/Node/Postgres — sin Docker de por medio:

### 1. Python

Descarga e instala Python 3.11 o más nuevo desde
https://www.python.org/downloads/ — **importante:** en la primera pantalla
del instalador, marca la casilla **"Add python.exe to PATH"** antes de darle
a instalar.

### 2. Node.js

Descarga e instala la versión **LTS** desde https://nodejs.org/ — instalador
normal, siguiente-siguiente-instalar.

### 3. PostgreSQL

Descarga e instala desde https://www.postgresql.org/download/windows/
(el instalador de EDB). Durante la instalación:

- Te pide una contraseña para el usuario `postgres` — anótala, la vas a
  necesitar en el paso siguiente.
- Puerto: deja el que viene por defecto (`5432`).
- Al final, deja marcada la opción de abrir **Stack Builder** — no, ciérrala,
  no la necesitas.

Cuando termine, abre el programa **"SQL Shell (psql)"** que quedó instalado
(búscalo en el menú de inicio). Te va a preguntar Server, Database, Port,
Username uno por uno — presiona Enter en cada uno para aceptar el valor por
defecto (que aparece entre corchetes). Cuando pida la contraseña, escribe la
que pusiste al instalar. Ya adentro, escribe esta línea y presiona Enter:

```sql
CREATE DATABASE segundo_cerebro;
```

### 4. Instala el proyecto

Abre PowerShell dentro de la carpeta `segundo-cerebro\backend` (clic en la
barra de direcciones del explorador, escribe `powershell`, Enter) y corre:

```
.\install.bat
```

Cuando termine, copia `.env.example` a `.env` (copiar, pegar, renombrar
quitando ".example") y abre ese `.env` con el Bloc de notas — pon tu cadena
de conexión local o de Neon en `DATABASE_URL`. Guarda y cierra.

Ahora en la carpeta `segundo-cerebro\frontend`, abre otra PowerShell y corre:

```
.\install.bat
```

### 5. Úsalo

Necesitas **dos ventanas de PowerShell abiertas al mismo tiempo**:

- En `segundo-cerebro\backend`: `.\start.bat`
- En `segundo-cerebro\frontend`: `.\start.bat`

Por defecto `install.bat` instala solo el modo liviano de búsqueda (ver
"Búsqueda semántica completa (opcional)" más arriba si quieres el modelo
de IA completo — en tu PC sí sobra RAM de sobra para correrlo). Cuando
ambas ventanas estén corriendo sin errores, abre `http://localhost:3000`
en tu navegador. Para apagar: `Ctrl+C` en cada una.

## Cómo se probó

Este proyecto se desarrolló en un entorno donde no había acceso a PyPI/npm
para instalar dependencias, así que la verificación se hizo en dos niveles:

- **Lógica de negocio real, probada de verdad:** clasificación por nombre de
  archivo, extracción de texto (PDF/Excel/Word), troceo en fragmentos,
  embeddings y búsqueda por similitud corrieron end-to-end contra **6
  documentos reales** de tu carpeta de Hospital del Niño (una factura, una
  plantilla de mediciones, una nota formal, un acta de entrega, un informe
  de cuenta y el plan de proyecto F14). `backend/tests/` tiene 12 pruebas
  automatizadas (`python -m unittest discover -s tests`, sin dependencias
  externas) más `tests/sandbox_integration_check.py`, que corre el pipeline
  completo e imprime clasificación, fragmentos y resultados de búsqueda para
  cada documento.
- **La app completa (FastAPI + Postgres + Next.js, ya empaquetada en un
  Docker construido por Render) no se pudo ejecutar integrada en ese entorno
  de desarrollo** — se construyó siguiendo el mismo patrón que ya se probó
  por separado (SQLAlchemy sobre los modelos de `app/models.py`, los mismos
  módulos de clasificación/extracción/embeddings ya verificados, FastAPI
  como capa delgada encima, sirviendo también el export estático de
  Next.js). El primer despliegue en Render es, en ese sentido, la primera
  vez que corre integrada — si algo falla, copia el mensaje de error del
  panel de "Logs" de Render y lo corregimos.

Dos cosas reales que esa prueba encontró y ya están corregidas en el código:
un bug de openpyxl con hojas de Excel que tienen celdas vacías al inicio de
fila (rompía la lectura de `F14 Plan de proyecto...xlsx`), y una reparación
automática con `pikepdf` para PDFs con estructura de páginas mal formada
(afectaba al acta de entrega de planos y a una nota firmada — ambos son PDFs
escaneados de documentos físicos).

## Limitación real encontrada: PDFs escaneados

De los 6 documentos de prueba, 2 (el acta de entrega de planos F27 y una
nota firmada) son PDFs sin capa de texto — fotos o escaneos guardados como
PDF. El sistema los clasifica correctamente por su nombre de archivo, pero
no puede indexar su contenido todavía: no hay texto que extraer sin OCR.
El sistema lo señala explícitamente (`sin_texto_extraible_posible_escaneo`)
en vez de fingir que los leyó. Dado que varios formatos de tu proyecto
(notas, actas) parecen escanearse con frecuencia, vale la pena adelantar el
OCR de la Fase 2 antes de lo planeado — decisión para cuando revisemos cómo
salió esta fase.

## Estructura del proyecto

```
Dockerfile                   arma la interfaz + la API en una sola imagen
                              (esto es lo que Render construye — nunca
                              corre en tu PC)
backend/
  install.bat / start.bat    alternativa opcional: instalar y arrancar
                              en tu PC sin Docker
  app/
    classification.py   clasificación por nombre de archivo (reglas)
    extraction/          extractores de PDF / Excel / Word
    chunking.py           divide texto extraído en fragmentos citables
    embeddings.py         embeddings locales (con respaldo sin modelo)
    vectorstore.py       búsqueda por similitud de coseno
    ingestion.py           orquesta todo el pipeline
    search.py              búsqueda híbrida (semántica + texto completo)
    security.py             usuario/contraseña de acceso a la aplicación
    models.py               esquema de base de datos (SQLAlchemy)
    routers/                endpoints de la API (FastAPI)
  tests/                    pruebas automatizadas + prueba de integración
frontend/
  install.bat / start.bat   alternativa opcional: instalar y arrancar
                             en tu PC sin Docker
  app/                      interfaz (Next.js) — subir documentos, buscar
```

## Siguiente paso

Cuando confirmes que esto corre bien desplegado y la clasificación se ve
razonable sobre tus propios documentos, seguimos con la Fase 1: extracción
asistida por IA de las plantillas de mediciones y el cálculo automático de
cuentas de avance.
