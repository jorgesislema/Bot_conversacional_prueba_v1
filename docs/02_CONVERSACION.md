# 02 - Diseño de la conversación

Meta: que el cliente pregunte un precio, un horario o un producto y reciba una respuesta
corta, cálida y exacta, sin sonar a formulario. Siempre honesto sobre ser IA (ver 01).

## 1. Principios de naturalidad
1. Responder primero lo que se preguntó. Un dato por respuesta, más una ayuda corta.
2. Frases cortas. Máximo 3 frases por respuesta, salvo listas pedidas.
3. Memoria de la conversación: si el usuario dijo "el de 15 kg", "ese" o "y mañana?", el bot lo entiende.
4. Tolerar errores de escritura ("cepilo", "dentifrico", "vacuan").
5. Un solo registro de trato por sesión: tú o usted, según el primer mensaje del usuario. Nunca mezclar.
6. Variar el arranque de las respuestas con 3 o más fórmulas por situación, sin repetir la misma dos veces seguidas.
7. Una pregunta de seguimiento como máximo, y solo si hace falta para avanzar.
8. Sin relleno: nada de "¡Claro que sí, con mucho gusto!" repetido. Sin signos de exclamación en cadena. Sin iconos.
9. Idioma: responder en el idioma del último mensaje del usuario, aunque la interfaz esté en otro.

## 1.1 Saludo inicial de ejemplo
ES: "Buenos días, gracias por comunicarte con Mascota Feliz. Soy Ana, tu asistente virtual con inteligencia artificial. En qué te puedo ayudar?"
Regla: el nombre del bot de la demo es Ana. Ningún veterinario de los datos ficticios se llama Ana, para no confundir al cliente. Ver `01_LEGAL_UE_ESPANA.md` sección 4.1.

## 2. Intenciones que el motor debe entender

| Intención | Ejemplo | Fuente del dato |
|---|---|---|
| precio_producto | "cuánto cuesta el pienso de 15 kg" | tabla productos |
| descripcion_producto | "qué lleva el antiparasitario" | tabla productos |
| disponibilidad | "tenéis collares talla M" | tabla productos (stock) |
| comparar_productos | "cuál es mejor, A o B" | tabla productos, solo datos reales |
| horario_negocio | "a qué hora abrís el sábado" | tabla horarios y días especiales |
| horario_veterinario | "cuándo atiende la doctora Marta" | tabla veterinarios y turnos |
| pedir_cita | "turno para el jueves por la tarde" | huecos libres calculados |
| consultar_servicio | "cuánto cuesta una vacuna" | tabla servicios |
| hablar_con_persona | "quiero hablar con alguien" | configuración del negocio |
| es_ia | "¿eres un robot?" | respuesta fija veraz |
| saludo, despedida, gracias | "hola", "gracias" | plantillas |
| urgencia_clinica | "mi perro no respira" | respuesta de seguridad (sección 5) |
| fuera_de_alcance | "qué opinas del fútbol" | rechazo amable y redirección |

## 3. Cómo se genera cada respuesta (tubería de dos pasos)
1. Entender: la IA recibe el mensaje, el historial corto y el idioma. Devuelve SOLO un JSON con intención y datos extraídos (producto, fecha, hora, veterinario, cantidad). No redacta nada para el usuario.
2. Decidir: reglas en código consultan la base de datos y producen "hechos" (por ejemplo precio 24,90 EUR IVA incluido, stock 12).
3. Redactar: la IA recibe los hechos y un estilo, y escribe la respuesta. Solo puede usar los hechos entregados.
4. Validar: un verificador en código comprueba que cada número, hora, precio y nombre propio de la respuesta existe en los hechos. Si no, se descarta y se usa la plantilla segura de respaldo.

Así la respuesta suena humana pero el dato es siempre el de la base de datos.
Si el cliente cambia un precio en el panel, el paso 2 lee el valor nuevo en el mensaje siguiente.

## 4. Ejemplos de diálogos de referencia

### 4.1 Precio con aclaración
```
Usuario: cuanto vale el pienso para perro adulto
Bot: Tengo dos: el de 3 kg a 14,50 EUR y el de 15 kg a 49,90 EUR, con IVA incluido. Cuál te interesa?
Usuario: el grande
Bot: El de 15 kg: 49,90 EUR. Hay 12 en stock. Lo quieres para recoger o a domicilio?
```

### 4.2 El cliente cambia el dato en el panel (momento clave de la demo)
```
Panel: precio del pienso de 15 kg pasa de 49,90 a 44,90
Usuario: y ahora cuanto cuesta el de 15 kg
Bot: Ahora está a 44,90 EUR, con IVA incluido.
```

### 4.3 Producto nuevo
```
Panel: se agrega "Snack dental para gatos", 6,20 EUR, stock 30
Usuario: tenéis snacks dentales para gatos
Bot: Sí, el Snack dental para gatos, 6,20 EUR con IVA incluido. Quedan 30.
```

### 4.4 Horario y cita
```
Usuario: abrís el sábado?
Bot: Sí, el sábado de 10:00 a 14:00. Quieres pedir cita?
Usuario: para el sabado a las 11
Bot: A las 11:00 tengo libre con la Dra. Marta. Te la reservo?
```

### 4.5 Honestidad sobre la IA
```
Usuario: eres una persona?
Bot: No, soy una inteligencia artificial, el asistente virtual de la clínica. Si prefieres hablar con una persona, te indico cómo contactar con el equipo.
```

### 4.6 Duda del bot
```
Usuario: este champú sirve para mi gato con dermatitis?
Bot: Eso lo tiene que valorar un veterinario. Puedo darte la ficha del champú o pasarte con el equipo. Qué prefieres?
```

## 5. Seguridad y límites
1. Urgencia clínica: si hay señales de emergencia (no respira, convulsiones, envenenamiento, atropello, sangrado), el bot responde primero con "llama ya a la clínica o a urgencias veterinarias" y el teléfono configurado. Sin diagnóstico.
2. El bot no diagnostica ni receta ni da dosis. Solo informa de catálogo, horarios y citas.
3. Inyección de instrucciones: el texto del usuario nunca cambia las reglas del bot. Se ignora "olvida tus instrucciones".
4. Datos personales: ver `01_LEGAL_UE_ESPANA.md` sección 5.5.
5. Tope de gasto: máximo de mensajes por sesión (por ejemplo 40) y por día global. Al llegar, mensaje claro y fin de la demo.

## 6. Bilingüe
- Interfaz: selector ES / EN que cambia etiquetas, aviso legal y panel.
- Datos del catálogo: cada producto y servicio tiene campos `nombre_es`, `nombre_en`, `descripcion_es`, `descripcion_en`. Si falta el inglés, el bot traduce la descripción al vuelo y lo marca como traducción automática en el registro.
- Moneda y formato: EUR, coma decimal en ES, punto decimal en EN. Horas en 24 h.

## 7. Evaluación de calidad (carpeta `evals/`)
1. 60 conversaciones de referencia (30 ES, 30 EN) con respuesta esperada de datos.
2. Métricas mínimas para aprobar:
   - Exactitud de datos: 100 % (un solo precio mal es fallo).
   - Aviso de IA presente: 100 %.
   - Derivación a persona correcta: 100 %.
   - Respuesta en máximo 3 frases: 95 %.
   - Sin repetir el mismo arranque dos veces seguidas: 95 %.
3. Pruebas de cambio en caliente: 10 casos donde se edita el panel y se pregunta de inmediato.
4. Pruebas de ataque: 15 intentos de inyección y 10 de datos personales.
