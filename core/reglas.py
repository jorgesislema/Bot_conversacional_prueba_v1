"""Convierte intención y estado en hechos leyendo la base de datos.
Qué hace: busca productos, servicios y veterinarios con tolerancia a
faltas, calcula precios, stock, horarios y citas, y registra compras y
citas solo tras un sí explícito. Recibe: conexión, estado, intención y
hora actual. Devuelve: hechos para redactar. Qué NO hace: no usa IA ni
escribe texto para el cliente (eso es redactar y plantillas).
"""

from __future__ import annotations

import re
import sqlite3
import unicodedata
from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from rapidfuzz import fuzz

from core.estado import Estado, guardar_candidatos, limpiar_tema
from core.huecos import dia_abierto, huecos_disponibles, huecos_negocio, siguiente_dia_abierto

ZONA = ZoneInfo("Europe/Madrid")
UMBRAL_PRODUCTO = 55
UMBRAL_DECISION = 88
MARGEN_DECISION = 12
DIAS_BUSQUEDA_CITA = 14

_DIAS_ES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
_DIAS_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
_MESES_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
             "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
_MESES_EN = ["January", "February", "March", "April", "May", "June", "July",
             "August", "September", "October", "November", "December"]


def _normalizar(texto: str) -> str:
    """Pone en minúsculas y quita acentos para comparar sin faltas."""
    base = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in base if not unicodedata.combining(c))


def _palabras(texto: str) -> list[str]:
    """Divide en palabras y quita plurales simples para tolerar errores."""
    palabras = []
    for token in _normalizar(texto).replace("/", " ").split():
        token = "".join(c for c in token if c.isalnum())
        if len(token) > 4 and token.endswith("es"):
            token = token[:-2]
        elif len(token) > 3 and token.endswith("s"):
            token = token[:-1]
        if token:
            palabras.append(token)
    return palabras


def _puntuacion(texto: str, nombre: str) -> float:
    """Puntúa de 0 a 100 cuánto se parece el texto al nombre."""
    base = fuzz.WRatio(_normalizar(texto), _normalizar(nombre))
    pedidas = set(_palabras(texto))
    propias = set(_palabras(nombre))
    # Extra por palabras coincidentes: ayuda con "pienso perro adulto".
    extra = 0.0
    if pedidas and propias:
        extra = 20.0 * len(pedidas & propias) / len(pedidas)
    return min(100.0, base + extra)


def _detalles(texto: str) -> set[str]:
    """Extrae tallas y cantidades ("15 kg", "talla L") para desempatar."""
    norma = _normalizar(texto)
    detalles = set(re.findall(r"\d+\s*[a-z]*", norma))
    detalles.update(re.findall(r"talla\s+([a-z])", norma))
    return {d.strip() for d in detalles if d.strip()}


def _fila_a_dict(fila: sqlite3.Row) -> dict[str, Any]:
    """Convierte una fila SQLite en diccionario."""
    return {clave: fila[clave] for clave in fila.keys()}


def buscar_productos(
    conn: sqlite3.Connection, texto: str, idioma: str, limite: int = 4
) -> list[dict[str, Any]]:
    """Busca productos activos tolerando faltas de escritura.

    Parámetros:
        conn: conexión SQLite con la semilla.
        texto: lo que escribió el usuario.
        idioma: "es" o "en" para elegir el nombre.
        limite: máximo de candidatos.
    Devuelve: productos ordenados por puntuación (vacío si no hay).
    Ejemplo:
        >>> conn = __import__("core.esquema", fromlist=["iniciar_bd"]).iniciar_bd()
        >>> [p["sku"] for p in buscar_productos(conn, "cepilo", "es")[:1]]
        ['P013']
    """
    campo = "nombre_es" if idioma == "es" else "nombre_en"
    if not texto.strip():
        return []
    detalles_usuario = _detalles(texto)
    palabras_usuario = set(_palabras(texto))
    filas = conn.execute("SELECT * FROM productos WHERE activo = 1").fetchall()
    puntuados: list[tuple[float, dict[str, Any]]] = []
    for fila in filas:
        nombre = str(fila[campo])
        puntos = _puntuacion(texto, nombre)
        palabras_nombre = set(_palabras(nombre))
        # Mención exacta del nombre: gana sin discutir.
        if palabras_nombre <= palabras_usuario:
            puntos = 100.0
        # La talla o cantidad pedida debe coincidir con el candidato.
        detalles_nombre = _detalles(nombre)
        if detalles_usuario:
            if detalles_usuario <= detalles_nombre:
                puntos += 20.0
            else:
                puntos -= 50.0
        if puntos >= UMBRAL_PRODUCTO:
            puntuados.append((min(100.0, puntos), _fila_a_dict(fila)))
    puntuados.sort(key=lambda x: -x[0])
    return [f for _, f in puntuados[:limite]]


