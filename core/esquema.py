"""Crea las tablas SQLite y carga los datos ficticios de la demo.

Qué hace: abre la conexión en memoria, ejecuta data/esquema.sql e
inserta la semilla de docs/04_DATOS_FICTICIOS.md. Recibe: una conexión
o nada (la crea). Devuelve: la conexión lista para usar. Qué NO hace:
no contiene lógica de negocio ni calcula huecos (eso es huecos.py).

Por qué memoria por sesión: cada visitante tiene su propia base y se
destruye al cerrar, así no se guardan datos personales (ver 01, 5.2).
"""

from __future__ import annotations

import random
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ZONA = ZoneInfo("Europe/Madrid")
SEMILLA_CITAS = 42
RAIZ = Path(__file__).resolve().parents[1]

# (sku, nombre_es, nombre_en, categoria, marca, precio_centimos, stock, descripcion_es, descripcion_en)
_PRODUCTOS: tuple[tuple[str, str, str, str, str, int, int, str, str], ...] = (
    ("P001", "Pienso perro adulto 3 kg", "Adult dog food 3 kg", "alimentación", "Campo Verde", 1450, 25,
     "Alimento completo para perros adultos de raza media. Con pollo y arroz.",
     "Complete food for medium-breed adult dogs. With chicken and rice."),
    ("P002", "Pienso perro adulto 15 kg", "Adult dog food 15 kg", "alimentación", "Campo Verde", 4990, 12,
     "Alimento completo para perros adultos de raza media. Con pollo y arroz.",
     "Complete food for medium-breed adult dogs. With chicken and rice."),
    ("P003", "Pienso cachorro 3 kg", "Puppy food 3 kg", "alimentación", "Campo Verde", 1590, 18,
     "Alimento completo para cachorros hasta 12 meses. Con pollo.",
     "Complete food for puppies up to 12 months. With chicken."),
    ("P004", "Pienso gato adulto 2 kg", "Adult cat food 2 kg", "alimentación", "Luna Gato", 1190, 30,
     "Alimento completo para gatos adultos. Con pescado.",
     "Complete food for adult cats. With fish."),
    ("P005", "Pienso gato esterilizado 2 kg", "Neutered cat food 2 kg", "alimentación", "Luna Gato", 1290, 22,
     "Alimento completo para gatos esterilizados. Bajo en grasa.",
     "Complete food for neutered cats. Low in fat."),
    ("P006", "Latas de pavo para gato (pack 6)", "Turkey cat cans (6 pack)", "alimentación", "Luna Gato", 790, 40,
     "Alimento húmedo de pavo. Seis latas de 85 g.",
     "Wet turkey food. Six 85 g cans."),
    ("P007", "Snack dental para perros", "Dental chew for dogs", "snacks", "DentiPet", 620, 50,
     "Snack masticable que ayuda a reducir el sarro.",
     "Chewable snack that helps reduce tartar."),
    ("P008", "Snack de pollo para perros", "Chicken treats for dogs", "snacks", "Campo Verde", 450, 60,
     "Snack blando de pollo, sin colorantes añadidos.",
     "Soft chicken snack, with no added colourings."),
    ("P009", "Antiparasitario externo perro pequeño", "Flea and tick spot-on, small dog", "salud", "Protecan", 1890, 15,
     "Pipeta antiparasitaria externa. Pregunta a un veterinario por la dosis.",
     "External antiparasitic spot-on. Ask a vet about the dose."),
    ("P010", "Antiparasitario externo perro grande", "Flea and tick spot-on, large dog", "salud", "Protecan", 2290, 0,
     "Pipeta antiparasitaria externa. Pregunta a un veterinario por la dosis.",
     "External antiparasitic spot-on. Ask a vet about the dose."),
    ("P011", "Antiparasitario externo gato", "Flea and tick spot-on, cat", "salud", "Protecan", 1690, 20,
     "Pipeta antiparasitaria externa. Pregunta a un veterinario por la dosis.",
     "External antiparasitic spot-on. Ask a vet about the dose."),
    ("P012", "Champú hipoalergénico", "Hypoallergenic shampoo", "higiene", "PelBrillo", 990, 16,
     "Champú suave para pieles sensibles. Sin perfume.",
     "Gentle shampoo for sensitive skin. Fragrance free."),
    ("P013", "Cepillo suave", "Soft brush", "higiene", "PelBrillo", 650, 35,
     "Cepillo de cerdas suaves para pelo corto.",
     "Soft-bristle brush for short hair."),
    ("P014", "Pasta dental con cepillo", "Toothpaste with brush", "higiene", "DentiPet", 840, 28,
     "Pasta dental sabor pollo y cepillo de dedo.",
     "Chicken-flavoured toothpaste with finger brush."),
    ("P015", "Collar ajustable talla M", "Adjustable collar, size M", "accesorios", "Paseo", 790, 24,
     "Collar de nylon ajustable con cierre de seguridad.",
     "Adjustable nylon collar with safety buckle."),
    ("P016", "Collar ajustable talla L", "Adjustable collar, size L", "accesorios", "Paseo", 890, 3,
     "Collar de nylon ajustable con cierre de seguridad.",
     "Adjustable nylon collar with safety buckle."),
    ("P017", "Correa extensible 5 m", "Retractable leash 5 m", "accesorios", "Paseo", 1590, 14,
     "Correa con freno y cinta de 5 metros.",
     "Leash with brake and 5 metre tape."),
    ("P018", "Arnés talla M", "Harness, size M", "accesorios", "Paseo", 1990, 9,
     "Arnés acolchado de ajuste rápido.",
     "Padded harness with quick adjustment."),
    ("P019", "Rascador pequeño", "Small scratching post", "juguetes", "Luna Gato", 2490, 7,
     "Rascador de sisal de 40 cm.",
     "40 cm sisal scratching post."),
    ("P020", "Pelota de goma", "Rubber ball", "juguetes", "Paseo", 390, 80,
     "Pelota de goma resistente de 6 cm.",
     "Hard-wearing 6 cm rubber ball."),
)

