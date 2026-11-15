"""Topes de gasto y de mensajes de la demo (docs/05, sección 10).

Qué hace: recorta mensajes largos, dice cuándo la sesión llega al tope
y cuenta los mensajes del día con un candado. Recibe: contadores y
textos. Devuelve: decisiones de bloqueo y textos recortados. Qué NO
hace: no toca Streamlit; la interfaz guarda el contador en caché.
"""

from __future__ import annotations

import threading

LIMITE_SESION_POR_DEFECTO = 40
LIMITE_DIARIO_POR_DEFECTO = 1500
LONGITUD_MAXIMA_MENSAJE = 500


def recortar_mensaje(texto: str, maximo: int = LONGITUD_MAXIMA_MENSAJE) -> tuple[str, bool]:
    """Recorta un mensaje demasiado largo al máximo permitido.

    Parámetros:
        texto: mensaje del usuario.
        maximo: longitud máxima en caracteres.
    Devuelve: tupla con el texto recortado y si hubo recorte.
    Ejemplo:
        >>> recortar_mensaje("hola", 2)
        ('ho', True)
    """
    if len(texto) <= maximo:
        return texto, False
    return texto[:maximo], True


def sesion_bloqueada(n_mensajes: int, limite: int = LIMITE_SESION_POR_DEFECTO) -> bool:
    """Indica si la sesión alcanzó el tope de mensajes.

    Parámetros:
        n_mensajes: mensajes enviados en la sesión.
        limite: tope configurado.
    Devuelve: verdadero cuando ya no se aceptan mensajes.
    Ejemplo:
        >>> sesion_bloqueada(40)
        True
    """
    return n_mensajes >= limite


def mensajes_restantes(n_mensajes: int, limite: int = LIMITE_SESION_POR_DEFECTO) -> int:
    """Calcula los mensajes que le quedan a la sesión.

    Parámetros:
        n_mensajes: mensajes enviados en la sesión.
        limite: tope configurado.
    Devuelve: número mayor o igual a cero.
    Ejemplo:
        >>> mensajes_restantes(38)
        2
    """
    return max(0, limite - n_mensajes)


class ContadorDiario:
    """Cuenta los mensajes del día de todas las sesiones juntas.

    Por qué un candado: varias sesiones escriben a la vez y el contador
    debe ser exacto para no superar el tope diario de gasto.
    """

    def __init__(self, limite: int = LIMITE_DIARIO_POR_DEFECTO) -> None:
        """Crea el contador con el tope diario configurado."""
        self._limite = limite
        self._total = 0
        self._candado = threading.Lock()

    def registrar(self) -> bool:
        """Suma un mensaje si queda cupo diario.

        Devuelve: verdadero si había cupo y se contó.
        Ejemplo:
            >>> ContadorDiario(1).registrar()
            True
        """
        with self._candado:
            if self._total >= self._limite:
                return False
            self._total += 1
            return True

    def hay_cupo(self) -> bool:
        """Indica si queda cupo diario sin contar nada."""
        with self._candado:
            return self._total < self._limite
