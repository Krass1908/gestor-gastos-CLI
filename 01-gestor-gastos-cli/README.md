# 💸 Gestor de gastos por línea de comandos

Aplicación CLI en Python para registrar, consultar y resumir gastos personales. No usa librerías externas: solo la biblioteca estándar.

!\[Python](https://img.shields.io/badge/python-3.10%2B-blue)
!\[Tests](https://img.shields.io/badge/tests-pytest-green)

## ¿Qué hace?

* Registra gastos con monto, categoría, descripción y fecha.
* Lista y filtra por categoría y/o mes.
* Muestra un resumen con totales, porcentajes y una barra por categoría.
* Exporta todo a CSV.
* Guarda los datos en un JSON con escritura atómica (no se corrompe si el programa se interrumpe).

## Instalación y uso

```bash
git clone https://github.com/krass1908/gestor-gastos-cli.git
cd gestor-gastos-cli
python -m gastos --help
```

Ejemplos:

```bash
python -m gastos agregar 125.50 comida -d "Tacos con amigos"
python -m gastos agregar 40 transporte -f 2026-03-15
python -m gastos listar --mes 2026-03
python -m gastos resumen
python -m gastos eliminar 2
python -m gastos exportar gastos.csv
```

Ejemplo de salida de `resumen`:

```
hogar         1200.00   70.2%  ##############
comida         410.50   24.0%  #####
transporte      99.90    5.8%  #
----------------------------------------
TOTAL         1710.40
```

Por defecto los datos se guardan en `\~/.gestor\_gastos.json`. Puedes cambiarlo con `--archivo ruta.json` o con la variable de entorno `GASTOS\_ARCHIVO`.

## Pruebas

```bash
pip install -r requirements.txt
pytest
```

## Estructura

```
gastos/
├── models.py    # dataclass Gasto y validaciones
├── storage.py   # repositorio JSON, filtros, resumen y exportación CSV
├── cli.py       # argparse y formato de salida
└── \_\_main\_\_.py  # permite ejecutar: python -m gastos
tests/
└── test\_gastos.py
```

## Conceptos que practica este proyecto

* Dataclasses y type hints.
* Separación de responsabilidades (modelo, almacenamiento, interfaz).
* Manejo de excepciones propias y códigos de salida de un programa CLI.
* Lectura/escritura de JSON y CSV.
* Pruebas con `pytest` (fixtures, `parametrize`, `tmp\_path`, `capsys`).

## Ideas para ampliarlo

* Presupuesto mensual por categoría con alertas.
* Gastos recurrentes.
* Cambiar el almacenamiento a SQLite.

