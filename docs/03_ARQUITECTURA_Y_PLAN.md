# 03 - Arquitectura y plan por fases

## 1. Decisiones
| Tema | Decisión | Motivo |
|---|---|---|
| Interfaz | Streamlit (`st.chat_message`, `st.chat_input`, pestañas) | Un solo archivo desplegable, enlace público gratis |
| Despliegue | Streamlit Community Cloud, repositorio de GitHub | Sin servidores propios |
| Base de datos | SQLite en memoria por sesión (`st.session_state`) | Sin Docker, aislamiento entre visitantes |
| IA | Proveedor con DPA y región UE, detrás de una interfaz `ProveedorIA` | Cambiar de proveedor sin tocar el motor |
| Respaldo de IA | Segundo proveedor + plantillas sin IA si ambos fallan | La demo nunca se cae |
| Idiomas | `i18n/es.json` y `i18n/en.json` | Texto fuera del código |
| Secretos | `st.secrets` | Nada en el repositorio |

## 2. Módulos de `core/`
| Archivo | Responsabilidad | NO hace |
|---|---|---|
| `esquema.py` | Crea tablas y carga datos ficticios | No contiene lógica de negocio |
| `entender.py` | Llama a la IA y devuelve intención en JSON validado | No redacta respuestas |
| `estado.py` | Memoria de la conversación (producto actual, fecha, trato tú/usted, idioma) | No consulta la IA |
| `reglas.py` | Convierte intención + estado en hechos leyendo la BD | No usa IA |
| `huecos.py` | Calcula citas libres según turnos y citas existentes | No escribe texto |
| `redactar.py` | Pide a la IA el texto a partir de hechos y estilo | No inventa datos |
| `validador.py` | Comprueba que la respuesta solo contiene datos de los hechos | No corrige: descarta |
| `plantillas.py` | Respuestas seguras sin IA, en ES y EN, con varias variantes | |
| `privacidad.py` | Detecta teléfono, correo, DNI/NIE, tarjeta y los quita antes de la IA | |
| `limites.py` | Tope de mensajes por sesión y por día, contador de coste | |
| `proveedor_ia.py` | Interfaz y dos implementaciones, con reintento y cambio al respaldo | |

## 3. Esquema de datos mínimo (SQLite)
- `negocio`(id, nombre, telefono, correo, trato_por_defecto, idioma_por_defecto)
- `productos`(id, sku, nombre_es, nombre_en, descripcion_es, descripcion_en, categoria, marca, precio_centimos, iva_incluido=1, stock, activo)
- `servicios`(id, nombre_es, nombre_en, duracion_min, precio_centimos, activo)
- `veterinarios`(id, nombre, especialidad, activo)
- `turnos`(id, veterinario_id, dia_semana, hora_inicio, hora_fin)
- `horarios_negocio`(id, dia_semana, hora_apertura, hora_cierre)
- `dias_especiales`(id, fecha, cerrado, hora_apertura, hora_cierre, nota)
- `citas`(id, veterinario_id, servicio_id, inicio, fin, alias_cliente)
- `ventas`(id, producto_id, cantidad, total_centimos, creado)
- `registro_eventos`(id, tipo, detalle, creado) para auditoría de cambios del panel

Reglas: dinero en céntimos enteros; nunca flotantes. Fechas en ISO 8601, zona Europe/Madrid.

## 4. Pantalla
- Columna izquierda: chat con cabecera "Asistente con IA", banner de demo, botón "Hablar con una persona", botón "Restablecer demo".
- Columna derecha, pestañas: Catálogo, Horarios, Veterinarios, Ventas.
  - Cada pestaña es una tabla editable (`st.data_editor`). Al guardar se escribe en SQLite.
  - Pestaña Ventas: lista de pedidos y citas que el bot fue registrando durante la demo.
- Selector ES / EN arriba a la derecha.
- Pie: titular, enlace a privacidad, aviso de datos ficticios.
- Móvil: el panel pasa debajo del chat.

## 5. Flujo "cambio en caliente"
1. El cliente edita una celda y pulsa Guardar.
2. Se valida (precio mayor o igual a 0, stock entero, horas coherentes).
3. Se escribe en SQLite y se anota en `registro_eventos`.
4. El mensaje siguiente del bot lee la base. No hay caché de datos de negocio.
5. Se muestra un aviso breve "Cambio aplicado. Prueba a preguntarle al asistente."

## 6. Plan por fases (una rama y una entrega por fase)

| Fase | Resultado | Criterio de aceptación |
|---|---|---|
| 0 | Repositorio, estructura, `requirements.txt`, CI con pytest | `pytest` corre en limpio |
| 1 | Esquema SQLite, semilla ficticia (20 productos, 6 servicios, 3 veterinarios), `huecos.py` | Pruebas de huecos y dinero en verde |
| 2 | Motor sin IA: reglas, plantillas, validador, privacidad, límites | 100 % de las pruebas de datos y de aviso legal |
| 3 | Proveedor de IA, entender y redactar, respaldo | Evals de `02_CONVERSACION.md` sección 7 aprobadas |
| 4 | Interfaz Streamlit completa, panel editable, bilingüe | Pruebas de cambio en caliente aprobadas |
| 5 | Despliegue en Streamlit Cloud, secretos, tope de gasto, documento de buenas prácticas para el cliente | Enlace público funcionando, lista legal completa |
| 6 | Revisión legal por abogado y ajustes | Informe firmado antes de ofrecerlo a clientes reales |

## 7. Pruebas obligatorias
1. Unitarias de cada módulo de `core/`.
2. Pruebas de legalidad: aviso de IA, "eres humano", derivación, privacidad.
3. Pruebas de cambio en caliente.
4. Pruebas de ataque (inyección, datos personales, mensajes enormes).
5. Prueba de carga ligera: 20 sesiones simultáneas sin mezclar datos.
6. Prueba bilingüe: mismo escenario en ES y EN con el mismo resultado de datos.

## 8. Costes y riesgos
| Riesgo | Mitigación |
|---|---|
| Gasto de IA descontrolado | Tope por sesión y por día, modelo pequeño, contador visible para el dueño |
| El bot inventa un dato | Validador y plantilla de respaldo |
| Cambio de la ley | Textos legales en `i18n` y revisión cada 6 meses |
| Streamlit Cloud duerme la app | Aviso de arranque lento; plan de pago si se usa en reuniones críticas |
| Datos personales en la demo | Detector y banner |
| Cliente cree que la demo es producto final | Banner de demo y documento de alcance |

## 9. Fuera de alcance de esta demo
WhatsApp real, voz, pagos, historial clínico, integración con otros sistemas, multiusuario con cuentas.
