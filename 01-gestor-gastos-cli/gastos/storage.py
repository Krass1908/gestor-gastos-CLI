"""Persistencia de los gastos en un archivo JSON."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

from .models import (
    Gasto,
    validar_categoria,
    validar_fecha,
    validar_monto,
)


class ErrorAlmacenamiento(RuntimeError):
    """Se lanza cuando el archivo de datos no se puede leer o escribir."""


class RepositorioGastos:
    """Lee y escribe gastos en un archivo JSON."""

    def __init__(self, ruta: str | Path):
        self.ruta = Path(ruta)

    # ------------------------------------------------------------------ E/S
    def _cargar(self) -> list[Gasto]:
        if not self.ruta.exists():
            return []
        try:
            with self.ruta.open(encoding="utf-8") as archivo:
                datos = json.load(archivo)
            return [Gasto.desde_dict(d) for d in datos]
        except (json.JSONDecodeError, TypeError) as exc:
            raise ErrorAlmacenamiento(
                f"El archivo {self.ruta} está dañado o tiene un formato inesperado."
            ) from exc

    def _guardar(self, gastos: list[Gasto]) -> None:
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        temporal = self.ruta.with_suffix(".tmp")
        with temporal.open("w", encoding="utf-8") as archivo:
            json.dump([g.a_dict() for g in gastos], archivo, ensure_ascii=False, indent=2)
        temporal.replace(self.ruta)  # reemplazo atómico: no deja el JSON a medias

    # ----------------------------------------------------------- operaciones
    def agregar(
        self,
        monto,
        categoria: str,
        descripcion: str = "",
        fecha: str | None = None,
    ) -> Gasto:
        gastos = self._cargar()
        nuevo_id = max((g.id for g in gastos), default=0) + 1
        gasto = Gasto(
            id=nuevo_id,
            fecha=validar_fecha(fecha),
            monto=validar_monto(monto),
            categoria=validar_categoria(categoria),
            descripcion=descripcion.strip(),
        )
        gastos.append(gasto)
        self._guardar(gastos)
        return gasto

    def listar(self, categoria: str | None = None, mes: str | None = None) -> list[Gasto]:
        """Devuelve los gastos, opcionalmente filtrados por categoría y/o mes (AAAA-MM)."""
        gastos = self._cargar()
        if categoria:
            categoria = validar_categoria(categoria)
            gastos = [g for g in gastos if g.categoria == categoria]
        if mes:
            gastos = [g for g in gastos if g.fecha.startswith(mes)]
        return sorted(gastos, key=lambda g: (g.fecha, g.id))

    def eliminar(self, id_gasto: int) -> bool:
        """Elimina un gasto por id. Devuelve True si existía."""
        gastos = self._cargar()
        restantes = [g for g in gastos if g.id != id_gasto]
        if len(restantes) == len(gastos):
            return False
        self._guardar(restantes)
        return True

    # ------------------------------------------------------------- reportes
    @staticmethod
    def total(gastos: list[Gasto]) -> float:
        return round(sum(g.monto for g in gastos), 2)

    @staticmethod
    def resumen_por_categoria(gastos: list[Gasto]) -> dict[str, float]:
        """Suma por categoría, ordenada de mayor a menor."""
        acumulado: dict[str, float] = defaultdict(float)
        for gasto in gastos:
            acumulado[gasto.categoria] += gasto.monto
        ordenado = sorted(acumulado.items(), key=lambda par: par[1], reverse=True)
        return {cat: round(valor, 2) for cat, valor in ordenado}

    @staticmethod
    def exportar_csv(gastos: list[Gasto], destino: str | Path) -> int:
        """Guarda los gastos en un CSV y devuelve cuántas filas escribió."""
        with Path(destino).open("w", newline="", encoding="utf-8") as archivo:
            escritor = csv.writer(archivo)
            escritor.writerow(["id", "fecha", "monto", "categoria", "descripcion"])
            for g in gastos:
                escritor.writerow([g.id, g.fecha, f"{g.monto:.2f}", g.categoria, g.descripcion])
        return len(gastos)