def buscar_servicio(
    conn: sqlite3.Connection, texto: str, idioma: str
) -> dict[str, Any] | None:
    """Busca el servicio que mejor encaja con el texto."""
    campo = "nombre_es" if idioma == "es" else "nombre_en"
    if not texto.strip():
        return None
    mejor: dict[str, Any] | None = None
    mejor_puntos = 60.0
    for fila in conn.execute("SELECT * FROM servicios WHERE activo = 1").fetchall():
        puntos = fuzz.WRatio(_normalizar(texto), _normalizar(str(fila[campo])))
        if puntos >= mejor_puntos:
            mejor_puntos = float(puntos)
            mejor = _fila_a_dict(fila)
    return mejor


def buscar_veterinario(conn: sqlite3.Connection, texto: str) -> dict[str, Any] | None:
    """Busca un veterinario por nombre, tolerando tratamiento (Dra.)."""
    if not texto.strip():
        return None
    mejor: dict[str, Any] | None = None
    mejor_puntos = 60.0
    for fila in conn.execute("SELECT * FROM veterinarios WHERE activo = 1").fetchall():
        nombre = str(fila["nombre"])
        puntos = max(
            fuzz.WRatio(_normalizar(texto), _normalizar(nombre)),
            fuzz.WRatio(_normalizar(texto), _normalizar(nombre.split()[-1])),
        )
        if puntos >= mejor_puntos:
            mejor_puntos = float(puntos)
            mejor = _fila_a_dict(fila)
    return mejor


def formatear_precio(centimos: int, idioma: str) -> str:
    """Formatea céntimos a "49,90 EUR" en ES y "49.90 EUR" en EN."""
    euros, resto = divmod(int(centimos), 100)
    if idioma == "en":
        return f"{euros}.{resto:02d} EUR"
    return f"{euros},{resto:02d} EUR"


def nombre_dia(dia: date, idioma: str) -> str:
    """Nombra un día como "jueves 20 de noviembre" o "Thursday 20 November"."""
    if idioma == "en":
        return f"{_DIAS_EN[dia.weekday()]} {dia.day} {_MESES_EN[dia.month - 1]}"
    return f"{_DIAS_ES[dia.weekday()]} {dia.day} de {_MESES_ES[dia.month - 1]}"


def _hechos(
    tipo: str, estado: Estado, datos: dict[str, Any] | None = None,
    pregunta: str = "", permitido: list[str] | None = None,
) -> dict[str, Any]:
    """Arma el diccionario de hechos de docs/05, sección 3."""
    return {
        "tipo_respuesta": tipo,
        "idioma": estado.idioma,
        "trato": estado.trato,
        "datos": datos or {},
        "pregunta_siguiente": pregunta,
        "permitido_mencionar": permitido or [],
    }


def _nombre_producto(producto: dict[str, Any], idioma: str) -> str:
    """Elige el nombre del producto en el idioma activo."""
    return str(producto["nombre_es"] if idioma == "es" else producto["nombre_en"])


def _descripcion_producto(producto: dict[str, Any], idioma: str) -> str:
    """Elige la descripción en el idioma activo."""
    return str(producto["descripcion_es"] if idioma == "es" else producto["descripcion_en"])


