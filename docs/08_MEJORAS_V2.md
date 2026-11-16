# 08 - Mejoras v2: que el bot responda y que la demo venda

Origen: prueba real del 2026-11-15 en Streamlit Cloud. Resultado: el bot respondió "no te he entendido" a todo y la pantalla parecía una hoja de cálculo.
Este documento manda sobre los anteriores donde se contradigan. Cada punto trae su criterio de aceptación.

## 1. Diagnóstico (causa real)

| Síntoma | Causa en el código |
|---|---|
| Todo responde "no te he entendido" | En Streamlit Cloud no hay `CLAVE_PRINCIPAL`. `construir_proveedor()` en `app.py` devuelve `None`. Entonces `core/flujo.py` fija `intencion = "no_entendido"` sin mirar el mensaje. |
| El modo sin IA no entiende nada | No existe un entendedor local. El modo sin IA solo tiene plantillas, no comprende. |
| Repite "no te entendí" en bucle | No hay regla que lo impida. |
| "veterinario luis" no da respuesta útil | No se trata el caso "nombre que no existe". |
| "comida para perro" no encuentra nada | No hay sinónimos ("comida" = "pienso" = "alimento") ni búsqueda por categoría y especie. |
| Aspecto aburrido | Interfaz por defecto de Streamlit, tablas con columnas técnicas (id, sku, veterinario_id), letras "A" y "U" como avatares, sin marca. |

## 2. Arreglo inmediato (sin código, lo hace el dueño)
1. En Streamlit Cloud: Manage app, Settings, Secrets.
2. Pegar, con la clave real:
```
PROVEEDOR_PRINCIPAL = "mistral"
CLAVE_PRINCIPAL = "..."
MODELO_PRINCIPAL = "mistral-small-latest"
LIMITE_DIARIO = 1500
LIMITE_SESION = 40
```
3. Guardar. La app se reinicia. El aviso "Modo sin IA" debe desaparecer.
Riesgo: la clave cuesta dinero por mensaje. Nunca subirla a GitHub.

## 3. Entendedor local (`core/entender_local.py`) - obligatorio
Meta: la demo debe funcionar bien aunque la IA falle o no haya clave.

### 3.1 Funcionamiento
1. Normalizar el texto: minúsculas, sin acentos, sin signos, corregir repeticiones ("holaaa").
2. Detectar intención por palabras clave y patrones (tabla 3.2). Puntuar cada intención; gana la de mayor puntuación.
3. Extraer entidades: producto o categoría, especie (perro, gato), tamaño o peso ("15 kg", "grande"), día de la semana, fecha relativa ("mañana", "el jueves"), hora ("10", "10:30", "a las 5 de la tarde"), franja ("mañana", "tarde"), nombre de veterinario, servicio.
4. Buscar contra la base de datos de la sesión, no contra listas fijas. Así un producto nuevo del panel se encuentra al instante.
5. Devolver el mismo JSON que `core/entender.py` (ver 05, sección 2) y una `confianza` de 0 a 1.

### 3.2 Palabras clave mínimas (ES y EN)
| Intención | Disparadores |
|---|---|
| precio_producto | cuanto, cuesta, vale, precio, sale, how much, price, cost |
| disponibilidad | tiene, tienen, teneis, hay, venden, queda, stock, do you have, available |
| descripcion_producto | que lleva, ingredientes, para que sirve, como es, describe, what is, ingredients |
| horario_negocio | hora, abre, abren, cierra, horario, abierto, open, close, hours |
| horario_veterinario | atiende, turno de, cuando esta, trabaja, when is, works |
| pedir_cita | cita, turno, reservar, agendar, pedir hora, appointment, book |
| consultar_servicio | vacuna, consulta, desparasitar, limpieza dental, peluqueria, baño, vaccine, grooming |
| saludo | hola, buenas, buenos dias, buenas tardes, hello, hi |
| despedida / gracias | adios, chao, gracias, bye, thanks |
| hablar_con_persona | persona, humano, agente, operador, human, agent |
| es_ia | eres un robot, eres una ia, eres humana, are you a bot |
| urgencia_clinica | no respira, convulsion, envenen, atropell, sangra, emergency |

