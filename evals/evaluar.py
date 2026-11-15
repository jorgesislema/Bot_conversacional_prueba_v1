"""Evalúa las 60 conversaciones de referencia (docs/02, sección 7).

Qué hace: ejecuta cada caso con datos simulados de entender, aplica
cambios en caliente y mide exactitud, aviso, derivación, frases y
arranques. Recibe: nada (lee los JSON). Devuelve: código 0 si aprueba.
Qué NO hace: no llama a la IA real; la eval con proveedor real queda
pendiente de las claves (ver DECISIONES.md).

Uso: python evals/evaluar.py
"""

from __future__ import annotations

import json
import random
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from zoneinfo import ZoneInfo  # noqa: E402

from core.esquema import iniciar_bd  # noqa: E402
from core.estado import Estado, crear_estado  # noqa: E402
from core.plantillas import aviso_inicial, cargar_textos, respaldo  # noqa: E402
from core.privacidad import contiene_datos_personales  # noqa: E402
from core.reglas import resolver  # noqa: E402
from core.validador import validar  # noqa: E402

ZONA = ZoneInfo("Europe/Madrid")
HOY = datetime(2026, 11, 16, 8, 0, tzinfo=ZONA).date()
AHORA = datetime(2026, 11, 16, 8, 0, tzinfo=ZONA)

CLAVES_ENTENDIDO = (
    "intencion", "idioma", "trato", "producto_texto", "servicio_texto",
    "veterinario_texto", "fecha", "hora", "franja", "cantidad", "referencia",
)


def _completar_entendido(parcial: dict, idioma: str) -> dict:
    """Rellena las claves que el caso no especifica."""
    base = {
        "intencion": "no_entendido", "idioma": idioma, "trato": "tu",
        "producto_texto": "", "servicio_texto": "", "veterinario_texto": "",
        "fecha": "", "hora": "", "franja": "", "cantidad": 0,
        "referencia": "ninguna",
    }
    for clave in CLAVES_ENTENDIDO:
        if clave in parcial:
            base[clave] = parcial[clave]
    return base


def _aplicar_cambio(conn: sqlite3.Connection, cambio: dict) -> None:
    """Aplica un cambio en caliente del panel sobre la sesión."""
    if cambio["accion"] == "update":
        columnas = ", ".join(f"{c} = ?" for c in cambio["valores"])
        cond = " AND ".join(f"{c} = ?" for c in cambio["filtro"])
        with conn:
            conn.execute(
                f"UPDATE {cambio['tabla']} SET {columnas} WHERE {cond}",
                list(cambio["valores"].values()) + list(cambio["filtro"].values()),
            )
    elif cambio["accion"] == "insert":
        columnas = ", ".join(cambio["valores"])
        marcas = ", ".join("?" for _ in cambio["valores"])
        with conn:
            conn.execute(
                f"INSERT INTO {cambio['tabla']} ({columnas}) VALUES ({marcas})",
                list(cambio["valores"].values()),
            )


def _primera_palabra(texto: str) -> str:
    """Primera palabra alfabética en minúsculas."""
    palabra = ""
    for letra in texto:
        if letra.isalpha():
            palabra += letra.lower()
        elif palabra:
            break
    return palabra