def resolver(
    conn: sqlite3.Connection, estado: Estado, entendido: dict[str, Any], ahora: datetime
) -> dict[str, Any]:
    """Convierte la intención entendida en hechos con datos de la base.

    Parámetros:
        conn: conexión SQLite de la sesión.
        estado: memoria de la conversación (se actualiza).
        entendido: JSON de entender (docs/05, sección 2).
        ahora: instante actual para validar fechas y horas.
    Devuelve: hechos listos para redactar o para plantillas.
    Ejemplo:
        >>> from core.esquema import iniciar_bd
        >>> from core.estado import crear_estado
        >>> from datetime import date, datetime
        >>> conn = iniciar_bd(date(2026, 11, 16))
        >>> h = resolver(conn, crear_estado(), {"intencion": "saludo"},
        ...     datetime(2026, 11, 16, 8, 0, tzinfo=ZONA))
        >>> h["tipo_respuesta"]
        'saludo'
    """
    from core.estado import fijar_trato_inicial  # Importe local: evita ciclos.

    idioma = str(entendido.get("idioma", estado.idioma))
    if idioma in ("es", "en"):
        estado.idioma = idioma
    fijar_trato_inicial(estado, str(entendido.get("trato", "desconocido")))
    intencion = str(entendido.get("intencion", "no_entendido"))

    if intencion == "precio_producto":
        return _resolver_producto(conn, estado, entendido, "precio")
    if intencion == "descripcion_producto":
        return _resolver_producto(conn, estado, entendido, "descripcion")
    if intencion == "disponibilidad":
        return _resolver_producto(conn, estado, entendido, "stock")
    if intencion == "comparar_productos":
        return _resolver_comparar(conn, estado, entendido)
    if intencion == "horario_negocio":
        return _resolver_horario_negocio(conn, estado, entendido, ahora)
    if intencion == "horario_veterinario":
        return _resolver_horario_veterinario(conn, estado, entendido, ahora)
    if intencion == "pedir_cita":
        return _resolver_pedir_cita(conn, estado, entendido, ahora)
    if intencion == "consultar_servicio":
        return _resolver_servicio(conn, estado, entendido)
    if intencion == "confirmar":
        return _resolver_confirmar(conn, estado, ahora)
    if intencion == "rechazar":
        estado.propuesta_pendiente = None
        return _hechos("anulado", estado)
    if intencion == "hablar_con_persona":
        negocio = _fila_a_dict(conn.execute("SELECT * FROM negocio").fetchone())
        datos = {"telefono": str(negocio["telefono"]), "correo": str(negocio["correo"])}
        return _hechos("derivar", estado, datos, permitido=list(datos.values()))
    if intencion == "es_ia":
        negocio = _fila_a_dict(conn.execute("SELECT * FROM negocio").fetchone())
        nombre = str(negocio["nombre"])
        return _hechos("aviso_ia", estado, {"negocio": nombre}, permitido=[nombre])
    if intencion == "urgencia_clinica":
        negocio = _fila_a_dict(conn.execute("SELECT * FROM negocio").fetchone())
        telefono = str(negocio["telefono"])
        return _hechos("urgencia", estado, {"telefono": telefono}, permitido=[telefono])
    if intencion in ("saludo", "despedida", "gracias"):
        limpiar_tema(estado)
        return _hechos(intencion, estado)
    if intencion == "fuera_de_alcance":
        return _hechos("rechazo_alcance", estado)
    return _hechos("no_se", estado)


def _candidato_por_referencia(
    estado: Estado, conn: sqlite3.Connection, referencia: str
) -> dict[str, Any] | None:
    """Devuelve el producto al que apunta la referencia del usuario."""
    if referencia in ("ese", "el_primero", "el_segundo", "el_grande", "el_pequeno"):
        if referencia == "ese" and estado.producto_actual:
            fila = conn.execute(
                "SELECT * FROM productos WHERE id = ?", (estado.producto_actual,)
            ).fetchone()
            return _fila_a_dict(fila) if fila else None
        if not estado.candidatos:
            return None
        if referencia in ("ese", "el_primero"):
            fila = conn.execute(
                "SELECT * FROM productos WHERE id = ?", (estado.candidatos[0],)
            ).fetchone()
            return _fila_a_dict(fila) if fila else None
        if referencia == "el_segundo" and len(estado.candidatos) > 1:
            fila = conn.execute(
                "SELECT * FROM productos WHERE id = ?", (estado.candidatos[1],)
            ).fetchone()
            return _fila_a_dict(fila) if fila else None
        filas = [
            _fila_a_dict(f)
            for c in estado.candidatos
            for f in [conn.execute("SELECT * FROM productos WHERE id = ?", (c,)).fetchone()]
            if f is not None
        ]
        if not filas:
            return None
        if referencia == "el_grande":
            return max(filas, key=lambda f: int(f["precio_centimos"]))
        return min(filas, key=lambda f: int(f["precio_centimos"]))
    return None


