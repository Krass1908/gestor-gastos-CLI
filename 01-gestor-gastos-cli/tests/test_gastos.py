import json

import pytest

from gastos.cli import main
from gastos.models import ErrorValidacion, validar_categoria, validar_fecha, validar_monto
from gastos.storage import ErrorAlmacenamiento, RepositorioGastos


@pytest.fixture
def repo(tmp_path):
    return RepositorioGastos(tmp_path / "gastos.json")


# ------------------------------------------------------------ validaciones
@pytest.mark.parametrize("valor", ["abc", "", "0", "-5", "nan", "inf", None])
def test_monto_invalido(valor):
    with pytest.raises(ErrorValidacion):
        validar_monto(valor)


def test_monto_valido_se_redondea():
    assert validar_monto("10.456") == 10.46


def test_categoria_se_normaliza_y_rechaza_desconocidas():
    assert validar_categoria("  Comida ") == "comida"
    with pytest.raises(ErrorValidacion):
        validar_categoria("viajes")


def test_fecha():
    assert validar_fecha("2026-03-05") == "2026-03-05"
    assert len(validar_fecha(None)) == 10
    with pytest.raises(ErrorValidacion):
        validar_fecha("05/03/2026")


# --------------------------------------------------------------- repositorio
def test_agregar_asigna_ids_incrementales(repo):
    g1 = repo.agregar("100", "comida", "tacos", "2026-01-10")
    g2 = repo.agregar("50", "ocio", fecha="2026-01-11")
    assert (g1.id, g2.id) == (1, 2)
    assert len(repo.listar()) == 2


def test_los_datos_persisten_en_disco(repo):
    repo.agregar("25.5", "transporte", fecha="2026-02-01")
    otro_repo = RepositorioGastos(repo.ruta)
    assert otro_repo.listar()[0].monto == 25.5


def test_filtros_por_categoria_y_mes(repo):
    repo.agregar("10", "comida", fecha="2026-01-05")
    repo.agregar("20", "comida", fecha="2026-02-05")
    repo.agregar("30", "hogar", fecha="2026-02-06")
    assert len(repo.listar(categoria="comida")) == 2
    assert len(repo.listar(mes="2026-02")) == 2
    assert len(repo.listar(categoria="comida", mes="2026-02")) == 1


def test_eliminar_no_reutiliza_ids(repo):
    repo.agregar("10", "comida")
    repo.agregar("20", "comida")
    assert repo.eliminar(2) is True
    assert repo.eliminar(99) is False
    assert repo.agregar("5", "otros").id == 2  # max(id)+1 con solo el #1 restante


def test_resumen_ordenado_de_mayor_a_menor(repo):
    repo.agregar("10", "comida")
    repo.agregar("90", "hogar")
    repo.agregar("15.5", "comida")
    resumen = repo.resumen_por_categoria(repo.listar())
    assert list(resumen) == ["hogar", "comida"]
    assert resumen["comida"] == 25.5
    assert repo.total(repo.listar()) == 115.5


def test_archivo_corrupto_lanza_error_claro(tmp_path):
    ruta = tmp_path / "roto.json"
    ruta.write_text("{esto no es json", encoding="utf-8")
    with pytest.raises(ErrorAlmacenamiento):
        RepositorioGastos(ruta).listar()


def test_exportar_csv(repo, tmp_path):
    repo.agregar("12.5", "salud", "farmacia", "2026-04-01")
    destino = tmp_path / "salida.csv"
    assert repo.exportar_csv(repo.listar(), destino) == 1
    lineas = destino.read_text(encoding="utf-8").splitlines()
    assert lineas[0] == "id,fecha,monto,categoria,descripcion"
    assert lineas[1] == "1,2026-04-01,12.50,salud,farmacia"


# ----------------------------------------------------------------------- CLI
def test_cli_flujo_completo(tmp_path, capsys):
    archivo = str(tmp_path / "datos.json")
    assert main(["--archivo", archivo, "agregar", "99.9", "comida", "-d", "pizza"]) == 0
    assert main(["--archivo", archivo, "listar"]) == 0
    salida = capsys.readouterr().out
    assert "pizza" in salida and "99.90" in salida
    assert json.loads(open(archivo, encoding="utf-8").read())[0]["categoria"] == "comida"


def test_cli_errores_devuelven_codigo_1(tmp_path, capsys):
    archivo = str(tmp_path / "datos.json")
    assert main(["--archivo", archivo, "agregar", "-5", "comida"]) == 1
    assert main(["--archivo", archivo, "agregar", "5", "inexistente"]) == 1
    assert main(["--archivo", archivo, "eliminar", "7"]) == 1
    assert "Error" in capsys.readouterr().err


def test_cli_resumen_vacio(tmp_path, capsys):
    assert main(["--archivo", str(tmp_path / "x.json"), "resumen"]) == 0
    assert "No hay gastos" in capsys.readouterr().out
