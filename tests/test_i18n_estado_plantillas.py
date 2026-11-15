"""Pruebas de i18n, estado y plantillas (fase 2)."""

import json
import random
from pathlib import Path

from core.estado import (
    crear_estado,
    fijar_trato_inicial,
    guardar_candidatos,
    limpiar_tema,
    registrar_turno,
)
from core.plantillas import cargar_textos, renderizar

RAIZ = Path(__file__).resolve().parents[1]


def _cargar(idioma: str) -> dict:
    with open(RAIZ / "i18n" / f"{idioma}.json", encoding="utf-8") as f:
        return json.load(f)


def test_mismas_claves_en_ambos_idiomas() -> None:
    """Los archivos es.json y en.json tienen exactamente las mismas claves."""
    assert set(_cargar("es").keys()) == set(_cargar("en").keys())


def test_sin_emojis_en_textos() -> None:
    """Ningún texto contiene emojis (regla de AGENTS.md)."""
    for idioma in ("es", "en"):
        contenido = json.dumps(_cargar(idioma), ensure_ascii=False)
        for letra in contenido:
            assert not (0x1F300 <= ord(letra) <= 0x1FAFF), f"Emoji en {idioma}"


def test_aviso_menciona_ia_en_ambos_idiomas() -> None:
    """El primer mensaje nombra la inteligencia artificial."""
    assert "inteligencia artificial" in _cargar("es")["aviso_ia_inicio"]
    texto_en = _cargar("en")["aviso_ia_inicio"].lower()
    assert "artificial intelligence" in texto_en


def test_trato_se_fija_solo_con_el_primer_mensaje() -> None:
    """El trato se fija con el primer mensaje y luego no cambia."""
    estado = crear_estado()
    fijar_trato_inicial(estado, "usted")
    registrar_turno(estado, "hola", "hola")
    fijar_trato_inicial(estado, "tu")
    assert estado.trato == "usted"


def test_historial_conserva_los_ultimos_6() -> None:
    """El historial nunca guarda más de 6 turnos."""
    estado = crear_estado()
    for i in range(9):
        registrar_turno(estado, f"u{i}", f"b{i}")
    assert len(estado.historial) == 6
    assert estado.n_mensajes == 9


def test_limpiar_tema_borra_candidatos_y_propuesta() -> None:
    """Cambiar de tema olvida el producto y la propuesta pendiente."""
    estado = crear_estado()
    estado.producto_actual = 2
    guardar_candidatos(estado, [1, 2])
    estado.propuesta_pendiente = {"tipo": "cita"}
    limpiar_tema(estado)
    assert estado.producto_actual == 0
    assert estado.candidatos == []
    assert estado.propuesta_pendiente is None


def test_variantes_no_repiten_la_ultima() -> None:
    """La plantilla elegida es distinta de la última usada."""
    textos = cargar_textos("es")
    for _ in range(20):
        _, indice = renderizar("precio", "es", {"producto": "X", "precio": "1,00 EUR"},
                               textos, evitar_indice=1)
        assert indice != 1


def test_variantes_difieren_entre_si() -> None:
    """Cada tipo con variantes trae textos distintos."""
    textos = cargar_textos("es")
    rng = random.Random(1)
    vistos = {renderizar("precio", "es", {"producto": "X", "precio": "1 EUR"},
                         textos, rng=rng)[0] for _ in range(30)}
    assert len(vistos) >= 2


def test_tipo_desconocido_usa_respaldo() -> None:
    """Un tipo inexistente cae en la plantilla de no_entendido."""
    texto, _ = renderizar("tipo_que_no_existe", "es", {})
    assert "entendido" in texto