def _resolver_producto(
    conn: sqlite3.Connection, estado: Estado, entendido: dict[str, Any], modo: str
) -> dict[str, Any]:
    """Resuelve precio, descripción o stock de un producto."""
    idioma = estado.idioma
    referencia = str(entendido.get("referencia", "ninguna"))
    producto = _candidato_por_referencia(estado, conn, referencia)
    candidatos: list[dict[str, Any]] = [producto] if producto else []
    if not candidatos:
        texto = str(entendido.get("producto_texto", ""))
        if not texto.strip() and estado.producto_actual and referencia == "ninguna":
            fila = conn.execute(
                "SELECT * FROM productos WHERE id = ?", (estado.producto_actual,)
            ).fetchone()
            candidatos = [_fila_a_dict(fila)] if fila else []
        else:
            candidatos = buscar_productos(conn, texto, idioma)
    if not candidatos:
        return _hechos("no_se", estado)
    texto = str(entendido.get("producto_texto", ""))
    # Nombre exacto escrito por el cliente: gana sin discutir.
    exactos = [c for c in candidatos
               if _normalizar(_nombre_producto(c, idioma)) == _normalizar(texto)]
    if exactos:
        candidatos = exactos[:1]
    if len(candidatos) > 1:
        palabras = set(_palabras(texto))
        # Palabra que solo aparece en un candidato: decide ("grande", "gato").
        distintivas = [
            p for p in palabras
            if sum(1 for c in candidatos
                   if p in _palabras(_nombre_producto(c, idioma))) == 1
        ]
        if distintivas:
            con_todas = [
                c for c in candidatos
                if all(p in _palabras(_nombre_producto(c, idioma))
                       for p in distintivas)
            ]
            if len(con_todas) == 1:
                candidatos = con_todas
    if len(candidatos) > 1:
        texto = str(entendido.get("producto_texto", ""))
        puntuaciones = [
            _puntuacion(texto, _nombre_producto(c, idioma)) for c in candidatos
        ]
        if not (puntuaciones[0] >= UMBRAL_DECISION
                and puntuaciones[0] - max(puntuaciones[1:]) >= MARGEN_DECISION):
            guardar_candidatos(estado, [int(c["id"]) for c in candidatos])
            nombres = [_nombre_producto(c, idioma) for c in candidatos]
            lista = ", ".join(nombres)
            return _hechos(
                "aclaracion_producto", estado, {"lista": lista}, permitido=nombres
            )
        candidatos = candidatos[:1]
    elegido = candidatos[0]
    estado.producto_actual = int(elegido["id"])
    guardar_candidatos(estado, [])
    nombre = _nombre_producto(elegido, idioma)
    precio = formatear_precio(int(elegido["precio_centimos"]), idioma)
    stock = int(elegido["stock"])
    if modo == "descripcion":
        descripcion = _descripcion_producto(elegido, idioma)
        permitido = [nombre] + re.findall(r"\d+", descripcion)
        return _hechos(
            "descripcion", estado,
            {"producto": nombre, "descripcion": descripcion},
            permitido=permitido,
        )
    if modo == "stock":
        return _hechos_stock(conn, estado, elegido, nombre, precio, stock, idioma)
    cantidad = int(entendido.get("cantidad", 0) or 0) or 1
    total = formatear_precio(int(elegido["precio_centimos"]) * cantidad, idioma)
    estado.propuesta_pendiente = {
        "tipo": "compra",
        "producto_id": str(elegido["id"]),
        "cantidad": str(cantidad),
    }
    if stock >= cantidad:
        pregunta = "Quieres comprarlo?" if idioma == "es" else "Do you want to buy it?"
    else:
        pregunta = ""
    datos = {"producto": nombre, "precio": precio, "cantidad": cantidad,
             "total": total, "stock": stock}
    permitido = [nombre, precio, total, str(cantidad), str(stock)]
    return _hechos("precio", estado, datos, pregunta, permitido)


