# 04 - Datos ficticios (semilla)

Todos los datos son inventados. Se cargan al iniciar cada sesión y al pulsar "Restablecer demo".
Dinero en céntimos enteros, IVA incluido. Zona horaria Europe/Madrid. Días de la semana: 0 = lunes, 6 = domingo.

## Negocio
| Campo | Valor |
|---|---|
| nombre | Mascota Feliz |
| nombre_bot | Ana |
| telefono | 900 000 000 (ficticio) |
| correo | contacto@mascotafeliz.example |
| trato_por_defecto | tu |
| idioma_por_defecto | es |
| direccion | Plaza Mayor 1, 28012 Madrid (plaza pública, no señala a ningún negocio real) |
| enlace_mapa | vacío: el enlace de Google Maps se crea con la dirección |

## Veterinarios (ninguno se llama Ana)
| id | nombre | especialidad |
|---|---|---|
| 1 | Marta Ruiz | medicina general |
| 2 | Pablo Soler | cirugía |
| 3 | Lucía Vega | dermatología y animales exóticos |

## Turnos de veterinarios
| veterinario | días | horas |
|---|---|---|
| Marta Ruiz | lunes a viernes | 09:00 a 14:00 |
| Pablo Soler | martes, jueves | 15:00 a 20:00 |
| Pablo Soler | sábado | 10:00 a 14:00 |
| Lucía Vega | lunes, miércoles, viernes | 15:00 a 20:00 |

## Horario del negocio
| días | horas |
|---|---|
| lunes a viernes | 09:00 a 20:00 |
| sábado | 10:00 a 14:00 |
| domingo | cerrado |

Día especial: el 25 de diciembre y el 1 de enero, cerrado (nota "Festivo").

## Servicios
| id | nombre_es | nombre_en | duración | precio |
|---|---|---|---|---|
| 1 | Consulta general | General check-up | 30 min | 2.500 (25,00 EUR) |
| 2 | Vacunación | Vaccination | 20 min | 3.500 (35,00 EUR) |
| 3 | Desparasitación | Deworming | 20 min | 2.000 (20,00 EUR) |
| 4 | Limpieza dental | Dental cleaning | 60 min | 9.000 (90,00 EUR) |
| 5 | Revisión dermatológica | Skin check | 40 min | 4.500 (45,00 EUR) |
| 6 | Baño y peluquería | Grooming | 60 min | 3.000 (30,00 EUR) |

Quién atiende: la limpieza dental solo Pablo Soler. La revisión dermatológica solo Lucía Vega. El resto cualquier veterinario con turno. Peluquería: se atiende en el horario del negocio sin veterinario (campo veterinario_id vacío).

## Productos (20)
Cada producto: sku, nombre ES / EN, descripción ES / EN, categoría, marca, precio (céntimos), stock. Las descripciones son cortas y factuales.

| sku | nombre_es | nombre_en | categoría | marca | precio | stock |
|---|---|---|---|---|---|---|
| P001 | Pienso perro adulto 3 kg | Adult dog food 3 kg | alimentación | Campo Verde | 1450 | 25 |
| P002 | Pienso perro adulto 15 kg | Adult dog food 15 kg | alimentación | Campo Verde | 4990 | 12 |
| P003 | Pienso cachorro 3 kg | Puppy food 3 kg | alimentación | Campo Verde | 1590 | 18 |
| P004 | Pienso gato adulto 2 kg | Adult cat food 2 kg | alimentación | Luna Gato | 1190 | 30 |
| P005 | Pienso gato esterilizado 2 kg | Neutered cat food 2 kg | alimentación | Luna Gato | 1290 | 22 |
| P006 | Latas de pavo para gato (pack 6) | Turkey cat cans (6 pack) | alimentación | Luna Gato | 790 | 40 |
| P007 | Snack dental para perros | Dental chew for dogs | snacks | DentiPet | 620 | 50 |
| P008 | Snack de pollo para perros | Chicken treats for dogs | snacks | Campo Verde | 450 | 60 |
| P009 | Antiparasitario externo perro pequeño | Flea and tick spot-on, small dog | salud | Protecan | 1890 | 15 |
| P010 | Antiparasitario externo perro grande | Flea and tick spot-on, large dog | salud | Protecan | 2290 | 0 |
| P011 | Antiparasitario externo gato | Flea and tick spot-on, cat | salud | Protecan | 1690 | 20 |
| P012 | Champú hipoalergénico | Hypoallergenic shampoo | higiene | PelBrillo | 990 | 16 |
| P013 | Cepillo suave | Soft brush | higiene | PelBrillo | 650 | 35 |
| P014 | Pasta dental con cepillo | Toothpaste with brush | higiene | DentiPet | 840 | 28 |
| P015 | Collar ajustable talla M | Adjustable collar, size M | accesorios | Paseo | 790 | 24 |
| P016 | Collar ajustable talla L | Adjustable collar, size L | accesorios | Paseo | 890 | 3 |
| P017 | Correa extensible 5 m | Retractable leash 5 m | accesorios | Paseo | 1590 | 14 |
| P018 | Arnés talla M | Harness, size M | accesorios | Paseo | 1990 | 9 |
| P019 | Rascador pequeño | Small scratching post | juguetes | Luna Gato | 2490 | 7 |
| P020 | Pelota de goma | Rubber ball | juguetes | Paseo | 390 | 80 |

Descripciones (ES; la IA constructora escribe la versión EN equivalente):
- P001, P002: "Alimento completo para perros adultos de raza media. Con pollo y arroz."
- P003: "Alimento completo para cachorros hasta 12 meses. Con pollo."
- P004: "Alimento completo para gatos adultos. Con pescado."
- P005: "Alimento completo para gatos esterilizados. Bajo en grasa."
- P006: "Alimento húmedo de pavo. Seis latas de 85 g."
- P007: "Snack masticable que ayuda a reducir el sarro."
- P008: "Snack blando de pollo, sin colorantes añadidos."
- P009, P010, P011: "Pipeta antiparasitaria externa. Pregunta a un veterinario por la dosis."
- P012: "Champú suave para pieles sensibles. Sin perfume."
- P013: "Cepillo de cerdas suaves para pelo corto."
- P014: "Pasta dental sabor pollo y cepillo de dedo."
- P015, P016: "Collar de nylon ajustable con cierre de seguridad."
- P017: "Correa con freno y cinta de 5 metros."
- P018: "Arnés acolchado de ajuste rápido."
- P019: "Rascador de sisal de 40 cm."
- P020: "Pelota de goma resistente de 6 cm."

Casos de prueba incluidos a propósito: P010 sin stock (el bot debe decirlo y no ofrecerlo). P016 con stock bajo (3). Dos productos con el mismo prefijo ("pienso perro adulto") para forzar la pregunta de aclaración.

## Citas existentes (para que haya huecos ocupados)
Cada vez que se inicia la sesión, crear 6 citas ficticias en los próximos 7 días laborables, repartidas entre los tres veterinarios, con alias "Cliente de ejemplo 1" a "6". Deben ser reproducibles: usar una semilla fija de aleatoriedad.

## Ventas
Tabla vacía al iniciar. Se llena con los pedidos y citas que el bot registre durante la demo.
