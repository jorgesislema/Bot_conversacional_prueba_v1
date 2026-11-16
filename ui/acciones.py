"""Acciones guiadas del panel "Prueba el motor".

Qué hace: cambia el precio de un producto, añade un producto nuevo y
cambia el horario de un día, siempre con validación y registro en
registro_eventos. También prepara la pregunta que el visitante puede
enviar al chat para ver el cambio al instante. Recibe: conexión SQLite
de la sesión y los valores del formulario. Devuelve: un Cambio con el
resumen y la pregunta sugerida. Qué NO hace: no dibuja nada en pantalla
(eso lo hace app.py) ni guarda datos fuera de la sesión.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from ui.panel import euros_a_centimos, validar_horas, validar_stock

# Días de la semana con 0 = lunes, igual que en data/esquema.sql.
DIAS_ES = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")
DIAS_EN = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")

# Categorías que el visitante puede elegir al añadir un producto. Son las
# mismas de la semilla, para que el buscador del bot las reconozca.
CATEGORIAS = ("alimentación", "snacks", "salud", "higiene", "accesorios", "juguetes")


@dataclass
class Cambio:
    """Resultado de una acción del panel.

    Atributos:
        resumen: texto corto para el registro y el aviso verde.
        pregunta_es: pregunta lista para enviar al chat en español.
        pregunta_en: la misma pregunta en inglés.
    """

    resumen: str
    pregunta_es: str
    pregunta_en: str

    def pregunta(self, idioma: str) -> str:
        """Devuelve la pregunta sugerida en el idioma pedido.

        Ejemplo:
            >>> Cambio("x", "hola", "hello").pregunta("en")
            'hello'
        """
        return self.pregunta_en if idioma == "en" else self.pregunta_es


def formatear_euros(centimos: int, idioma: str = "es") -> str:
    """Formatea céntimos como "49,90 EUR" (ES) o "49.90 EUR" (EN).

    Ejemplo:
        >>> formatear_euros(4990)
        '49,90 EUR'
    """
    texto = f"{centimos / 100:.2f}"
    if idioma != "en":
        texto = texto.replace(".", ",")
    return f"{texto} EUR"


def _registrar(conn: sqlite3.Connection, detalle: str) -> None:
    """Anota el cambio en registro_eventos (auditoría de la demo)."""
    conn.execute(
        "INSERT INTO registro_eventos (tipo, detalle, creado)"
        " VALUES ('cambio_panel', ?, datetime('now'))",
        (detalle,),
    )


def cambiar_precio(conn: sqlite3.Connection, producto_id: int, euros: str) -> Cambio:
    """Cambia el precio de un producto activo.

    Parámetros:
        conn: conexión SQLite de la sesión.
        producto_id: id del producto.
        euros: precio nuevo en euros con coma o punto ("44,90").
    Devuelve: el cambio con la pregunta sugerida.
    Errores:
        ValueError("error_precio") si el precio no es válido.
        ValueError("error_producto") si el producto no existe.
    Ejemplo:
        >>> cambiar_precio(conn, 2, "44,90").resumen  # doctest: +SKIP
        'Pienso perro adulto 15 kg: 49,90 EUR -> 44,90 EUR'
    """
    centimos = euros_a_centimos(euros)
    fila = conn.execute(
        "SELECT nombre_es, nombre_en, precio_centimos FROM productos WHERE id = ?",
        (producto_id,),
    ).fetchone()
    if fila is None:
        raise ValueError("error_producto")
    resumen = (f"{fila['nombre_es']}: {formatear_euros(int(fila['precio_centimos']))}"
               f" -> {formatear_euros(centimos)}")
    with conn:
        conn.execute("UPDATE productos SET precio_centimos = ? WHERE id = ?",
                     (centimos, producto_id))
        _registrar(conn, resumen)
    return Cambio(
        resumen,
        f"Cuánto cuesta el {fila['nombre_es']}?",
        f"How much is the {fila['nombre_en']}?",
    )


def anadir_producto(
    conn: sqlite3.Connection,
    nombre_es: str,
    categoria: str,
    euros: str,
    stock: object,
    descripcion_es: str = "",
    nombre_en: str = "",
    descripcion_en: str = "",
    marca: str = "Mascota Feliz",
) -> Cambio:
    """Añade un producto nuevo al catálogo de la sesión.

    Por qué el nombre en inglés copia al español si llega vacío: el bot
    necesita un nombre en cada idioma y es mejor mostrar el original que
    inventar una traducción.

    Parámetros:
        conn: conexión SQLite de la sesión.
        nombre_es: nombre del producto (obligatorio, 3 a 80 caracteres).
        categoria: una de CATEGORIAS.
        euros: precio con IVA incluido.
        stock: unidades disponibles (entero mayor o igual a 0).
        descripcion_es, nombre_en, descripcion_en, marca: opcionales.
    Devuelve: el cambio con la pregunta sugerida.
    Errores:
        ValueError("error_nombre"), ValueError("error_categoria"),
        ValueError("error_precio") o ValueError("error_stock").
    Ejemplo:
        >>> anadir_producto(conn, "Snack dental gato", "snacks", "6,20", 30)  # doctest: +SKIP
    """
    nombre = " ".join(nombre_es.split())
    if not 3 <= len(nombre) <= 80:
        raise ValueError("error_nombre")
    if categoria not in CATEGORIAS:
        raise ValueError("error_categoria")
    centimos = euros_a_centimos(euros)
    unidades = validar_stock(stock)
    existe = conn.execute(
        "SELECT 1 FROM productos WHERE lower(nombre_es) = lower(?)", (nombre,)
    ).fetchone()
    if existe is not None:
        raise ValueError("error_nombre_repetido")
    nombre_ingles = " ".join(nombre_en.split()) or nombre
    descripcion = " ".join(descripcion_es.split()) or nombre
    descripcion_ingles = " ".join(descripcion_en.split()) or descripcion
    total = conn.execute("SELECT COUNT(*) FROM productos").fetchone()[0]
    sku = f"N{int(total) + 1:03d}"
    resumen = f"Nuevo: {nombre}, {formatear_euros(centimos)}, stock {unidades}"
    with conn:
        conn.execute(
            "INSERT INTO productos (sku, nombre_es, nombre_en, descripcion_es,"
            " descripcion_en, categoria, marca, precio_centimos, stock)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (sku, nombre, nombre_ingles, descripcion, descripcion_ingles,
             categoria, " ".join(marca.split()) or "Mascota Feliz", centimos, unidades),
        )
        _registrar(conn, resumen)
    return Cambio(resumen, f"Tienen {nombre}?", f"Do you have {nombre_ingles}?")


def cambiar_horario(
    conn: sqlite3.Connection,
    dia_semana: int,
    apertura: str,
    cierre: str,
    cerrado: bool = False,
) -> Cambio:
    """Cambia el horario de un día de la semana o lo marca como cerrado.

    Por qué cerrar es borrar la fila: core/huecos.py considera cerrado
    todo día sin fila en horarios_negocio, así no hay dos formas de
    decir lo mismo.

    Parámetros:
        conn: conexión SQLite de la sesión.
        dia_semana: 0 = lunes ... 6 = domingo.
        apertura, cierre: horas HH:MM (se ignoran si cerrado).
        cerrado: verdadero para cerrar ese día.
    Devuelve: el cambio con la pregunta sugerida.
    Errores:
        ValueError("error_horas") si las horas no son válidas o el día
        no existe.
    Ejemplo:
        >>> cambiar_horario(conn, 5, "10:00", "15:00").resumen  # doctest: +SKIP
        'Horario del sábado: 10:00 a 15:00'
    """
    if not 0 <= dia_semana <= 6:
        raise ValueError("error_horas")
    dia_es, dia_en = DIAS_ES[dia_semana], DIAS_EN[dia_semana]
    with conn:
        if cerrado:
            conn.execute("DELETE FROM horarios_negocio WHERE dia_semana = ?",
                         (dia_semana,))
            resumen = f"Horario del {dia_es}: cerrado"
        else:
            validar_horas(apertura, cierre)
            conn.execute(
                "INSERT INTO horarios_negocio (dia_semana, hora_apertura, hora_cierre)"
                " VALUES (?, ?, ?) ON CONFLICT (dia_semana) DO UPDATE SET"
                " hora_apertura = excluded.hora_apertura,"
                " hora_cierre = excluded.hora_cierre",
                (dia_semana, apertura, cierre),
            )
            resumen = f"Horario del {dia_es}: {apertura} a {cierre}"
        _registrar(conn, resumen)
    return Cambio(resumen, f"A qué hora abren el {dia_es}?",
                  f"What time do you open on {dia_en}?")


def ultimos_cambios(conn: sqlite3.Connection, limite: int = 5) -> list[str]:
    """Devuelve los últimos cambios del panel, del más nuevo al más viejo.

    Ejemplo:
        >>> ultimos_cambios(conn)  # doctest: +SKIP
        ['Horario del sábado: 10:00 a 15:00']
    """
    filas = conn.execute(
        "SELECT detalle FROM registro_eventos WHERE tipo = 'cambio_panel'"
        " ORDER BY id DESC LIMIT ?",
        (limite,),
    ).fetchall()
    return [str(f["detalle"]) for f in filas]


def productos_para_selector(conn: sqlite3.Connection, idioma: str) -> list[tuple[int, str]]:
    """Lista (id, "nombre - precio") de productos activos para un selector.

    Ejemplo:
        >>> productos_para_selector(conn, "es")[0]  # doctest: +SKIP
        (1, 'Pienso perro adulto 3 kg - 14,50 EUR')
    """
    columna = "nombre_en" if idioma == "en" else "nombre_es"
    filas = conn.execute(
        f"SELECT id, {columna} AS nombre, precio_centimos FROM productos"
        " WHERE activo = 1 ORDER BY id"
    ).fetchall()
    return [(int(f["id"]),
             f"{f['nombre']} - {formatear_euros(int(f['precio_centimos']), idioma)}")
            for f in filas]


def precio_actual(conn: sqlite3.Connection, producto_id: int, idioma: str = "es") -> str:
    """Precio actual del producto sin moneda, listo para editar ("14,50").

    Ejemplo:
        >>> precio_actual(conn, 1)  # doctest: +SKIP
        '14,50'
    """
    fila = conn.execute("SELECT precio_centimos FROM productos WHERE id = ?",
                        (producto_id,)).fetchone()
    if fila is None:
        return ""
    return formatear_euros(int(fila["precio_centimos"]), idioma).removesuffix(" EUR")


def horario_de(conn: sqlite3.Connection, dia_semana: int) -> tuple[str, str] | None:
    """Devuelve (apertura, cierre) del día o None si está cerrado."""
    fila = conn.execute(
        "SELECT hora_apertura, hora_cierre FROM horarios_negocio WHERE dia_semana = ?",
        (dia_semana,),
    ).fetchone()
    if fila is None:
        return None
    return str(fila["hora_apertura"]), str(fila["hora_cierre"])
