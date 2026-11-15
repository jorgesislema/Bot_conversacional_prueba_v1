# Decisiones

Registro de decisiones. Añadir una fila por decisión nueva o duda resuelta.

| Fecha | Decisión | Motivo | Estado |
|---|---|---|---|
| 2026-11-15 | Streamlit + SQLite en memoria por sesión, sin Docker | Despliegue gratuito y sin servidores | Cerrada |
| 2026-11-15 | Aviso de IA en el primer mensaje y etiqueta fija | Ley de IA, art. 50 | Cerrada |
| 2026-11-15 | Nombre del bot: Ana. Veterinarios: Marta, Pablo, Lucía | Evitar confusión de nombres | Cerrada |
| 2026-11-15 | Tubería entender, reglas, redactar, validar | Que el dato siempre salga de la base | Cerrada |
| 2026-11-15 | Dependencias fijas: streamlit 1.66.1, pandas 3.1.0, rapidfuzz 3.11.0; SDK de IA en fase 3 | Evitar sorpresas en despliegue; proveedor aún sin elegir | Cerrada |
| 2026-11-15 | CI en GitHub Actions con Python 3.12: pytest + mypy --strict core/ | Criterio de aceptación de la fase 0 | Cerrada |
| 2026-11-15 | Columna negocio.nombre_bot añadida al esquema (la piden 04 y 05) | El esquema de 03 no la listaba pero los textos la necesitan | Cerrada |
| 2026-11-15 | Ampliaciones mínimas: tipo compra_confirmada, tipo anulado y clave compra_confirmada en i18n; huecos_negocio para peluquería | Completan el flujo de compra, la cancelación y la peluquería sin veterinario que piden 04 y 05 | Cerrada |
| 2026-11-15 | Proveedor HTTP compatible con OpenAI (sirve para Mistral u otros cambiando URL y clave); ultimo_uso y temperatura amplían el contrato de 05.9 sin romperlo | Cambiar de proveedor sin tocar el motor; contar tokens sin registrar texto | Cerrada |
| 2026-11-15 | Evals con entender simulado: verifican reglas, plantillas y validador; la eval con IA real espera claves | Sin claves no hay llamadas reales; los datos se verifican igual al 100 % | Cerrada |
| 2026-11-15 | Nuevo módulo core/flujo.py que orquesta entender, reglas, redactar y validar | La tubería de 02.3 vive en un solo lugar probado sin interfaz | Cerrada |
| 2026-11-15 | Claves i18n añadidas: compra_confirmada, error_filas, texto_privacidad | Completan flujos que 07 no detallaba; la paridad ES/EN se mantiene | Cerrada |
| 2026-11-15 | Despliegue: todo listo en el repo (requirements, config, secretos de ejemplo, guía); publicar en share.streamlit.app lo hace el dueño con su cuenta | La URL pública exige la cuenta de GitHub del dueño | Abierta |
| Pendiente | Claves del proveedor de IA principal y de respaldo | Elegir con los criterios de 06.6 y pegarlas en secretos | Abierta |
| Pendiente | Titular legal y correo que aparecen en el pie | Los define el dueño del proyecto | Abierta |
| Pendiente | Revisión de un abogado | Antes de ofrecerlo a clientes reales | Abierta |
