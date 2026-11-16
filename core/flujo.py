"""Orquesta la tubería entender, reglas, redactar y validar.

Qué hace: aplica privacidad, topes, respuestas fijas sin IA y el
reintento con respaldo de plantillas. Recibe: conexión, estado,
textos, mensaje y proveedor opcional. Devuelve: el resultado con el
texto para el cliente. Qué NO hace: no dibuja nada en pantalla (eso es
ui/) ni guarda secretos.
"""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from core.entender import entender
from core.estado import Estado, registrar_turno
from core.limites import (
    LIMITE_SESION_POR_DEFECTO,
    mensajes_restantes,
    recortar_mensaje,
    sesion_bloqueada,
)
from core.plantillas import respaldo
from core.privacidad import contiene_datos_personales, ocultar_datos_personales
from core.proveedor_ia import ErrorProveedor, ProveedorIA
from core.redactar import redactar
from core.reglas import resolver
from core.validador import validar

_registro = logging.getLogger(__name__)

# Respuestas que salen fijas sin pasar por la IA (ver 05, reglas 10 a 12).
SIN_IA = ("aviso_ia", "derivar")


@dataclass
class Resultado:
    """Lo que devuelve un turno del flujo."""

    texto: str
    tipo: str
    con_ia: bool
    recortado: bool
    tope: bool


def responder(
    conn: sqlite3.Connection,
    estado: Estado,
    textos: dict[str, Any],
    mensaje: str,
    ahora: datetime,
    proveedor: ProveedorIA | None = None,
    cupo_diario: bool = True,
    limite_sesion: int = LIMITE_SESION_POR_DEFECTO,
) -> Resultado:
    """Procesa un mensaje de principio a fin.

    Parámetros:
        conn: conexión SQLite de la sesión.
        estado: memoria de la conversación (se actualiza).
        textos: diccionario i18n del idioma activo.
        mensaje: texto del usuario.
        ahora: instante actual.
        proveedor: IA o None para modo sin IA.
        cupo_diario: falso cuando se acabó el cupo del día.
        limite_sesion: tope de mensajes por sesión.
    Devuelve: resultado con el texto y cómo se generó.
    Ejemplo:
        >>> from core.esquema import iniciar_bd
        >>> from datetime import date, datetime
        >>> from zoneinfo import ZoneInfo
        >>> conn = iniciar_bd(date(2026, 11, 16))
        >>> r = responder(conn, Estado(), {"no_entendido": ["Cómo no?"],
        ...     "frases_prohibidas": []}, "hola",
        ...     datetime(2026, 11, 16, 8, 0, tzinfo=ZoneInfo("Europe/Madrid")))
        >>> r.tipo
        'no_se'
    """
    if sesion_bloqueada(estado.n_mensajes, limite_sesion):
        texto, _ = _respaldo_directo("tope", estado, textos)
        return Resultado(texto, "tope", False, False, True)
    mensaje, recortado = recortar_mensaje(mensaje)
    if contiene_datos_personales(mensaje):
        texto, _ = _respaldo_directo("datos_personales", estado, textos)
        mensaje_limpio, _ = ocultar_datos_personales(mensaje)
        registrar_turno(estado, mensaje_limpio, texto)
        return Resultado(texto, "datos_personales", False, recortado, False)
    historial = list(estado.historial)
    if proveedor is None or not cupo_diario:
        entendido: dict[str, Any] = {
            "intencion": "no_entendido", "idioma": estado.idioma,
            "trato": "desconocido",
        }
    else:
        try:
            entendido = entender(proveedor, mensaje, historial, ahora)
        except ErrorProveedor as error:
            # Se registra solo el motivo técnico (por ejemplo "HTTP Error 401"),
            # nunca el texto del usuario ni la clave, para poder diagnosticar
            # en los registros de Streamlit Cloud por qué la IA no respondió.
            _registro.warning("Fallo al entender con la IA: %s", error)
            entendido = {"intencion": "no_entendido", "idioma": estado.idioma,
                         "trato": "desconocido"}
    hechos = resolver(conn, estado, entendido, ahora)
    tipo = str(hechos.get("tipo_respuesta", "no_se"))
    arranque = historial[-1]["bot"] if historial else ""
    if tipo in SIN_IA or proveedor is None or not cupo_diario:
        texto, _ = respaldo(hechos, textos, evitar_arranque=arranque)
        registrar_turno(estado, mensaje, texto)
        return Resultado(texto, tipo, False, recortado, False)
    negocio = conn.execute("SELECT nombre, nombre_bot FROM negocio").fetchone()
    try:
        candidato = redactar(proveedor, hechos, str(negocio["nombre_bot"]),
                             str(negocio["nombre"]), arranque)
        motivos = validar(candidato, hechos, arranque, textos["frases_prohibidas"])
        if motivos:
            candidato = redactar(proveedor, hechos, str(negocio["nombre_bot"]),
                                 str(negocio["nombre"]), arranque,
                                 correccion="; ".join(motivos))
            motivos = validar(candidato, hechos, arranque,
                              textos["frases_prohibidas"])
        if motivos:
            raise ErrorProveedor("redacción inválida dos veces")
    except ErrorProveedor as error:
        _registro.warning("Fallo al redactar con la IA: %s", error)
        candidato, _ = respaldo(hechos, textos, evitar_arranque=arranque)
        registrar_turno(estado, mensaje, candidato)
        return Resultado(candidato, tipo, False, recortado, False)
    registrar_turno(estado, mensaje, candidato)
    return Resultado(candidato, tipo, True, recortado, False)


def _respaldo_directo(
    tipo: str, estado: Estado, textos: dict[str, Any]
) -> tuple[str, int]:
    """Respuesta fija sin IA para topes y datos personales."""
    hechos = {"tipo_respuesta": tipo, "idioma": estado.idioma, "datos": {},
              "permitido_mencionar": []}
    return respaldo(hechos, textos)


def restantes(estado: Estado, limite: int = LIMITE_SESION_POR_DEFECTO) -> int:
    """Mensajes que le quedan a la sesión (para la barra de la interfaz)."""
    return mensajes_restantes(estado.n_mensajes, limite)
