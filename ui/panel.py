"""Panel de negocio: lectura, validación y guardado de cambios.

Qué hace: convierte entre céntimos y euros, detecta filas cambiadas y
guarda con validación (precio mayor o igual a 0, stock entero, horas
coherentes). Recibe: conexión y tablas. Devuelve: número de cambios.
Qué NO hace: no dibuja widgets (eso lo hace app.py con data_editor).
"""

from __future__ import annotations

import re
import sqlite3

import pandas as pd

_PATRON_HORA = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def euros_a_centimos(texto: str) -> int:
    """Convierte "49,90" o "49.90" a 4990 céntimos.

    Parámetros:
        texto: precio en euros con coma o punto decimal.
    Devuelve: céntimos enteros.
    Errores:
        ValueError("error_precio") si no es un número mayor o igual a 0.
    Ejemplo:
        >>> euros_a_centimos("49,90")
        4990
    """
    try:
        # Se aceptan las formas habituales de escribir un precio: "12,5",
        # "12.50", "12,50 €", "12 EUR" y "1.234,50" (punto de miles).
        limpio = str(texto).strip().lower().replace("€", "").replace("eur", "")
        limpio = limpio.replace(" ", "")
        if "," in limpio and "." in limpio:
            limpio = limpio.replace(".", "")
        valor = float(limpio.replace(",", "."))
    except (ValueError, AttributeError):
        raise ValueError("error_precio") from None
    if valor != valor or valor in (float("inf"), float("-inf")):
        raise ValueError("error_precio")  # Rechaza "nan" e infinito.
    if valor < 0:
        raise ValueError("error_precio")
    return int(round(valor * 100))


def validar_stock(valor: object) -> int:
    """Valida que el stock sea un entero mayor o igual a cero.

    Errores:
        ValueError("error_stock") si no cumple.
    Ejemplo:
        >>> validar_stock(3)
        3
    """
    try:
        numero = int(str(valor).strip())
    except (ValueError, AttributeError):
        raise ValueError("error_stock") from None
    if numero < 0 or float(str(valor).strip().replace(",", ".")) != numero:
        raise ValueError("error_stock")
    return numero


def validar_horas(inicio: str, fin: str) -> None:
    """Comprueba formato HH:MM y que el cierre sea posterior.

    Errores:
        ValueError("error_horas") si no cumple.
    Ejemplo:
        >>> validar_horas("09:00", "14:00")
    """
    if not (_PATRON_HORA.match(str(inicio)) and _PATRON_HORA.match(str(fin))):
        raise ValueError("error_horas")
    if str(fin) <= str(inicio):
        raise ValueError("error_horas")


def cargar_tabla(conn: sqlite3.Connection, tabla: str) -> pd.DataFrame:
    """Lee una tabla en un DataFrame con columnas en euros si hay precio."""
    df = pd.read_sql_query(f"SELECT * FROM {tabla} ORDER BY id", conn)
    if "precio_centimos" in df.columns:
        df["precio_eur"] = (df["precio_centimos"] / 100).round(2)
    return df


def guardar_tabla(
    conn: sqlite3.Connection,
    tabla: str,
    original: pd.DataFrame,
    editado: pd.DataFrame,
    solo_columnas: tuple[str, ...] = (),
) -> int:
    """Guarda las filas cambiadas con validación y registra el evento.

    Parámetros:
        conn: conexión SQLite de la sesión.
        tabla: nombre de la tabla.
        original: DataFrame tal como se cargó.
        editado: DataFrame tras el editor.
        solo_columnas: columnas editables; vacío permite todas menos id.
    Devuelve: número de filas actualizadas.
    Errores:
        ValueError con clave i18n ("error_precio", "error_stock",
        "error_horas") si algún valor no es válido. No guarda nada.
    Ejemplo:
        >>> guardar_tabla(conn, "productos", df0, df1)  # doctest: +SKIP
        2
    """
    if len(original) != len(editado):
        raise ValueError("error_filas")
    cambios = 0
    with conn:
        for (_, fila0), (_, fila1) in zip(original.iterrows(), editado.iterrows()):
            if fila0["id"] != fila1["id"]:
                raise ValueError("error_filas")
            valores: dict[str, object] = {}
            for columna in editado.columns:
                if columna in ("id", "precio_eur") or (
                    solo_columnas and columna not in solo_columnas
                ):
                    continue
                nuevo = fila1[columna]
                if pd.isna(nuevo) and pd.isna(fila0[columna]):
                    continue
                if nuevo == fila0[columna]:
                    continue
                valores[str(columna)] = nuevo
            if "precio_eur" in editado.columns and (
                not solo_columnas or "precio_eur" in solo_columnas
            ):
                euros = editado.loc[editado["id"] == fila1["id"], "precio_eur"].iloc[0]
                original_eur = original.loc[
                    original["id"] == fila1["id"], "precio_eur"].iloc[0]
                if euros != original_eur:
                    valores["precio_centimos"] = euros_a_centimos(str(euros))
            if not valores:
                continue
            _validar_fila(tabla, fila1, valores)
            asignaciones = ", ".join(f"{c} = ?" for c in valores)
            conn.execute(
                f"UPDATE {tabla} SET {asignaciones} WHERE id = ?",
                list(valores.values()) + [fila1["id"]],
            )
            cambios += 1
        if cambios:
            conn.execute(
                "INSERT INTO registro_eventos (tipo, detalle, creado)"
                " VALUES (?, ?, datetime('now'))",
                ("cambio_panel", f"{tabla}: {cambios} filas"),
            )
    return cambios


def _validar_fila(tabla: str, fila: pd.Series, valores: dict[str, object]) -> None:
    """Valida precio, stock y horas de una fila cambiada."""
    if "precio_centimos" in valores:
        centimos = valores["precio_centimos"]
        if not isinstance(centimos, int) or centimos < 0:
            raise ValueError("error_precio")
    if "stock" in valores:
        valores["stock"] = validar_stock(valores["stock"])
    if "duracion_min" in valores:
        try:
            duracion = int(valores["duracion_min"])
        except (TypeError, ValueError):
            raise ValueError("error_stock") from None
        if duracion <= 0:
            raise ValueError("error_stock")
        valores["duracion_min"] = duracion
    inicio = valores.get("hora_inicio", valores.get("hora_apertura", fila.get(
        "hora_inicio", fila.get("hora_apertura", ""))))
    fin = valores.get("hora_fin", valores.get("hora_cierre", fila.get(
        "hora_fin", fila.get("hora_cierre", ""))))
    if tabla in ("turnos", "horarios_negocio") and (
        "hora_inicio" in valores or "hora_fin" in valores
        or "hora_apertura" in valores or "hora_cierre" in valores
    ):
        validar_horas(str(inicio), str(fin))


def resumen_ventas(conn: sqlite3.Connection) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devuelve los pedidos y las citas registrados durante la demo."""
    ventas = pd.read_sql_query(
        "SELECT v.id, p.nombre_es AS producto, v.cantidad,"
        " v.total_centimos / 100.0 AS total_eur, v.creado"
        " FROM ventas v JOIN productos p ON p.id = v.producto_id"
        " ORDER BY v.id", conn)
    citas = pd.read_sql_query(
        "SELECT c.id, COALESCE(v.nombre, 'Equipo') AS veterinario,"
        " s.nombre_es AS servicio, c.inicio, c.fin, c.alias_cliente"
        " FROM citas c LEFT JOIN veterinarios v ON v.id = c.veterinario_id"
        " JOIN servicios s ON s.id = c.servicio_id"
        " ORDER BY c.inicio", conn)
    return ventas, citas
