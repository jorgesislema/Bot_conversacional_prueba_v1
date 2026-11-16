"""Pruebas de la conversación tipo vendedor (fallos vistos en producción).

Conversación real del 2026-11-16:
    "buenas tardes tiene comida para cachoros" -> respondió "Tenemos 40 en
    stock" (eran las latas de gato). "que marca" -> "no tengo información".
Estas pruebas fijan el comportamiento correcto: lista con nombre, marca y
precio; marca del producto o de la lista; y nunca solo un número de stock.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from core.esquema import iniciar_bd
from core.estado import crear_estado
from core.plantillas import cargar_textos, respaldo
from core.reglas import interpretar_categoria, productos_de_categoria, resolver
from core.validador import validar
from ui.panel import euros_a_centimos

LUNES = date(2026, 11, 16)
AHORA = datetime(2026, 11, 16, 16, 0, tzinfo=ZoneInfo("Europe/Madrid"))


def _entendido(intencion: str, producto: str = "", idioma: str = "es") -> dict[str, object]:
    """JSON de entender con valores por defecto."""
    return {"intencion": intencion, "idioma": idioma, "trato": "tu",
            "producto_texto": producto, "referencia": "ninguna"}


@pytest.mark.parametrize(
    ("texto", "categoria", "especie"),
    [
        ("comida para cachoros", "alimentación", "cachorro"),
        ("comida para perros", "alimentación", "perro"),
        ("tiene comida para gato", "alimentación", "gato"),
        ("juguetes para gatos", "juguetes", "gato"),
        ("dog food", "alimentación", "perro"),
    ],
)
def test_interpretar_categoria_amplia(texto: str, categoria: str, especie: str) -> None:
    """Detecta categoría y especie aunque haya faltas y plurales."""
    assert interpretar_categoria(texto) == (categoria, especie, [])


def test_pregunta_concreta_no_es_amplia() -> None:
    """Si dice más que la categoría, no se fuerza una lista."""
    _, _, sobrantes = interpretar_categoria("pienso perro adulto 15 kg")
    assert sobrantes


def test_cachorros_da_el_pienso_de_cachorro_con_precio_y_marca() -> None:
    """Fallo real: devolvía las latas de gato y solo el stock."""
    conn = iniciar_bd(LUNES)
    hechos = resolver(conn, crear_estado(),
                      _entendido("disponibilidad", "comida para cachoros"), AHORA)
    datos = hechos["datos"]
    assert hechos["tipo_respuesta"] == "stock"
    assert datos["producto"] == "Pienso cachorro 3 kg"
    assert datos["precio"] == "15,90 EUR"
    assert datos["marca"] == "Campo Verde"
    texto, _ = respaldo(hechos, cargar_textos("es"))
    assert "Pienso cachorro 3 kg" in texto and "15,90 EUR" in texto
    assert "25" not in texto  # El stock alto no se dice.


def test_comida_para_perros_da_lista_y_luego_la_marca() -> None:
    """Pregunta amplia: lista; "que marca" después: lista con marcas."""
    conn = iniciar_bd(LUNES)
    estado = crear_estado()
    hechos = resolver(conn, estado, _entendido("disponibilidad", "comida para perros"), AHORA)
    assert hechos["tipo_respuesta"] == "lista_productos"
    lista = hechos["datos"]["lista"]
    assert "Pienso perro adulto 3 kg" in lista and "14,50 EUR" in lista
    assert "Pienso cachorro 3 kg" in lista
    assert "gato" not in lista.lower()
    texto, _ = respaldo(hechos, cargar_textos("es"))
    assert validar(texto, hechos, "", []) == []
    marca = resolver(conn, estado, _entendido("descripcion_producto", ""), AHORA)
    assert marca["tipo_respuesta"] == "lista_productos"
    assert "Campo Verde" in marca["datos"]["lista"]


def test_que_marca_de_un_producto_concreto() -> None:
    """Tras hablar del champú, "que marca" responde PelBrillo con precio."""
    conn = iniciar_bd(LUNES)
    estado = crear_estado()
    resolver(conn, estado, _entendido("disponibilidad", "champu"), AHORA)
    hechos = resolver(conn, estado, _entendido("descripcion_producto", ""), AHORA)
    assert hechos["datos"]["marca"] == "PelBrillo"
    texto, _ = respaldo(hechos, cargar_textos("es"))
    assert "PelBrillo" in texto and "9,90 EUR" in texto


def test_champu_responde_nombre_y_precio_no_solo_stock() -> None:
    """Fallo real: "16 unidades de champú" sin precio."""
    conn = iniciar_bd(LUNES)
    hechos = resolver(conn, crear_estado(), _entendido("disponibilidad", "champu"), AHORA)
    for i in range(3):
        texto = cargar_textos("es")["stock_hay"][i].format(**hechos["datos"])
        assert "9,90 EUR" in texto and "16" not in texto


def test_lista_en_ingles() -> None:
    """La lista sale en inglés con punto decimal."""
    conn = iniciar_bd(LUNES)
    estado = crear_estado(idioma="en")
    hechos = resolver(conn, estado, _entendido("disponibilidad", "cat food", "en"), AHORA)
    assert hechos["tipo_respuesta"] == "lista_productos"
    assert "11.90 EUR" in hechos["datos"]["lista"]


def test_agotado_sin_alternativa_no_rompe_la_plantilla() -> None:
    """Stock 0 sin alternativa usa stock_cero (antes podía fallar)."""
    hechos = {"tipo_respuesta": "stock", "idioma": "es",
              "datos": {"producto": "X", "stock": 0}, "permitido_mencionar": []}
    texto, _ = respaldo(hechos, cargar_textos("es"))
    assert "X" in texto


def test_producto_nuevo_aparece_en_su_categoria() -> None:
    """Un producto añadido en el panel entra en la lista de su categoría."""
    from ui.acciones import anadir_producto

    conn = iniciar_bd(LUNES)
    anadir_producto(conn, "Ratón de juguete para gato", "juguetes", "3,50", 10)
    nombres = [p["nombre_es"] for p in productos_de_categoria(conn, "juguetes", "gato", "es")]
    assert "Ratón de juguete para gato" in nombres


@pytest.mark.parametrize(
    ("texto", "centimos"),
    [("12,5", 1250), ("12.50", 1250), ("12,50 €", 1250), ("12 EUR", 1200),
     ("1.234,50", 123450), (" 0,99 ", 99)],
)
def test_precio_acepta_decimales_en_varias_formas(texto: str, centimos: int) -> None:
    """El panel acepta coma, punto, símbolo de euro y punto de miles."""
    assert euros_a_centimos(texto) == centimos


@pytest.mark.parametrize("texto", ["", "abc", "-1", "nan"])
def test_precio_invalido(texto: str) -> None:
    """Texto, negativo o vacío: error traducible."""
    with pytest.raises(ValueError, match="error_precio"):
        euros_a_centimos(texto)