def _hechos_stock(
    conn: sqlite3.Connection, estado: Estado, elegido: dict[str, Any],
    nombre: str, precio: str, stock: int, idioma: str,
) -> dict[str, Any]:
    """Arma los hechos de disponibilidad con alternativa si hace falta."""
    if stock <= 0:
        alternativa = conn.execute(
            "SELECT * FROM productos WHERE activo = 1 AND categoria = ?"
            " AND stock > 0 AND id != ? ORDER BY stock DESC LIMIT 1",
            (str(elegido["categoria"]), int(elegido["id"])),
        ).fetchone()
        if alternativa is None:
            return _hechos("stock", estado, {"producto": nombre, "stock": 0},
                           permitido=[nombre, "0"])
        alt = _fila_a_dict(alternativa)
        nombre_alt = _nombre_producto(alt, idioma)
        precio_alt = formatear_precio(int(alt["precio_centimos"]), idioma)
        return _hechos(
            "stock", estado,
            {"producto": nombre, "stock": 0, "alternativa": nombre_alt,
             "precio": precio_alt},
            permitido=[nombre, "0", nombre_alt, precio_alt],
        )
    if stock <= 3:
        return _hechos(
            "stock", estado, {"producto": nombre, "stock": stock},
            permitido=[nombre, str(stock)],
        )
    return _hechos(
        "stock", estado, {"producto": nombre, "stock": stock},
        permitido=[nombre, str(stock)],
    )


def _resolver_comparar(
    conn: sqlite3.Connection, estado: Estado, entendido: dict[str, Any]
) -> dict[str, Any]:
    """Compara dos productos solo con datos reales del catálogo."""
    idioma = estado.idioma
    candidatos = buscar_productos(conn, str(entendido.get("producto_texto", "")), idioma)
    if len(candidatos) < 2:
        return _hechos("no_se", estado)
    par = candidatos[:2]
    guardar_candidatos(estado, [int(c["id"]) for c in par])
    partes = []
    precios = []
    for c in par:
        precio_txt = formatear_precio(int(c["precio_centimos"]), idioma)
        precios.append(precio_txt)
        descripcion = _descripcion_producto(c, idioma).rstrip(".")
        partes.append(f"{_nombre_producto(c, idioma)}: {descripcion} ({precio_txt})")
    descripcion_final = " ; ".join(partes)
    nombres = [_nombre_producto(c, idioma) for c in par]
    permitido = nombres + precios + re.findall(r"\d+", descripcion_final)
    permitido = nombres + precios + re.findall(r"\d+", descripcion_final)
    return _hechos(
        "descripcion", estado,
        {"producto": " y ".join(nombres), "descripcion": descripcion_final},
        permitido=permitido,
    )


def _resolver_horario_negocio(
    conn: sqlite3.Connection, estado: Estado, entendido: dict[str, Any], ahora: datetime
) -> dict[str, Any]:
    """Responde el horario del día pedido o del próximo día abierto."""
    hoy = ahora.astimezone(ZONA).date()
    fecha = _parse_fecha(str(entendido.get("fecha", ""))) or hoy
    if fecha < hoy:
        fecha = hoy
    if not dia_abierto(conn, fecha):
        siguiente = siguiente_dia_abierto(conn, fecha)
        return _hechos(
            "cerrado", estado, {"dia": nombre_dia(siguiente, estado.idioma)},
            permitido=[nombre_dia(siguiente, estado.idioma)],
        )
    fila = conn.execute(
        "SELECT hora_apertura, hora_cierre FROM horarios_negocio WHERE dia_semana = ?",
        (fecha.weekday(),),
    ).fetchone()
    if fila is None:
        siguiente = siguiente_dia_abierto(conn, fecha + timedelta(days=1))
        return _hechos(
            "cerrado", estado, {"dia": nombre_dia(siguiente, estado.idioma)},
            permitido=[nombre_dia(siguiente, estado.idioma)],
        )
    dia_txt = nombre_dia(fecha, estado.idioma)
    datos = {"dia": dia_txt, "apertura": str(fila["hora_apertura"]),
             "cierre": str(fila["hora_cierre"])}
    return _hechos("horario", estado, datos, permitido=list(datos.values()))


def _resolver_horario_veterinario(
    conn: sqlite3.Connection, estado: Estado, entendido: dict[str, Any], ahora: datetime
) -> dict[str, Any]:
    """Responde el turno de un veterinario en el día pedido o próximo."""
    vet = buscar_veterinario(conn, str(entendido.get("veterinario_texto", "")))
    if vet is None and estado.veterinario_actual:
        fila = conn.execute(
            "SELECT * FROM veterinarios WHERE id = ?", (estado.veterinario_actual,)
        ).fetchone()
        vet = _fila_a_dict(fila) if fila else None
    if vet is None:
        return _hechos("no_se", estado)
    estado.veterinario_actual = int(vet["id"])
    hoy = ahora.astimezone(ZONA).date()
    fecha = _parse_fecha(str(entendido.get("fecha", ""))) or hoy
    dia = max(fecha, hoy)
    for _ in range(366):
        turno = conn.execute(
            "SELECT hora_inicio, hora_fin FROM turnos"
            " WHERE veterinario_id = ? AND dia_semana = ?",
            (int(vet["id"]), dia.weekday()),
        ).fetchone()
        if turno is not None and dia_abierto(conn, dia):
            dia_txt = nombre_dia(dia, estado.idioma)
            datos = {"dia": dia_txt, "apertura": str(turno["hora_inicio"]),
                     "cierre": str(turno["hora_fin"])}
            permitido = list(datos.values()) + [str(vet["nombre"])]
            return _hechos("horario", estado, datos, permitido=permitido)
        dia += timedelta(days=1)
    return _hechos("no_se", estado)


