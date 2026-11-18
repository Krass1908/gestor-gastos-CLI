"""Interfaz de línea de comandos del gestor de gastos."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import __version__
from .models import CATEGORIAS, ErrorValidacion, Gasto
from .storage import ErrorAlmacenamiento, RepositorioGastos

ARCHIVO_POR_DEFECTO = Path.home() / ".gestor_gastos.json"


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gastos",
        description="Gestor de gastos personales por línea de comandos.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--archivo",
        help="Ruta del JSON de datos (por defecto ~/.gestor_gastos.json "
        "o la variable de entorno GASTOS_ARCHIVO).",
    )
    sub = parser.add_subparsers(dest="comando", required=True)

    agregar = sub.add_parser("agregar", help="Registra un gasto nuevo.")
    agregar.add_argument("monto", help="Monto del gasto, por ejemplo 125.50")
    agregar.add_argument("categoria", help=f"Una de: {', '.join(CATEGORIAS)}")
    agregar.add_argument("-d", "--descripcion", default="", help="Texto opcional.")
    agregar.add_argument("-f", "--fecha", help="Fecha AAAA-MM-DD (por defecto, hoy).")

    listar = sub.add_parser("listar", help="Muestra los gastos registrados.")
    listar.add_argument("-c", "--categoria", help="Filtra por categoría.")
    listar.add_argument("-m", "--mes", help="Filtra por mes (AAAA-MM).")

    eliminar = sub.add_parser("eliminar", help="Elimina un gasto por su id.")
    eliminar.add_argument("id", type=int, help="Id del gasto (se ve con 'listar').")

    resumen = sub.add_parser("resumen", help="Total y desglose por categoría.")
    resumen.add_argument("-m", "--mes", help="Limita el resumen a un mes (AAAA-MM).")

    exportar = sub.add_parser("exportar", help="Exporta los gastos a un CSV.")
    exportar.add_argument("destino", help="Ruta del archivo CSV de salida.")
    return parser


def formatear_tabla(gastos: list[Gasto]) -> str:
    if not gastos:
        return "No hay gastos que mostrar."
    lineas = [f"{'ID':>3}  {'FECHA':<10}  {'MONTO':>10}  {'CATEGORÍA':<10}  DESCRIPCIÓN"]
    lineas.append("-" * 60)
    for g in gastos:
        lineas.append(
            f"{g.id:>3}  {g.fecha:<10}  {g.monto:>10.2f}  {g.categoria:<10}  {g.descripcion}"
        )
    return "\n".join(lineas)


def formatear_resumen(gastos: list[Gasto]) -> str:
    if not gastos:
        return "No hay gastos que resumir."
    total = RepositorioGastos.total(gastos)
    lineas = []
    for categoria, valor in RepositorioGastos.resumen_por_categoria(gastos).items():
        porcentaje = valor / total * 100
        barra = "#" * max(1, round(porcentaje / 5))
        lineas.append(f"{categoria:<10} {valor:>10.2f}  {porcentaje:>5.1f}%  {barra}")
    lineas.append("-" * 40)
    lineas.append(f"{'TOTAL':<10} {total:>10.2f}")
    return "\n".join(lineas)


def main(argv: list[str] | None = None) -> int:
    args = construir_parser().parse_args(argv)
    ruta = args.archivo or os.environ.get("GASTOS_ARCHIVO") or ARCHIVO_POR_DEFECTO
    repo = RepositorioGastos(ruta)

    try:
        if args.comando == "agregar":
            gasto = repo.agregar(args.monto, args.categoria, args.descripcion, args.fecha)
            print(f"Gasto #{gasto.id} registrado: {gasto.monto:.2f} en {gasto.categoria}.")
        elif args.comando == "listar":
            print(formatear_tabla(repo.listar(args.categoria, args.mes)))
        elif args.comando == "eliminar":
            if repo.eliminar(args.id):
                print(f"Gasto #{args.id} eliminado.")
            else:
                print(f"No existe un gasto con id {args.id}.", file=sys.stderr)
                return 1
        elif args.comando == "resumen":
            print(formatear_resumen(repo.listar(mes=args.mes)))
        elif args.comando == "exportar":
            filas = repo.exportar_csv(repo.listar(), args.destino)
            print(f"{filas} gastos exportados a {args.destino}.")
    except (ErrorValidacion, ErrorAlmacenamiento, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
