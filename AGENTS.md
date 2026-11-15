# AGENTS.md - Reglas para la IA que construya este proyecto

Lee este archivo primero. Después lee, en orden: `docs/01_LEGAL_UE_ESPANA.md`, `docs/02_CONVERSACION.md`, `docs/03_ARQUITECTURA_Y_PLAN.md`.

## Objetivo
Demo pública en Streamlit de un motor conversacional para negocios veterinarios.
El cliente cambia un producto, un precio, un horario o un veterinario en el panel,
y el bot responde con el dato nuevo en el mensaje siguiente.
Interfaz bilingüe (ES / EN). Sin Docker. Base de datos SQLite.

## Reglas de código (obligatorias)
1. Todo el código, comentarios, docstrings y mensajes en español. Las cadenas de usuario viven en `i18n/es.json` y `i18n/en.json`.
2. Sin iconos ni emojis en el código, los comentarios, los textos del bot ni la interfaz, salvo que `docs/` lo pida de forma explícita.
3. Cada módulo lleva docstring de cabecera: qué hace, qué recibe, qué devuelve, qué NO hace.
4. Cada función pública lleva docstring con parámetros, retorno, errores y un ejemplo corto.
5. Comentarios que expliquen el porqué de cada decisión no obvia, sobre todo las legales.
6. Tipado estático (type hints) en todo. Se valida con `mypy --strict` en `core/`.
7. Cada módulo nuevo trae sus pruebas en `tests/`. No se da una fase por terminada si `pytest` falla.
8. Un cambio = un commit pequeño, con mensaje en español. Una rama por fase.
9. Ningún secreto en el código ni en los registros. Las claves viven en `st.secrets` o en variables de entorno.

## Reglas de producto (no negociables)
1. El bot NUNCA inventa precio, horario, stock ni descripción. Todo dato sale de la base de datos de la sesión.
2. El bot NUNCA se hace pasar por persona. Ver `docs/01_LEGAL_UE_ESPANA.md`.
3. Si el bot no sabe, lo dice y ofrece derivar a una persona. No adivina.
4. Ningún dato personal real se guarda. Ver sección de privacidad.

## Estructura de carpetas esperada
```
app.py                  Entrada de Streamlit
core/                   Motor: intención, estado, reglas, redacción, validador
data/                   Esquema SQL y datos ficticios (semilla)
i18n/                   Textos es.json y en.json
ui/                     Chat, panel de negocio, aviso legal
tests/                  Pruebas
evals/                  Conversaciones de referencia y su evaluador
docs/                   Especificación (no se borra)
```