def _resolver_servicio(
    conn: sqlite3.Connection, estado: Estado, entendido: dict[str, Any]
) -> dict[str, Any]:
    """Responde el precio de un servicio del catálogo."""
    servicio = buscar_servicio(conn, str(entendido.get("servicio_texto", "")), estado.idioma)
    if servicio is None:
        return _hechos("no_se", estado)
    estado.servicio_actual = int(servicio["id"])
    nombre = str(servicio["nombre_es"] if estado.idioma == "es" else servicio["nombre_en"])
    precio = formatear_precio(int(servicio["precio_centimos"]), estado.idioma)
    pregunta = "Quieres pedir cita?" if estado.idioma == "es" else "Shall I book you in?"
    return _hechos("precio", estado, {"producto": nombre, "precio": precio},
                   pregunta, [nombre, precio])


def _resolver_pedir_cita(
    conn: sqlite3.Connection, estado: Estado, entendido: dict[str, Any], ahora: datetime
) -> dict[str, Any]:
    """Ofrece un hueco de cita o el más cercano si no hay sitio."""
    servicio = buscar_servicio(conn, str(entendido.get("servicio_texto", "")), estado.idioma)
    if servicio is None and estado.servicio_actual:
        fila = conn.execute(
            "SELECT * FROM servicios WHERE id = ?", (estado.servicio_actual,)
        ).fetchone()
        servicio = _fila_a_dict(fila) if fila else None
    if servicio is None:
        pregunta = ("Para qué servicio quieres la cita?" if estado.idioma == "es"
                    else "Which service is the appointment for?")
        return _hechos("no_se", estado, {}, pregunta)
    estado.servicio_actual = int(servicio["id"])
    duracion = int(servicio["duracion_min"])
    vet = buscar_veterinario(conn, str(entendido.get("veterinario_texto", "")))
    if vet is None and estado.veterinario_actual:
        fila = conn.execute(
            "SELECT * FROM veterinarios WHERE id = ?", (estado.veterinario_actual,)
        ).fetchone()
        vet = _fila_a_dict(fila) if fila else None
    vet_id = int(vet["id"]) if vet else None
    if vet_id is not None:
        estado.veterinario_actual = vet_id
    hoy = ahora.astimezone(ZONA).date()
    fecha = _parse_fecha(str(entendido.get("fecha", "")))
    if fecha is not None and fecha < hoy:
        fecha = None  # Una fecha pasada no se ofrece: se busca desde hoy.
    if fecha is not None and not dia_abierto(conn, fecha):
        siguiente = siguiente_dia_abierto(conn, fecha)
        return _hechos(
            "cerrado", estado, {"dia": nombre_dia(siguiente, estado.idioma)},
            permitido=[nombre_dia(siguiente, estado.idioma)],
        )
    hora = str(entendido.get("hora", ""))
    franja = str(entendido.get("franja", ""))
    if fecha is not None:
        huecos = _filtrar_franja(
            _huecos_cita(conn, fecha, duracion, vet_id, servicio, ahora), franja)
        if huecos:
            return _guardar_propuesta_cita(
                conn, estado, servicio, _elegir_hueco(huecos, hora), False)
        dia = fecha + timedelta(days=1)
        for _ in range(DIAS_BUSQUEDA_CITA):
            siguientes = _filtrar_franja(
                _huecos_cita(conn, dia, duracion, vet_id, servicio, ahora), franja)
            if siguientes:
                return _guardar_propuesta_cita(
                    conn, estado, servicio, siguientes[0], True)
            dia += timedelta(days=1)
        return _hechos("no_se", estado)
    for i in range(DIAS_BUSQUEDA_CITA):
        dia = hoy + timedelta(days=i)
        huecos = _filtrar_franja(
            _huecos_cita(conn, dia, duracion, vet_id, servicio, ahora), franja)
        if huecos:
            return _guardar_propuesta_cita(
                conn, estado, servicio, _elegir_hueco(huecos, hora), False)
    return _hechos("no_se", estado)


