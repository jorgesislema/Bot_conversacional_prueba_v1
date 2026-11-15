"""Respuestas seguras sin IA (docs/05, sección 7).

Qué hace: elige una variante distinta de la última usada y rellena
los huecos con datos de los hechos. Recibe: tipo de respuesta, idioma,
datos y textos i18n. Devuelve: texto y el índice usado. Qué NO hace:
no inventa datos; si falta un tipo, usa la plantilla de no_entendido.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parents[1]


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
) -> tuple[str, int]:
    """Rellena una plantilla con los datos de los hechos.

    Parámetros:
        tipo: tipo de respuesta de docs/05, sección 3.
        idioma: "es" o "en".
        datos: valores exactos que salen de la base de datos.
        textos: diccionario i18n ya cargado (se carga si falta).
        evitar_indice: variante que no se debe repetir.
        rng: generador para elegir variante (por defecto, azar).
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
    candidatos = [i for i in range(len(opciones)) if i != evitar_indice]
    elegido = (rng or random).choice(candidatos) if candidatos else 0
    return opciones[elegido].format(**datos), elegido