Saludo más pregunta en el mismo mensaje ("buenas, tiene comida para perro"): gana la pregunta. El saludo solo se devuelve con una palabra corta de respuesta ("Buenas.") delante.

### 3.3 Sinónimos (tabla `sinonimos` en SQLite, editable)
comida, alimento, pienso, croquetas, food -> categoría alimentación.
golosina, premio, chuche, treat -> snacks.
pipeta, antipulgas, garrapatas -> salud.
perro, perrito, cachorro, dog, puppy -> especie perro. gato, gatito, cat, kitten -> especie gato.
Añadir columna `especie` (perro, gato, ambos) a `productos` para filtrar.

### 3.4 Orden de uso
1. Si hay clave de IA: usar la IA para entender. Si la IA falla o devuelve `no_entendido`, probar el entendedor local.
2. Si no hay clave: usar solo el entendedor local.
3. Si la confianza local es baja (menos de 0,4) y no hay IA: respuesta de ayuda guiada (sección 4.3), nunca "no te entendí" sin más.

### Aceptación
Sin clave de IA, estos mensajes reales dan respuesta útil:
- "buenas tiene comida para perro" -> lista corta de piensos para perro con precio.
- "tiene comida para gato" -> lista de piensos y latas para gato.
- "a que hora abre el lunes" -> "El lunes abrimos de 09:00 a 20:00."
- "buenos dias tiene turno el veterinario luis" -> ver 4.2.

## 4. Conversación natural (cambios sobre 02)

### 4.1 Preguntas amplias: responder con lista corta
Si una búsqueda devuelve de 2 a 4 productos: mostrar todos en líneas cortas con precio y preguntar cuál le interesa.
Más de 4: mostrar los 3 más vendidos o con más stock y decir cuántos hay en total.
Ejemplo:
```
Usuario: buenas tiene comida para perro
Bot: Buenas. Sí, tenemos estos piensos para perro:
- Adulto 3 kg: 14,50 EUR
- Adulto 15 kg: 49,90 EUR
- Cachorro 3 kg: 15,90 EUR
Precios con IVA incluido. Para qué edad es tu perro?
```
La regla de "máximo 3 frases" no aplica a las listas. El validador acepta listas de hasta 5 líneas.

### 4.2 Nombre que no existe
```
Usuario: buenos dias tiene turno el veterinario luis
Bot: Buenos días. No tenemos ningún veterinario llamado Luis. El equipo es Marta Ruiz, Pablo Soler y Lucía Vega. Quieres cita con alguno de ellos?
```
Igual para productos: "No tenemos ese producto. Lo más parecido es ...".

### 4.3 Nunca dos "no te entendí" seguidos
Primera vez: pedir que lo diga de otra forma y dar 3 ejemplos de lo que puede preguntar.
Segunda vez seguida: mostrar botones de ayuda (sección 5.3) y ofrecer hablar con una persona.

### 4.4 Ritmo
- Mostrar "Ana está escribiendo" con `st.status` o un punto animado, máximo 0,8 s.
- Respuesta mostrada con efecto de escritura rápido (`st.write_stream`), no de golpe.

## 5. Diseño comercial de la interfaz

### 5.1 Estructura
- Cabecera con franja de color de marca: nombre "Mascota Feliz", subtítulo "Clínica veterinaria y tienda", insignia "Asistente con IA" en forma de pastilla. Selector ES / EN como dos pastillas, no como lista desplegable.
- Columna izquierda (60 %): el chat en una tarjeta blanca con sombra suave y bordes redondeados, altura fija con su propia barra de desplazamiento (`st.container(height=...)`).
- Columna derecha (40 %): panel "Prueba el motor" (sección 5.4).
- Banner de demo y "Modo sin IA" se mueven a una línea pequeña al pie del chat, no arriba.

