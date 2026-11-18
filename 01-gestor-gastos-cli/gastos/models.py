"""Modelo de datos y validaciones del gestor de gastos."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from datetime import date

CATEGORIAS = ("comida", "transporte", "hogar", "ocio", "salud", "otros")


class ErrorValidacion(ValueError):
    """Se lanza cuando los datos de un gasto no son válidos."""


@dataclass
class Gasto:
    """Un gasto individual."""

    id: int
    fecha: str  # formato ISO: AAAA-MM-DD
    monto: float
    categoria: str
    descripcion: str = ""

    def a_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def desde_dict(cls, datos: dict) -> "Gasto":
        return cls(**datos)


def validar_monto(monto) -> float:
    """Convierte el monto a float y verifica que sea positivo y finito."""
    try:
        valor = float(monto)
    except (TypeError, ValueError):
        raise ErrorValidacion(f"El monto '{monto}' no es un número válido.") from None
    if not math.isfinite(valor):
        raise ErrorValidacion("El monto debe ser un número finito.")
    if valor <= 0:
        raise ErrorValidacion("El monto debe ser mayor que cero.")
    return round(valor, 2)


def validar_categoria(categoria: str) -> str:
    """Normaliza la categoría y comprueba que exista en CATEGORIAS."""
    normalizada = (categoria or "").strip().lower()
    if normalizada not in CATEGORIAS:
        validas = ", ".join(CATEGORIAS)
        raise ErrorValidacion(f"Categoría '{categoria}' no válida. Opciones: {validas}.")
    return normalizada


def validar_fecha(fecha: str | None) -> str:
    """Devuelve la fecha en formato ISO; si no se indica, usa la de hoy."""
    if not fecha:
        return date.today().isoformat()
    try:
        return date.fromisoformat(fecha).isoformat()
    except ValueError:
        raise ErrorValidacion(
            f"Fecha '{fecha}' no válida. Usa el formato AAAA-MM-DD."
        ) from None
