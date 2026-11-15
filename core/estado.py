"""Memoria de la conversación (docs/05, sección 1).

Qué hace: guarda idioma, trato, producto y cita en curso, candidatos
de la última aclaración e historial corto. Recibe: eventos de la
conversación. Devuelve: el estado actualizado. Qué NO hace: no consulta
la IA ni la base de datos, solo recuerda.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Estado:
    """Memoria de una sesión de chat."""

    idioma: str = "es"
    trato: str = "tu"
    producto_actual: int = 0
    servicio_actual: int = 0
    veterinario_actual: int = 0
    fecha_actual: str = ""
    hora_actual: str = ""
    candidatos: list[int] = field(default_factory=list)
    propuesta_pendiente: dict[str, str] | None = None
    historial: list[dict[str, str]] = field(default_factory=list)
    n_mensajes: int = 0
    aviso_ia_mostrado: bool = False


def crear_estado(idioma: str = "es", trato: str = "tu") -> Estado:
    """Crea el estado inicial de una sesión.

    Parámetros:
        idioma: idioma por defecto del negocio.
        trato: trato por defecto del negocio.
    Devuelve: estado vacío con esos valores.
    Ejemplo:
        >>> crear_estado().idioma
        'es'
    """
    return Estado(idioma=idioma, trato=trato)


def fijar_trato_inicial(estado: Estado, trato: str) -> None:
    """Fija tú o usted con el primer mensaje y ya no cambia.

    Por qué solo el primero: mezclar tratos en la misma charla suena
    robótico (ver 02, principio 5).
    """
    if estado.n_mensajes == 0 and trato in ("tu", "usted"):
        estado.trato = trato


def registrar_turno(estado: Estado, usuario: str, bot: str) -> None:
    """Guarda un turno en el historial, que conserva los últimos 6."""
    estado.historial.append({"usuario": usuario, "bot": bot})
    estado.historial = estado.historial[-6:]
    estado.n_mensajes += 1


def guardar_candidatos(estado: Estado, candidatos: list[int]) -> None:
    """Guarda los ids ofrecidos para resolver "el grande" o "ese"."""
    estado.candidatos = candidatos


def limpiar_tema(estado: Estado) -> None:
    """Borra el tema actual cuando el usuario cambia de asunto."""
    estado.producto_actual = 0
    estado.servicio_actual = 0
    estado.veterinario_actual = 0
    estado.fecha_actual = ""
    estado.hora_actual = ""
    estado.candidatos = []
    estado.propuesta_pendiente = None
