# 07 - Claves de texto (i18n)

Los archivos `i18n/es.json` y `i18n/en.json` deben tener exactamente las mismas claves. Una prueba lo verifica.
Sin emojis ni iconos. Los textos usan marcadores como {negocio}, {nombre_bot}, {saludo}.

## Claves y texto base en español (la versión EN es la traducción equivalente)

### Legal y aviso
| clave | texto ES |
|---|---|
| aviso_ia_inicio | {saludo}, gracias por comunicarte con {negocio}. Soy {nombre_bot}, tu asistente virtual con inteligencia artificial. En qué te puedo ayudar? |
| aviso_ia_inicio_usted | {saludo}, gracias por comunicarse con {negocio}. Soy {nombre_bot}, su asistente virtual con inteligencia artificial. En qué le puedo ayudar? |
| etiqueta_ia | Asistente con IA |
| es_ia | No, soy una inteligencia artificial, el asistente virtual de {negocio}. Si prefieres hablar con una persona, te indico cómo contactar con el equipo. |
| derivar_persona | Claro. Puedes contactar con el equipo en el {telefono} o en {correo}. |
| derivar_demo | En un negocio real, aquí se te pasaría con una persona del equipo. |
| banner_demo | Demo con datos ficticios. No escribas datos personales reales. |
| datos_personales | Prefiero que no compartas datos personales por aquí. Puedo ayudarte sin ellos. |
| tope | Se alcanzó el límite de mensajes de esta demo. El panel sigue disponible. |
| pie_titular | Titular: {titular}. Contacto: {correo_titular}. |
| pie_privacidad | Privacidad |

### Saludos según la hora (Europe/Madrid)
saludo_manana: "Buenos días" (hasta las 12:59). saludo_tarde: "Buenas tardes" (13:00 a 20:59). saludo_noche: "Buenas noches" (desde las 21:00).
EN: "Good morning", "Good afternoon", "Good evening".

### Respuestas base (plantillas de respaldo, 3 variantes cada una; aquí la primera)
| clave | texto ES |
|---|---|
| precio | {producto}: {precio}, IVA incluido. |
| stock_hay | Hay {stock} disponibles. |
| stock_pocas | Quedan pocas unidades: {stock}. |
| stock_cero | Ahora mismo no hay stock de {producto}. |
| alternativa | Puedo ofrecerte {alternativa} a {precio}. |
| aclaracion | Tengo varias opciones: {lista}. Cuál te interesa? |
| horario | {dia}: de {apertura} a {cierre}. |
| cerrado | Ese día estamos cerrados. El siguiente día abierto es {dia}. |
| oferta_cita | Tengo libre el {dia} a las {hora} con {veterinario}. Te la reservo? |
| cita_confirmada | Hecho. Cita para {servicio} el {dia} a las {hora} con {veterinario}. |
| sin_hueco | No tengo hueco en esa franja. Lo más cercano es el {dia} a las {hora}. Te va bien? |
| urgencia | Esto puede ser una urgencia. Llama ya a la clínica al {telefono} o a un servicio de urgencias veterinarias. |
| medico | Eso lo tiene que valorar un veterinario. Puedo darte la ficha del producto o pasarte con el equipo. |
| rechazo_alcance | De eso no te puedo ayudar. Puedo informarte de productos, precios, horarios y citas. |
| no_entendido | No te he entendido bien. Puedes decirlo de otra forma? |
| despedida | Gracias por escribirnos. Que vaya muy bien. |
| gracias | De nada. Algo más en lo que te pueda ayudar? |

### Interfaz
| clave | texto ES |
|---|---|
| idioma | Idioma |
| boton_persona | Hablar con una persona |
| boton_reset | Restablecer demo |
| pestana_catalogo | Catálogo |
| pestana_horarios | Horarios |
| pestana_veterinarios | Veterinarios |
| pestana_ventas | Ventas |
| guardar | Guardar cambios |
| cambio_aplicado | Cambio aplicado. Prueba a preguntarle al asistente. |
| error_precio | El precio debe ser un número mayor o igual a cero. |
| error_stock | El stock debe ser un número entero mayor o igual a cero. |
| error_horas | La hora de cierre debe ser posterior a la de apertura. |
| placeholder_chat | Escribe tu mensaje |
| mensajes_restantes | Mensajes restantes: {n} |
| modo_sin_ia | Modo sin IA: respuestas básicas. |

### Frases prohibidas (el validador las busca)
ES: "como persona", "soy humano", "soy una persona", "yo también tengo", "en mi experiencia personal".
EN: "as a human", "i am human", "i am a person", "in my personal experience".

## Formato
- ES: coma decimal ("49,90 EUR"), fecha "jueves 20 de noviembre", hora "17:30".
- EN: punto decimal ("49.90 EUR"), fecha "Thursday 20 November", hora "17:30".