def _huecos_cita(
    conn: sqlite3.Connection, dia: date, duracion: int, vet_id: int | None,
    servicio: dict[str, Any], ahora: datetime,
) -> list[Any]:
    """Calcula huecos según el servicio (peluquería va sin veterinario)."""
    if int(servicio["id"]) == 6 and vet_id is None:
        return huecos_negocio(conn, dia, duracion, ahora)
    return huecos_disponibles(conn, dia, duracion, vet_id, ahora)


def _filtrar_franja(huecos: list[Any], franja: str) -> list[Any]:
    """Filtra huecos por mañana (antes de las 13:00) o tarde."""
    if franja == "manana":
        return [h for h in huecos if h.inicio.hour < 13]
    if franja == "tarde":
        return [h for h in huecos if h.inicio.hour >= 13]
    return huecos


def _elegir_hueco(huecos: list[Any], hora: str) -> Any:
    """Elige el hueco más cercano a la hora pedida, o el primero."""
    if hora:
        pedidos = [h for h in huecos if h.inicio.strftime("%H:%M") == hora]
        if pedidos:
            return pedidos[0]
        try:
            objetivo = datetime.strptime(hora, "%H:%M").time()
        except ValueError:
            return huecos[0]
        return min(huecos, key=lambda h: abs(
            (h.inicio.hour * 60 + h.inicio.minute)
            - (objetivo.hour * 60 + objetivo.minute)))
    return huecos[0]


def _nombre_atencion(vet_id: int, conn: sqlite3.Connection, idioma: str) -> str:
    """Nombre de quien atiende: el veterinario o el equipo de peluquería."""
    if vet_id == 0:
        return "the grooming team" if idioma == "en" else "el equipo de peluquería"
    fila = conn.execute(
        "SELECT nombre FROM veterinarios WHERE id = ?", (vet_id,)).fetchone()
    return str(fila["nombre"]) if fila else ""


def _guardar_propuesta_cita(
    conn: sqlite3.Connection, estado: Estado, servicio: dict[str, Any],
    elegido: Any, lejano: bool,
) -> dict[str, Any]:
    """Guarda la propuesta pendiente y arma oferta o alternativa."""
    nombre_vet = _nombre_atencion(elegido.veterinario_id, conn, estado.idioma)
    nombre_serv = str(servicio["nombre_es"] if estado.idioma == "es"
                      else servicio["nombre_en"])
    estado.propuesta_pendiente = {
        "tipo": "cita",
        "veterinario_id": str(elegido.veterinario_id),
        "servicio_id": str(servicio["id"]),
        # Sin segundos: el mismo formato que la semilla, para comparar igual.
        "inicio": elegido.inicio.strftime("%Y-%m-%dT%H:%M"),
        "fin": elegido.fin.strftime("%Y-%m-%dT%H:%M"),
    }
    estado.fecha_actual = elegido.inicio.date().isoformat()
    estado.hora_actual = elegido.inicio.strftime("%H:%M")
    dia_txt = nombre_dia(elegido.inicio.date(), estado.idioma)
    hora_txt = elegido.inicio.strftime("%H:%M")
    datos = {"dia": dia_txt, "hora": hora_txt, "veterinario": nombre_vet,
             "servicio": nombre_serv}
    tipo = "sin_hueco" if lejano else "oferta_cita"
    return _hechos(tipo, estado, datos,
                   permitido=[dia_txt, hora_txt, nombre_vet, nombre_serv])


def _resolver_confirmar(
    conn: sqlite3.Connection, estado: Estado, ahora: datetime
) -> dict[str, Any]:
    """Confirma la propuesta pendiente: registra la cita o la compra."""
    propuesta = estado.propuesta_pendiente
    if not propuesta:
        return _hechos("no_se", estado)
    if propuesta.get("tipo") == "cita":
        return _confirmar_cita(conn, estado)
    if propuesta.get("tipo") == "compra":
        return _confirmar_compra(conn, estado, ahora)
    return _hechos("no_se", estado)


