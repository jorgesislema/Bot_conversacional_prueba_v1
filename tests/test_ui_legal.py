"""Prueba del aviso legal del pie (fase 4)."""

from ui.legal import texto_pie, texto_privacidad


def test_pie_con_titular_y_correo() -> None:
    """El pie muestra al titular y su contacto."""
    textos = {"pie_titular": "Titular: {titular}. Contacto: {correo_titular}."}
    assert texto_pie(textos, "Clínica X", "x@y.z") == "Titular: Clínica X. Contacto: x@y.z."


def test_privacidad_corto() -> None:
    """Existe un texto corto de privacidad."""
    assert texto_privacidad({"texto_privacidad": "Aviso"}) == "Aviso"