def evaluar() -> int:
    """Ejecuta los casos y comprueba los umbrales de docs/02, sección 7."""
    rng = random.Random(7)
    turnos_total = 0
    turnos_ok = 0
    avisos_ok = 0
    avisos_total = 0
    deriv_ok = 0
    deriv_total = 0
    frases_ok = 0
    frases_total = 0
    arranques_ok = 0
    arranques_total = 0
    fallos: list[str] = []

    for archivo in ("evals/casos_es.json", "evals/casos_en.json"):
        casos = json.loads((RAIZ / archivo).read_text(encoding="utf-8"))
        for caso in casos:
            idioma = "en" if archivo.endswith("_en.json") else "es"
            textos = cargar_textos(idioma)
            conn = iniciar_bd(HOY)
            estado: Estado = crear_estado(idioma=idioma)
            if caso.get("cambio"):
                _aplicar_cambio(conn, caso["cambio"])
            if caso.get("pii"):
                avisos_total += 1
                if contiene_datos_personales(str(caso["pii"])):
                    avisos_ok += 1
                else:
                    fallos.append(f"{caso['id']}: no detectó datos personales")
                hechos = {"tipo_respuesta": "datos_personales", "idioma": idioma,
                          "datos": {}, "permitido_mencionar": []}
                texto, _ = respaldo(hechos, textos, rng=rng)
                frases_total += 1
                if not validar(texto, hechos, "", textos["frases_prohibidas"]):
                    frases_ok += 1
                continue
            negocio = conn.execute("SELECT * FROM negocio").fetchone()
            anterior = aviso_inicial(textos, idioma, "tu", str(negocio["nombre"]),
                                     str(negocio["nombre_bot"]), AHORA)
            avisos_total += 1
            if ("inteligencia artificial" in anterior
                    or "artificial intelligence" in anterior):
                avisos_ok += 1
            else:
                fallos.append(f"{caso['id']}: aviso sin mención de IA")
            for turno in caso.get("turnos", []):
                turnos_total += 1
                entendido = _completar_entendido(turno["entendido"], idioma)
                hechos = resolver(conn, estado, entendido, AHORA)
                tipos = turno.get("tipos", [turno.get("tipo")])
                datos_ok = all(hechos["datos"].get(k) == v
                               for k, v in turno.get("datos", {}).items())
                permitido_ok = all(p in hechos["permitido_mencionar"]
                                   for p in turno.get("permitido", []))
                if hechos["tipo_respuesta"] in tipos and datos_ok and permitido_ok:
                    turnos_ok += 1
                else:
                    fallos.append(f"{caso['id']}: {hechos['tipo_respuesta']} "
                                  f"{hechos['datos']}")
                texto, _ = respaldo(hechos, textos, rng=rng,
                                    evitar_arranque=anterior)
                motivos = validar(texto, hechos, anterior,
                                  textos["frases_prohibidas"])
                frases_total += 1
                if "demasiadas_frases" not in motivos and "demasiado_larga" not in motivos:
                    frases_ok += 1
                else:
                    fallos.append(f"{caso['id']}: frases {motivos}")
                arranques_total += 1
                if _primera_palabra(texto) != _primera_palabra(anterior):
                    arranques_ok += 1
                else:
                    fallos.append(f"{caso['id']}: repite arranque")
                anterior = texto
                if caso.get("derivacion"):
                    deriv_total += 1
                    if ("900 000 000" in texto
                            and hechos["tipo_respuesta"] == "derivar"):
                        deriv_ok += 1
                    else:
                        fallos.append(f"{caso['id']}: derivación incompleta")
            for consulta in caso.get("sql", []):
                fila = conn.execute(consulta["consulta"]).fetchone()
                if (fila is None or list(fila)[0] != consulta["espera"]):
                    fallos.append(f"{caso['id']}: SQL {consulta['consulta']}")
                    turnos_total += 1
                else:
                    turnos_total += 1
                    turnos_ok += 1

    exactitud = 100.0 * turnos_ok / max(1, turnos_total)
    aviso = 100.0 * avisos_ok / max(1, avisos_total)
    derivacion = 100.0 * (deriv_ok / deriv_total) if deriv_total else 100.0
    frases = 100.0 * frases_ok / max(1, frases_total)
    arranques = 100.0 * arranques_ok / max(1, arranques_total)
    print(f"Exactitud de datos: {exactitud:.1f} % (mínimo 100)")
    print(f"Aviso de IA presente: {aviso:.1f} % (mínimo 100)")
    print(f"Derivación correcta: {derivacion:.1f} % (mínimo 100)")
    print(f"Respuesta en 3 frases: {frases:.1f} % (mínimo 95)")
    print(f"Arranque no repetido: {arranques:.1f} % (mínimo 95)")
    for fallo in fallos:
        print("FALLO:", fallo)
    if exactitud < 100 or aviso < 100 or derivacion < 100:
        return 1
    if frases < 95 or arranques < 95:
        return 1
    print("Evals aprobadas.")
    return 0


if __name__ == "__main__":
    sys.exit(evaluar())