# (id, nombre_es, nombre_en, duracion_min, precio_centimos)
_SERVICIOS: tuple[tuple[int, str, str, int, int], ...] = (
    (1, "Consulta general", "General check-up", 30, 2500),
    (2, "Vacunación", "Vaccination", 20, 3500),
    (3, "Desparasitación", "Deworming", 20, 2000),
    (4, "Limpieza dental", "Dental cleaning", 60, 9000),
    (5, "Revisión dermatológica", "Skin check", 40, 4500),
    (6, "Baño y peluquería", "Grooming", 60, 3000),
)

# (id, nombre, especialidad)
_VETERINARIOS: tuple[tuple[int, str, str], ...] = (
    (1, "Marta Ruiz", "medicina general"),
    (2, "Pablo Soler", "cirugía"),
    (3, "Lucía Vega", "dermatología y animales exóticos"),
)

# (veterinario_id, dia_semana, hora_inicio, hora_fin)
_TURNOS: tuple[tuple[int, int, str, str], ...] = (
    *[(1, d, "09:00", "14:00") for d in (0, 1, 2, 3, 4)],
    (2, 1, "15:00", "20:00"),
    (2, 3, "15:00", "20:00"),
    (2, 5, "10:00", "14:00"),
    *[(3, d, "15:00", "20:00") for d in (0, 2, 4)],
)

# (dia_semana, hora_apertura, hora_cierre). Domingo cerrado: sin fila.
_HORARIO_NEGOCIO: tuple[tuple[int, str, str], ...] = (
    *[(d, "09:00", "20:00") for d in (0, 1, 2, 3, 4)],
    (5, "10:00", "14:00"),
)


def crear_conexion() -> sqlite3.Connection:
    """Abre una base SQLite en memoria solo para la sesión actual.

    Devuelve: conexión con filas accesibles por nombre de columna.
    Ejemplo:
        >>> conn = crear_conexion()
        >>> conn.execute("SELECT 1").fetchone()[0]
        1
    """
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    return conn


def crear_esquema(conn: sqlite3.Connection) -> None:
    """Crea las tablas ejecutando data/esquema.sql.

    Parámetros:
        conn: conexión SQLite abierta.
    Ejemplo:
        >>> conn = crear_conexion(); crear_esquema(conn)
    """
    sql = (RAIZ / "data" / "esquema.sql").read_text(encoding="utf-8")
    conn.executescript(sql)


