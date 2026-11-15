"""Pruebas de privacidad y de límites (fase 2)."""

from core.limites import (
    ContadorDiario,
    mensajes_restantes,
    recortar_mensaje,
    sesion_bloqueada,
)
from core.privacidad import contiene_datos_personales, ocultar_datos_personales


def test_detecta_telefono_espanol() -> None:
    """Detecta un móvil español de 9 dígitos."""
    assert contiene_datos_personales("llámame al 612345678")


def test_detecta_telefono_con_espacios() -> None:
    """Detecta un fijo con espacios como el 900 000 000."""
    assert contiene_datos_personales("llama al 900 000 000")


def test_detecta_telefono_internacional() -> None:
    """Detecta un teléfono con prefijo internacional."""
    assert contiene_datos_personales("mi número es +34 612 345 678")


def test_detecta_correo() -> None:
    """Detecta una dirección de correo."""
    assert contiene_datos_personales("escríbeme a ana@test.es")


def test_detecta_dni_valido() -> None:
    """Detecta un DNI con letra de control correcta."""
    assert contiene_datos_personales("mi DNI es 12345678Z")


def test_ignora_dni_con_letra_falsa() -> None:
    """No bloquea 8 dígitos con una letra de control incorrecta."""
    assert not contiene_datos_personales("mi DNI es 12345678A")


def test_detecta_nie_valido() -> None:
    """Detecta un NIE con letra de control correcta."""
    assert contiene_datos_personales("mi NIE es X1234567L")


def test_detecta_iban() -> None:
    """Detecta un IBAN español."""
    assert contiene_datos_personales("mi IBAN es ES9121000418450200051332")


def test_detecta_tarjeta_valida() -> None:
    """Detecta una tarjeta que pasa el control de Luhn."""
    assert contiene_datos_personales("mi tarjeta es 4111111111111111")


def test_ignora_digitos_sin_sentido() -> None:
    """No confunde el peso del pienso con datos personales."""
    assert not contiene_datos_personales("cuánto cuesta el pienso de 15 kg")


def test_ocultar_enmascara_y_avisa() -> None:
    """Oculta el dato y dice que encontró algo."""
    texto, encontrado = ocultar_datos_personales("llama al 612345678 por favor")
    assert encontrado
    assert "612345678" not in texto


def test_sesion_bloqueada_al_llegar_al_tope() -> None:
    """La sesión se bloquea justo al alcanzar el límite."""
    assert not sesion_bloqueada(39)
    assert sesion_bloqueada(40)


def test_recorta_mensaje_largo() -> None:
    """Recorta a 500 caracteres e indica que hubo recorte."""
    texto, recortado = recortar_mensaje("x" * 600)
    assert recortado
    assert len(texto) == 500


def test_mensajes_restantes() -> None:
    """Calcula los mensajes que quedan sin bajar de cero."""
    assert mensajes_restantes(38) == 2
    assert mensajes_restantes(99) == 0


def test_contador_diario_respeta_el_tope() -> None:
    """El contador diario deja de contar al llegar al límite."""
    contador = ContadorDiario(2)
    assert contador.registrar()
    assert contador.registrar()
    assert not contador.registrar()
    assert not contador.hay_cupo()
