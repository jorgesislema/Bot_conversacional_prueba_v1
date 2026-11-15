# 06 - Despliegue en Streamlit Community Cloud

Meta: una URL pública que se le entrega al cliente.

## 1. Archivos necesarios en la raíz del repositorio
- `app.py`: punto de entrada.
- `requirements.txt`: dependencias con versión fija. Mínimo: streamlit, pandas, rapidfuzz (búsqueda tolerante), el SDK del proveedor de IA elegido, pytest y mypy solo en `requirements-dev.txt`.
- `.streamlit/config.toml`: tema claro, `toolbarMode = "minimal"`, `gatherUsageStats = false`.
- `.streamlit/secrets.toml.example`: plantilla sin valores reales.
- `.gitignore`: incluye `.streamlit/secrets.toml`, `__pycache__`, `.env`, `*.db`.

## 2. Secretos (se cargan en el panel de Streamlit, nunca en Git)
Claves esperadas, en formato TOML:
- `PROVEEDOR_PRINCIPAL`: nombre del proveedor.
- `CLAVE_PRINCIPAL`: clave de API.
- `PROVEEDOR_RESPALDO` y `CLAVE_RESPALDO`: opcionales.
- `LIMITE_DIARIO`: entero, por ejemplo 1500.
- `LIMITE_SESION`: entero, por ejemplo 40.
- `CLAVE_ADMIN`: opcional, para ver el contador de coste.
Si falta la clave principal, la app arranca en modo sin IA (solo plantillas) y lo indica en el panel.

## 3. Pasos para publicar
1. Subir el repositorio a GitHub (privado o público; sin secretos).
2. Entrar en share.streamlit.io con la cuenta de GitHub.
3. Crear app nueva: repositorio, rama principal, archivo `app.py`.
4. En "Advanced settings": elegir la versión de Python y pegar los secretos.
5. Desplegar. La URL tendrá la forma `https://nombre.streamlit.app`. Se puede elegir el nombre.
6. Probar la URL desde el móvil y desde una ventana privada.
7. Pasar la lista de verificación legal (`docs/01_LEGAL_UE_ESPANA.md` sección 6) con la URL pública.

## 4. Comportamiento a tener en cuenta
- La app se duerme tras un tiempo sin visitas y tarda en despertar. Avisar al cliente o abrirla 5 minutos antes de una reunión.
- No hay disco permanente. Por eso la base va en memoria por sesión. Un reinicio borra todo y es lo esperado.
- Cada pestaña del navegador es una sesión. Los datos de una sesión no los ve otra.
- Los cambios en Git se redespliegan solos al hacer push a la rama principal.
- Si el cliente quiere que su URL no sea pública, la app se puede restringir a correos autorizados desde los ajustes de compartir.

## 5. Qué decir al cliente (texto para enviar)
"Esta es una demo con datos inventados. Cambia un precio, un horario o agrega un producto en el panel de la derecha y pregúntale al asistente. Verás que responde con el dato nuevo al instante. No escribas datos personales reales."

## 6. Elección del proveedor de IA (decisión pendiente, anotar en DECISIONES.md)
Criterios obligatorios: acuerdo de tratamiento de datos (DPA), sin entrenamiento con los datos del cliente, procesamiento en la UE si es posible, salida JSON fiable, buen español e inglés, coste bajo por mensaje.
Candidatos a evaluar en la fase 3: un proveedor europeo (por ejemplo Mistral) y un proveedor grande con región UE (por ejemplo los de nube con región europea). Medir con los evals de `02_CONVERSACION.md` sección 7 y elegir el más barato que apruebe. Precios y condiciones no verificados: comprobarlos en la web oficial el día de la decisión.

## 7. Prueba de humo tras publicar
1. Abre la URL: aparece el aviso de IA en el primer mensaje.
2. Pregunta un precio: responde bien.
3. Cambia ese precio en el panel y vuelve a preguntar: responde el nuevo.
4. Cambia a EN: interfaz y respuestas en inglés.
5. Escribe un teléfono: el bot pide no compartirlo.
6. "Quiero hablar con una persona": deriva.
7. Pulsa "Restablecer demo": vuelve a los datos originales.
