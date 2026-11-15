# Bot conversacional veterinario (demo en Streamlit)

Demo pública para que un cliente pruebe el motor conversacional.
El cliente edita un producto, precio, horario o veterinario en el panel y el bot responde con el dato nuevo en el mensaje siguiente.

## Estado
Solo hay documentos. El código lo construye otra IA siguiendo `AGENTS.md`.

## Orden de lectura para la IA constructora
1. `AGENTS.md` (reglas obligatorias)
2. `docs/01_LEGAL_UE_ESPANA.md` (aviso de IA, privacidad)
3. `docs/02_CONVERSACION.md` (cómo debe sonar el bot)
4. `docs/03_ARQUITECTURA_Y_PLAN.md` (módulos, esquema, fases)
5. `docs/04_DATOS_FICTICIOS.md` (datos semilla exactos)
6. `docs/05_CONTRATOS_Y_PROMPTS.md` (JSON, firmas, prompts, validador)
7. `docs/06_DESPLIEGUE_STREAMLIT.md` (publicar y dar la URL)
8. `docs/07_TEXTOS_I18N.md` (claves de texto ES y EN)
9. `docs/DECISIONES.md` y `docs/ESTADO.md` (actualizar al terminar cada fase)

## Cómo trabajar
- Una fase por rama, empezando por la fase 0 de `docs/03_ARQUITECTURA_Y_PLAN.md`.
- Al cerrar una fase: `pytest` en verde, `mypy --strict core/` limpio, `docs/ESTADO.md` actualizado.
- Si algo no está definido en los documentos, anotar la duda en `docs/DECISIONES.md` y elegir la opción más simple y segura. No inventar datos de negocio.
