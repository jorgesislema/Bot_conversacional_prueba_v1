# 01 - Marco legal UE y España

Estado: investigado el 2026-11-15. No es asesoría jurídica.
Antes de vender a un cliente real, un abogado debe revisar los textos finales.

## 1. Respuesta corta
Sí. En la UE (y por tanto en España) el bot debe decir que es una IA.
Se puede cumplir sin que la conversación suene robótica: se avisa una vez, de forma clara,
y después el bot habla natural. Lo que está prohibido es fingir ser una persona.

## 2. Normas que aplican

| Norma | Qué exige al bot | Cómo se cumple aquí |
|---|---|---|
| Reglamento (UE) 2024/1689, Ley de IA, art. 50.1 | Informar a la persona de que interactúa con una IA, salvo que sea evidente por el contexto. Aplica desde el 2 de agosto de 2026, sin importar el nivel de riesgo. | Mensaje inicial fijo + etiqueta permanente en pantalla |
| Ley de IA, art. 50.2 y 50.4 | Marcar el contenido sintético (audio, imagen, vídeo) y etiquetar deepfakes. | La demo solo genera texto. Si se añade voz, se marca como sintética. |
| Ley de IA, art. 4 | Formación mínima en IA del personal que opera el sistema. | Documento breve de buenas prácticas para el cliente (fase 5) |
| Ley de IA, art. 5 | Prohibe técnicas de manipulación subliminal o engañosa. | Sin presión de venta falsa, sin urgencia inventada |
| RGPD (UE) 2016/679 y LOPDGDD 3/2018 | Base legal, información al usuario, minimización, conservación limitada, encargado de tratamiento con el proveedor de IA. | La demo no pide datos personales. Aviso de privacidad. Proveedor de IA con acuerdo de tratamiento y región UE. |
| RGPD art. 22 | Derecho a no ser objeto de decisiones solo automatizadas con efectos jurídicos. | El bot informa y toma pedidos o citas simples. No decide cobros, diagnósticos ni sanciones. |
| LSSI-CE 34/2002 | Datos de identificación del prestador y aviso de cookies si hay cookies no esenciales. | Pie de página con titular. Sin cookies de seguimiento. |
| Ley 10/2025 de Servicios de Atención a la Clientela (BOE 27-12-2025, en vigor 28-12-2025) | Para grandes empresas y servicios básicos: atención gratuita, accesible y derecho a que te atienda una persona si la pides. | Botón y frase "hablar con una persona" siempre disponible. Se explica al cliente que, si su negocio entra en el ámbito de la ley, debe tener persona detrás. |
| Texto Refundido de la Ley de Consumidores (RDL 1/2007) | Información veraz de precio (IVA incluido) y sin publicidad engañosa. | Precios siempre con impuestos incluidos, tomados de la base de datos. |
| Anteproyecto español de gobernanza de la IA y AESIA | Autoridad de supervisión en España (AESIA) y sanciones por no etiquetar. | Se sigue el art. 50 al pie de la letra. Revisar el texto final cuando se publique. |

Sanciones de referencia de la Ley de IA por incumplir transparencia: hasta 15 millones de euros o el 3 % de la facturación mundial, la cifra mayor.

## 3. Aclaraciones que reducen riesgo
- El aplazamiento del paquete "Digital Omnibus" afecta sobre todo a los sistemas de alto riesgo.
  La transparencia del art. 50.1 (avisar de que es IA) SÍ aplica desde agosto de 2026.
  Solo el marcado legible por máquina de contenido generado tiene prórroga hasta el 2 de diciembre de 2026.
- "Evidente por el contexto" es una excepción débil. No se usa. Se avisa siempre.
- Proveedor: quien construye el motor (nosotros). Responsable del despliegue: el negocio cliente. Ambos tienen deberes. El contrato debe repartirlos.

## 4. Reglas de diseño que salen de la ley (obligatorias)

### 4.1 Aviso de IA
1. Primer mensaje del chat, siempre, en el idioma activo. No existe un formato oficial: la ley pide un aviso claro, al inicio y antes de ayudar. Texto base en `i18n`, con saludo según la hora de Europe/Madrid (buenos días, buenas tardes, buenas noches):
   - ES: "{saludo}, gracias por comunicarte con {negocio}. Soy {nombre_bot}, tu asistente virtual con inteligencia artificial. En qué te puedo ayudar?"
   - EN: "{saludo}, thank you for contacting {negocio}. I am {nombre_bot}, your virtual assistant, an artificial intelligence. How can I help you?"
   - Ejemplo de la demo: negocio "Mascota Feliz", nombre_bot "Ana".
   - Debe aparecer la expresión "inteligencia artificial" o "IA" (en inglés "artificial intelligence" o "AI"). "Asistente virtual" por sí solo no basta.
   - Después del aviso el bot pasa directo a ayudar. No se repite el aviso en cada mensaje.