### 5.2 Mensajes
- Burbujas: bot a la izquierda, fondo gris claro; cliente a la derecha, fondo color de marca y texto blanco.
- Avatares: el del bot es un círculo con la inicial "A" y el color de marca; el del cliente, un círculo neutro. Sin emojis (regla de AGENTS.md).
- Hora pequeña bajo cada mensaje.
- Productos en respuesta: tarjeta compacta con nombre, precio grande, etiqueta de stock (verde "Disponible", naranja "Pocas unidades", gris "Agotado").

### 5.3 Sugerencias rápidas
Debajo del chat, 4 botones tipo pastilla que envían el texto al pulsarse:
"Ver precios de pienso" / "Horario del sábado" / "Pedir cita" / "Hablar con una persona". En inglés, su traducción.
Se ocultan tras el tercer mensaje del cliente y vuelven si el bot no entiende.

### 5.4 Panel "Prueba el motor" (lo más importante para vender)
Sustituye las tablas técnicas por tres acciones guiadas:
1. Cambiar un precio: selector de producto, campo de precio, botón "Aplicar".
2. Añadir un producto: nombre, categoría, especie, precio, stock, descripción corta. Botón "Añadir".
3. Cambiar un horario: día, apertura, cierre, o marcar cerrado.
Tras aplicar:
- Mensaje verde "Cambio aplicado".
- Botón destacado "Pregúntale ahora a Ana", que envía al chat la pregunta ya preparada (por ejemplo "Cuánto cuesta el Pienso perro adulto 15 kg?").
- La fila cambiada se resalta en el registro de cambios.
Las tablas completas pasan a una pestaña "Datos completos" para quien quiera ver todo. Ocultar columnas id, sku, veterinario_id, precio_centimos, iva_incluido. Mostrar día con nombre ("lunes"), no número.

### 5.5 Marca y estilo
- Fichero `ui/estilo.css` cargado con `st.markdown(..., unsafe_allow_html=True)`. Solo CSS propio, sin HTML que venga del usuario (riesgo de inyección).
- `.streamlit/config.toml`: `primaryColor = "#1F7A6D"` (verde azulado), `backgroundColor = "#F6F8F7"`, `secondaryBackgroundColor = "#FFFFFF"`, `textColor = "#1C2B28"`, `font = "sans serif"`.
- Fuente Inter si está disponible.
- Ocultar menú y pie de Streamlit (`toolbarMode = "minimal"`, CSS para el pie).
- Móvil: panel debajo del chat, sugerencias en una fila desplazable.

### 5.6 Primer contacto del visitante
Una línea encima del chat, solo en la primera visita: "Habla con Ana como lo haría un cliente. Luego cambia un precio a la derecha y vuelve a preguntar." Botón "Entendido" para ocultarla.

## 6. Pruebas nuevas obligatorias
1. `tests/test_entender_local.py`: los 4 mensajes reales de la sección 3 y 30 variantes más (faltas, sin acentos, inglés).
2. Prueba sin clave: `responder(..., proveedor=None)` nunca devuelve `no_se` para los mensajes de la tabla 3.2.
3. Prueba de dos fallos seguidos: el segundo devuelve el tipo `ayuda_guiada`.
4. Prueba de producto nuevo añadido desde el panel y encontrado por sinónimo.
5. Prueba de nombre inexistente de veterinario y de producto.
6. Evals de `evals/` ejecutados en dos modos: con IA falsa y sin IA. Ambos deben aprobar exactitud de datos al 100 %.

## 7. Orden de trabajo (una rama: `fase-7-mejoras-v2`)
1. Entendedor local, sinónimos y columna especie. Pruebas.
2. Flujo: orden de uso de 3.4, ayuda guiada, nombres inexistentes, listas. Pruebas.
3. Interfaz: estilo, burbujas, sugerencias, panel "Prueba el motor". Revisar en móvil.
4. Actualizar `docs/ESTADO.md` y `docs/DECISIONES.md`.
5. Desplegar y repetir la prueba de humo de `06_DESPLIEGUE_STREAMLIT.md` sección 7, más los 4 mensajes reales.
