"""Interfaz del proveedor de IA y sus implementaciones (docs/05, sección 9).

Qué hace: define generar_json y generar_texto con tiempo máximo de 15 s,
un reintento y cambio al respaldo si falla. Recibe: prompts. Devuelve:
JSON o texto, más el uso de tokens en ultimo_uso. Qué NO hace: no guarda
ni registra el texto del usuario, solo cuenta tokens.

Nota de contrato: ultimo_uso y temperatura amplían el contrato de 05.9
sin romperlo; se anotan en docs/DECISIONES.md.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass


class ErrorProveedor(Exception):
    """Falla el proveedor de IA tras el reintento."""


@dataclass
class Uso:
    """Tokens consumidos por una llamada (para el contador de coste)."""

    entrada: int = 0
    salida: int = 0


class ProveedorIA(ABC):
    """Contrato que cumplen el proveedor principal y el de respaldo."""

    def __init__(self) -> None:
        """Inicializa el contador de uso de la última llamada."""
        self.ultimo_uso: Uso | None = None

    @abstractmethod
    def generar_json(self, prompt: str, max_tokens: int,
                     temperatura: float = 0.1) -> dict[str, object]:
        """Pide un JSON al modelo (para entender).

        Parámetros:
            prompt: instrucciones con el mensaje y el historial.
            max_tokens: tope de tokens de la respuesta.
            temperatura: baja (0 a 0,2) para extraer datos.
        """

    @abstractmethod
    def generar_texto(self, prompt: str, max_tokens: int,
                      temperatura: float = 0.6) -> str:
        """Pide un texto al modelo (para redactar).

        Parámetros:
            prompt: estilo más hechos.
            max_tokens: tope de tokens de la respuesta.
            temperatura: media (0,5 a 0,7) para sonar natural.
        """


class ProveedorHTTP(ProveedorIA):
    """Proveedor con API compatible con OpenAI (Mistral, OpenAI, etc.).

    Por qué HTTP estándar sin SDK: cambiar de proveedor es cambiar la
    URL y la clave, sin tocar el motor (ver 03.1).
    """

    def __init__(self, base_url: str, clave: str, modelo: str,
                 tiempo_maximo: int = 15) -> None:
        """Guarda la configuración sin exponer la clave en registros."""
        super().__init__()
        self._url = base_url.rstrip("/") + "/chat/completions"
        self._clave = clave
        self._modelo = modelo
        self._tiempo_maximo = tiempo_maximo

    def _llamar(self, cuerpo: dict[str, object]) -> dict[str, object]:
        """Envía la petición con un reintento ante fallos de red."""
        datos = json.dumps(cuerpo).encode("utf-8")
        ultimo_error = ""
        for _ in range(2):
            # Por qué User-Agent propio: varios proveedores están detrás de
            # cortafuegos que bloquean con 403 el agente "Python-urllib".
            peticion = urllib.request.Request(
                self._url, data=datos,
                headers={"Content-Type": "application/json",
                         "Accept": "application/json",
                         "User-Agent": "MascotaFelizDemo/1.0",
                         "Authorization": "Bearer " + self._clave},
                method="POST",
            )
            try:
                with urllib.request.urlopen(peticion,
                                            timeout=self._tiempo_maximo) as respuesta:
                    cuerpo_resp: dict[str, object] = json.loads(
                        respuesta.read().decode("utf-8"))
                    return cuerpo_resp
            except urllib.error.HTTPError as error:
                # Se guarda un trozo del cuerpo de error del proveedor para
                # diagnosticar (clave incorrecta, saldo, modelo). Nunca
                # contiene la clave ni el texto del usuario.
                try:
                    detalle = error.read().decode("utf-8", "replace")[:300]
                except Exception:
                    detalle = ""
                ultimo_error = f"HTTP {error.code} en {self._url}: {detalle}"
                if error.code in (400, 401, 402, 403, 404):
                    # Errores de configuración: reintentar no sirve.
                    break
                time.sleep(0.5)
            except Exception as error:  # Red o tiempo: se reintenta una vez.
                ultimo_error = str(error)
                time.sleep(0.5)
        raise ErrorProveedor(f"sin respuesta del proveedor: {ultimo_error}")

    @staticmethod
    def _uso(respuesta: dict[str, object]) -> Uso:
        """Extrae el conteo de tokens sin tocar el contenido."""
        uso = respuesta.get("usage", {})
        if isinstance(uso, dict):
            entrada = uso.get("prompt_tokens", 0)
            salida = uso.get("completion_tokens", 0)
            if isinstance(entrada, int) and isinstance(salida, int):
                return Uso(entrada, salida)
        return Uso()

    @staticmethod
    def _contenido(respuesta: dict[str, object]) -> str:
        """Extrae el texto de la primera opción."""
        opciones = respuesta.get("choices", [])
        if (isinstance(opciones, list) and opciones
                and isinstance(opciones[0], dict)):
            mensaje = opciones[0].get("message", {})
            if isinstance(mensaje, dict):
                contenido = mensaje.get("content", "")
                if isinstance(contenido, str):
                    return contenido
        raise ErrorProveedor("respuesta sin contenido")

    def generar_json(self, prompt: str, max_tokens: int,
                     temperatura: float = 0.1) -> dict[str, object]:
        """Pide JSON con formato de respuesta forzado a objeto."""
        respuesta = self._llamar({
            "model": self._modelo,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperatura,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        })
        self.ultimo_uso = self._uso(respuesta)
        texto = self._contenido(respuesta)
        try:
            valor: dict[str, object] = json.loads(texto)
        except json.JSONDecodeError as error:
            raise ErrorProveedor(f"JSON inválido: {error}") from error
        return valor

    def generar_texto(self, prompt: str, max_tokens: int,
                      temperatura: float = 0.6) -> str:
        """Pide texto libre al modelo."""
        respuesta = self._llamar({
            "model": self._modelo,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperatura,
            "max_tokens": max_tokens,
        })
        self.ultimo_uso = self._uso(respuesta)
        return self._contenido(respuesta)


class ProveedorFalso(ProveedorIA):
    """Proveedor de mentira solo para pruebas y evals sin red.

    Devuelve respuestas en cola y anota los prompts recibidos para que
    las pruebas comprueben qué se le pidió. Nunca se usa en producción.
    """

    def __init__(self, jsons: list[dict[str, object]] | None = None,
                 textos: list[str] | None = None) -> None:
        """Recibe las colas de respuestas programadas."""
        super().__init__()
        self._jsons = list(jsons or [])
        self._textos = list(textos or [])
        self.prompts: list[str] = []

    def generar_json(self, prompt: str, max_tokens: int,
                     temperatura: float = 0.1) -> dict[str, object]:
        """Devuelve el siguiente JSON programado."""
        self.prompts.append(prompt)
        self.ultimo_uso = Uso()
        if not self._jsons:
            raise ErrorProveedor("cola de JSON vacía")
        return self._jsons.pop(0)

    def generar_texto(self, prompt: str, max_tokens: int,
                      temperatura: float = 0.6) -> str:
        """Devuelve el siguiente texto programado."""
        self.prompts.append(prompt)
        self.ultimo_uso = Uso()
        if not self._textos:
            raise ErrorProveedor("cola de textos vacía")
        return self._textos.pop(0)


class ProveedorConRespaldo(ProveedorIA):
    """Prueba el principal y, si falla, el secundario.

    Por qué dos proveedores: la demo nunca se cae aunque uno falle;
    si fallan los dos, el flujo usa plantillas sin IA (ver 03.1).
    """

    def __init__(self, principal: ProveedorIA, respaldo: ProveedorIA) -> None:
        """Guarda ambos proveedores ya configurados."""
        super().__init__()
        self._principal = principal
        self._respaldo = respaldo

    def generar_json(self, prompt: str, max_tokens: int,
                     temperatura: float = 0.1) -> dict[str, object]:
        """Pide JSON al principal o al respaldo."""
        try:
            resultado = self._principal.generar_json(prompt, max_tokens, temperatura)
            self.ultimo_uso = self._principal.ultimo_uso
            return resultado
        except ErrorProveedor:
            resultado = self._respaldo.generar_json(prompt, max_tokens, temperatura)
            self.ultimo_uso = self._respaldo.ultimo_uso
            return resultado

    def generar_texto(self, prompt: str, max_tokens: int,
                      temperatura: float = 0.6) -> str:
        """Pide texto al principal o al respaldo."""
        try:
            resultado = self._principal.generar_texto(prompt, max_tokens, temperatura)
            self.ultimo_uso = self._principal.ultimo_uso
            return resultado
        except ErrorProveedor:
            resultado = self._respaldo.generar_texto(prompt, max_tokens, temperatura)
            self.ultimo_uso = self._respaldo.ultimo_uso
            return resultado