2. Etiqueta fija visible en la cabecera del chat: "Asistente con IA" / "AI assistant". No se puede ocultar desde el panel.
3. Si el usuario pregunta "¿eres una persona?" o similar, el bot responde con la verdad, sin rodeos, en esta misma respuesta.
4. El nombre del bot no puede ser un nombre humano con foto humana que induzca a error. Se permite un nombre de marca ("Asistente de Clínica Luna").

### 4.2 Derivar a una persona
1. Frases que activan la derivación: "hablar con una persona", "agente", "humano", "operador", "talk to a human".
2. El bot confirma y muestra el canal de contacto del negocio (teléfono o correo configurable).
3. En la demo no hay persona real. Se muestra un mensaje de ejemplo: "En un negocio real, aquí se le pasaría a una persona del equipo."

### 4.3 Qué NO se hace (y por qué)
- No se simulan pausas de "está escribiendo" largas para parecer humano. Una pausa corta (menos de 1 s) por tiempo real de respuesta es aceptable.
- No se usan frases como "como persona, yo...". No se inventan experiencias propias.
- No se oculta el aviso de IA por "mejor experiencia".
- No se pide ni se guarda dato personal real en la demo.

### 4.4 Cómo se mantiene la fluidez a pesar del aviso
El aviso ocurre una vez y es breve. La naturalidad viene de otra parte: ver `docs/02_CONVERSACION.md`.
Un bot honesto y útil se siente natural. Un bot que oculta que es IA pierde la confianza al descubrirse.

## 5. Privacidad de la demo
1. Banner permanente bajo el chat: "Demo con datos ficticios. No escribas datos personales reales." (y en inglés).
2. Cada visitante tiene su propia base SQLite en memoria o en archivo temporal. Se destruye al cerrar la sesión.
3. Registros de conversación: solo en memoria durante la sesión. Sin envío a terceros salvo el proveedor de IA.
4. Proveedor de IA: elegir uno con acuerdo de tratamiento de datos (DPA), sin entrenamiento con datos del cliente y con región UE. Guardar la elección en `docs/DECISIONES.md`.
5. Detector de datos personales: si el usuario escribe un teléfono, correo, DNI/NIE o tarjeta, el bot NO lo procesa, avisa y pide no compartirlo. Esa parte del mensaje no se envía al proveedor de IA.
6. Texto de privacidad corto enlazado en el pie: responsable, finalidad, proveedor, plazo (sesión), derechos y contacto.

## 6. Lista de verificación legal (se ejecuta antes de cada entrega)
- [ ] El primer mensaje contiene el aviso de IA en ES y EN.
- [ ] La etiqueta "Asistente con IA" no se puede quitar.
- [ ] "¿Eres humano?" recibe respuesta veraz (prueba automática).
- [ ] "Quiero hablar con una persona" deriva (prueba automática).
- [ ] Un teléfono o correo escrito no llega al proveedor de IA (prueba automática).
- [ ] Todos los precios muestran impuestos incluidos.
- [ ] No hay cookies de seguimiento.
- [ ] Existe aviso de privacidad y datos del titular en el pie.
- [ ] Un abogado revisó los textos si va a haber cliente real.

## 7. Fuentes
- [Guía práctica del art. 50 de la Ley de IA](https://artificialintelligenceact.eu/es/transparency-rules-article-50/)
- [Comisión Europea, normas de transparencia de la IA](https://digital-strategy.ec.europa.eu/es/factpages/quick-facts-transparency-rules-ai-systems)
- [Comisión Europea, directrices de transparencia](https://digital-strategy.ec.europa.eu/es/library/guidelines-transparency-obligations-providers-and-deployers-ai-systems)
- [Qué se aplica el 2 de agosto de 2026 (aiacto.eu)](https://www.aiacto.eu/es/blog/articulo-50-ai-act-que-se-aplica-2-agosto-2026)
- [Ley 10/2025 de atención a la clientela, La Moncloa](https://www.lamoncloa.gob.es/serviciosdeprensa/notasprensa/derechos-sociales-consumo-agenda-2030/paginas/2025/ley-servicios-atencion-al-cliente.aspx)
- [Ley 10/2025 en Norm@doc (BOE 27-12-2025)](https://www.hacienda.gob.es/DocLeyes/REPOSITORIO%20NORMATIVA/94289.htm)

Pendiente de verificar con abogado: alcance exacto de la Ley 10/2025 para pymes veterinarias, y texto final de la ley española de gobernanza de IA.