def cargar_semilla(conn: sqlite3.Connection, hoy: date | None = None) -> None:
    """Inserta los datos ficticios de docs/04_DATOS_FICTICIOS.md.

    Parámetros:
        conn: conexión con el esquema ya creado.
        hoy: fecha de referencia para las citas de ejemplo; por defecto hoy.
    Errores:
        sqlite3.IntegrityError si la semilla ya se cargó en esta conexión.
    Ejemplo:
        >>> conn = crear_conexion(); crear_esquema(conn); cargar_semilla(conn)
    """
    if hoy is None:
        hoy = datetime.now(ZONA).date()
    with conn:
        conn.execute(
            "INSERT INTO negocio (id, nombre, nombre_bot, telefono, correo,"
            " trato_por_defecto, idioma_por_defecto)"
            " VALUES (1, ?, ?, ?, ?, ?, ?)",
            ("Mascota Feliz", "Ana", "900 000 000",
             "contacto@mascotafeliz.example", "tu", "es"),
        )
        conn.executemany(
            "INSERT INTO productos (sku, nombre_es, nombre_en, categoria, marca,"
            " precio_centimos, stock, descripcion_es, descripcion_en)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7], p[8]) for p in _PRODUCTOS],
        )
        conn.executemany(
            "INSERT INTO servicios (id, nombre_es, nombre_en, duracion_min,"
            " precio_centimos) VALUES (?, ?, ?, ?, ?)",
            list(_SERVICIOS),
        )
        conn.executemany(
            "INSERT INTO veterinarios (id, nombre, especialidad) VALUES (?, ?, ?)",
            list(_VETERINARIOS),
        )
        conn.executemany(
            "INSERT INTO turnos (veterinario_id, dia_semana, hora_inicio, hora_fin)"
            " VALUES (?, ?, ?, ?)",
            list(_TURNOS),
        )
        conn.executemany(
            "INSERT INTO horarios_negocio (dia_semana, hora_apertura, hora_cierre)"
            " VALUES (?, ?, ?)",
            list(_HORARIO_NEGOCIO),
        )
        for anno in (hoy.year, hoy.year + 1):
            conn.executemany(
                "INSERT OR IGNORE INTO dias_especiales (fecha, cerrado,"
                " hora_apertura, hora_cierre, nota) VALUES (?, 1, NULL, NULL, ?)",
                [(f"{anno}-12-25", "Festivo"), (f"{anno}-01-01", "Festivo")],
            )
        _cargar_citas_ejemplo(conn, hoy)


def _cargar_citas_ejemplo(conn: sqlite3.Connection, hoy: date) -> None:
    """Crea 6 citas de ejemplo reproducibles en días laborables próximos.

    Por qué aleatoriedad con semilla fija: cada sesión empieza con huecos
    ocupados pero siempre los mismos, para que la demo sea repetible.
    """
    rng = random.Random(SEMILLA_CITAS)
    turnos_por_dia: dict[int, list[tuple[int, str, str]]] = {}
    for vet, dia_sem, ini, fin in _TURNOS:
        turnos_por_dia.setdefault(dia_sem, []).append((vet, ini, fin))
    abiertas = {d for d, _, _ in _HORARIO_NEGOCIO}
    puestas = 0
    dia = hoy + timedelta(days=1)
    while puestas < 6:
        if dia.weekday() in abiertas:
            candidatos = turnos_por_dia.get(dia.weekday(), [])
            if candidatos:
                vet, ini, fin = candidatos[puestas % len(candidatos)]
                partes_ini = ini.split(":")
                partes_fin = fin.split(":")
                base_h, base_m = int(partes_ini[0]), int(partes_ini[1])
                # Desplazamiento reproducible dentro del turno.
                extra = rng.choice([30, 60, 90, 120])
                inicio = datetime(dia.year, dia.month, dia.day, base_h, base_m) + timedelta(minutes=extra)
                fin_turno = datetime(dia.year, dia.month, dia.day,
                                     int(partes_fin[0]), int(partes_fin[1]))
                if inicio + timedelta(minutes=30) <= fin_turno:
                    conn.execute(
                        "INSERT INTO citas (veterinario_id, servicio_id, inicio, fin,"
                        " alias_cliente) VALUES (?, 1, ?, ?, ?)",
                        (vet, inicio.strftime("%Y-%m-%dT%H:%M"),
                         (inicio + timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M"),
                         f"Cliente de ejemplo {puestas + 1}"),
                    )
                    puestas += 1
        dia += timedelta(days=1)


def iniciar_bd(hoy: date | None = None) -> sqlite3.Connection:
    """Crea y deja lista una base de sesión: esquema más semilla.

    Parámetros:
        hoy: fecha de referencia opcional para las citas de ejemplo.
    Devuelve: conexión lista para consultar.
    Ejemplo:
        >>> conn = iniciar_bd()
        >>> conn.execute("SELECT COUNT(*) FROM productos").fetchone()[0]
        20
    """
    conn = crear_conexion()
    crear_esquema(conn)
    cargar_semilla(conn, hoy)
    return conn