def _confirmar_cita(conn: sqlite3.Connection, estado: Estado) -> dict[str, Any]:
    """Guarda la cita si el hueco sigue libre."""
    propuesta = estado.propuesta_pendiente or {}
    # Formato sin segundos, igual que la semilla, para comparar bien.
    inicio_txt = datetime.fromisoformat(str(propuesta["inicio"])).strftime("%Y-%m-%dT%H:%M")
    fin_txt = datetime.fromisoformat(str(propuesta["fin"])).strftime("%Y-%m-%dT%H:%M")
    inicio = datetime.fromisoformat(inicio_txt)
    fin = datetime.fromisoformat(fin_txt)
    vet_id = int(str(propuesta["veterinario_id"]))
    if vet_id == 0:
        choque = conn.execute(
            "SELECT 1 FROM citas WHERE veterinario_id IS NULL"
            " AND inicio < ? AND fin > ?",
            (fin_txt, inicio_txt),
        ).fetchone()
    else:
        choque = conn.execute(
            "SELECT 1 FROM citas WHERE veterinario_id = ? AND inicio < ? AND fin > ?",
            (vet_id, fin_txt, inicio_txt),
        ).fetchone()
    if choque is not None:
        estado.propuesta_pendiente = None
        return _hechos("no_se", estado)
    with conn:
        conn.execute(
            "INSERT INTO citas (veterinario_id, servicio_id, inicio, fin,"
            " alias_cliente) VALUES (?, ?, ?, ?, ?)",
            (None if vet_id == 0 else vet_id, int(str(propuesta["servicio_id"])),
             inicio_txt, fin_txt, "Demo"),
        )
    estado.propuesta_pendiente = None
    nombre_vet = _nombre_atencion(vet_id, conn, estado.idioma)
    serv = _fila_a_dict(conn.execute(
        "SELECT * FROM servicios WHERE id = ?",
        (int(str(propuesta["servicio_id"])),)).fetchone())
    dia_txt = nombre_dia(inicio.date(), estado.idioma)
    hora_txt = inicio.strftime("%H:%M")
    nombre_serv = str(serv["nombre_es"] if estado.idioma == "es" else serv["nombre_en"])
    datos = {"dia": dia_txt, "hora": hora_txt,
             "veterinario": nombre_vet, "servicio": nombre_serv}
    return _hechos("cita_confirmada", estado, datos, permitido=list(datos.values()))


def _confirmar_compra(
    conn: sqlite3.Connection, estado: Estado, ahora: datetime
) -> dict[str, Any]:
    """Registra la venta, descuenta stock y confirma el total."""
    propuesta = estado.propuesta_pendiente or {}
    producto_id = int(str(propuesta["producto_id"]))
    cantidad = int(str(propuesta["cantidad"]))
    fila = conn.execute(
        "SELECT * FROM productos WHERE id = ?", (producto_id,)).fetchone()
    if fila is None:
        estado.propuesta_pendiente = None
        return _hechos("no_se", estado)
    producto = _fila_a_dict(fila)
    if int(producto["stock"]) < cantidad:
        estado.propuesta_pendiente = None
        nombre = _nombre_producto(producto, estado.idioma)
        precio = formatear_precio(int(producto["precio_centimos"]), estado.idioma)
        return _hechos_stock(conn, estado, producto, nombre, precio,
                             int(producto["stock"]), estado.idioma)
    total = int(producto["precio_centimos"]) * cantidad
    with conn:
        conn.execute(
            "UPDATE productos SET stock = stock - ? WHERE id = ?",
            (cantidad, producto_id),
        )
        conn.execute(
            "INSERT INTO ventas (producto_id, cantidad, total_centimos, creado)"
            " VALUES (?, ?, ?, ?)",
            (producto_id, cantidad, total,
             ahora.astimezone(ZONA).replace(tzinfo=None).isoformat()),
        )
    estado.propuesta_pendiente = None
    nombre = _nombre_producto(producto, estado.idioma)
    total_txt = formatear_precio(total, estado.idioma)
    datos = {"producto": nombre, "cantidad": cantidad, "total": total_txt}
    return _hechos("compra_confirmada", estado, datos,
                   permitido=[nombre, total_txt, str(cantidad)])


def _parse_fecha(texto: str) -> date | None:
    """Interpreta una fecha ISO; devuelve None si no es válida o es vacía."""
    if not texto.strip():
        return None
    try:
        return date.fromisoformat(texto.strip())
    except ValueError:
        return None
