"""Respuestas seguras sin IA (docs/05, sección 7).

Qué hace: elige una variante distinta de la última usada y rellena
los huecos con datos de los hechos. Recibe: tipo de respuesta, idioma,
datos y textos i18n. Devuelve: texto y el índice usado. Qué NO hace:
no inventa datos; si falta un tipo, usa la plantilla de no_entendido.
"""

from __future__ import annotations

import json
import random
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

ZONA = ZoneInfo("Europe/Madrid")
RAIZ = Path(__file__).resolve().parents[1]
_PATRON_PALABRA = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+")


def _primera_palabra(texto: str) -> str:
    """Devuelve la primera palabra en minúsculas o vacío."""
    hallados = _PATRON_PALABRA.findall(texto)
    return hallados[0].lower() if hallados else ""


def cargar_textos(idioma: str) -> dict[str, Any]:
    """Carga el archivo i18n del idioma pedido.

    Parámetros:
        idioma: "es" o "en"; cualquier otro usa español.
    Devuelve: diccionario con las claves de texto.
    Ejemplo:
        >>> cargar_textos("es")["etiqueta_ia"]
        'Asistente con IA'
    """
    if idioma not in ("es", "en"):
        idioma = "es"
    ruta = RAIZ / "i18n" / f"{idioma}.json"
    with open(ruta, encoding="utf-8") as f:
        datos: dict[str, Any] = json.load(f)
    return datos


def variantes(tipo: str, textos: dict[str, Any]) -> list[str]:
    """Devuelve las variantes de un tipo de respuesta.

    Si el tipo no existe, devuelve las de no_entendido como respaldo.
    """
    valor = textos.get(tipo, textos["no_entendido"])
    if isinstance(valor, list):
        return [str(v) for v in valor]
    return [str(valor)]


def renderizar(
    tipo: str,
    idioma: str,
    datos: dict[str, Any],
    textos: dict[str, Any] | None = None,
    evitar_indice: int = -1,
    rng: random.Random | None = None,
    evitar_arranque: str = "",
) -> tuple[str, int]:
    """Rellena una plantilla con los datos de los hechos.

    Parámetros:
        tipo: tipo de respuesta de docs/05, sección 3.
        idioma: "es" o "en".
        datos: valores exactos que salen de la base de datos.
        textos: diccionario i18n ya cargado (se carga si falta).
        evitar_indice: variante que no se debe repetir.
        rng: generador para elegir variante (por defecto, azar).
        evitar_arranque: primera palabra que no debe repetirse.
    Devuelve: tupla con el texto y el índice de variante usado.
    Errores:
        KeyError si un hueco de la plantilla no está en datos.
    Ejemplo:
        >>> texto, i = renderizar("precio", "es", {"producto": "Pienso", "precio": "10,00 EUR"})
        >>> "10,00 EUR" in texto
        True
    """
    if textos is None:
        textos = cargar_textos(idioma)
    opciones = variantes(tipo, textos)
    primera = _primera_palabra(evitar_arranque)
    if primera:
        distintas = [v for v in opciones if _primera_palabra(v) != primera]
        if distintas:
            opciones = distintas
    candidatos = [i for i in range(len(opciones)) if i != evitar_indice]
    elegido = (rng or random).choice(candidatos) if candidatos else 0
    return opciones[elegido].format(**datos), elegido


_MAPA_TIPOS = {
    "aclaracion_producto": "aclaracion",
    "aviso_ia": "es_ia",
    "no_se": "no_entendido",
}


def saludo_segun_hora(ahora: datetime, textos: dict[str, Any]) -> str:
    """Elige buenos días, buenas tardes o buenas noches en Madrid.

    Por qué Madrid: la demo opera en zona Europe/Madrid (ver 03.3).
    """
    hora = ahora.astimezone(ZONA).hour
    if hora < 13:
        return str(textos["saludo_manana"])
    if hora < 21:
        return str(textos["saludo_tarde"])
    return str(textos["saludo_noche"])


def aviso_inicial(
    textos: dict[str, Any], idioma: str, trato: str,
    negocio: str, nombre_bot: str, ahora: datetime,
) -> str:
    """Compone el primer mensaje con el aviso de IA (ver 01, 4.1).

    El aviso es obligatorio y siempre el primero; después el bot ayuda
    sin repetirlo.
    """
    clave = "aviso_ia_inicio" if trato == "tu" else "aviso_ia_inicio_usted"
    return str(textos[clave]).format(
        saludo=saludo_segun_hora(ahora, textos),
        negocio=negocio, nombre_bot=nombre_bot,
    )


def respaldo(
    hechos: dict[str, Any],
    textos: dict[str, Any] | None = None,
    evitar_indice: int = -1,
    rng: random.Random | None = None,
    evitar_arranque: str = "",
) -> tuple[str, int]:
    """Genera la respuesta segura de respaldo para unos hechos.

    Por qué existe: si la IA falla o el validador rechaza dos veces, la
    demo nunca se cae y el dato sigue saliendo de la base (ver 02.3).
    El stock sin existencias combina el aviso con la alternativa.

    Parámetros:
        hechos: diccionario con tipo_respuesta, idioma y datos.
        textos: diccionario i18n ya cargado (se carga si falta).
        evitar_indice: variante que no se debe repetir.
        rng: generador para elegir variante.
        evitar_arranque: primera palabra que no debe repetirse.
    Devuelve: tupla con el texto y el índice de variante usado.
    Ejemplo:
        >>> texto, _ = respaldo({"tipo_respuesta": "saludo", "idioma": "es",
        ...     "datos": {}, "permitido_mencionar": []})
        >>> isinstance(texto, str)
        True
    """
    tipo = str(hechos.get("tipo_respuesta", "no_se"))
    idioma = str(hechos.get("idioma", "es"))
    datos = dict(hechos.get("datos", {}))
    if textos is None:
        textos = cargar_textos(idioma)
    if tipo == "derivar":
        primera, _ = renderizar("derivar_persona", idioma, datos, textos,
                                evitar_indice, rng, evitar_arranque)
        segunda, _ = renderizar("derivar_demo", idioma, {}, textos,
                                evitar_indice, rng)
        return f"{primera} {segunda}", 0
    if tipo == "stock":
        if datos.get("stock", 1) == 0 and "alternativa" in datos:
            primera, _ = renderizar("stock_cero", idioma, datos, textos,
                                    evitar_indice, rng, evitar_arranque)
            segunda, indice = renderizar("alternativa", idioma, datos, textos,
                                         evitar_indice, rng)
            return f"{primera} {segunda}", indice
        clave = "stock_pocas" if int(datos.get("stock", 99)) <= 3 else "stock_hay"
        return renderizar(clave, idioma, datos, textos, evitar_indice, rng,
                          evitar_arranque)
    return renderizar(_MAPA_TIPOS.get(tipo, tipo), idioma, datos, textos,
                      evitar_indice, rng, evitar_arranque)
