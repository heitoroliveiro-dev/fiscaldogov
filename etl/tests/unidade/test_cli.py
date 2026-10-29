"""Linha de comando: argumentos, códigos de saída e verificar-config (contracts/etl-cli.md, T040).

O caminho completo de coletar contra o banco está em tests/integracao/test_coletar.py.
"""

import pytest

from etl.__main__ import codigo_de_saida, interpretar, verificar, versao_do_codigo
from etl.portas import Gatilho, StatusExecucao


@pytest.mark.parametrize(
    ("status", "codigo"),
    [
        (StatusExecucao.SUCESSO, 0),
        (StatusExecucao.COM_PENDENCIAS, 0),
        (StatusExecucao.DISPENSADA, 0),
        (StatusExecucao.FALHA, 1),
    ],
)
def test_codigo_de_saida_por_status(status: StatusExecucao, codigo: int) -> None:
    assert codigo_de_saida(status) == codigo


def test_coletar_sem_gatilho_e_manual() -> None:
    argumentos = interpretar(["coletar"])

    assert (argumentos.comando, argumentos.gatilho) == ("coletar", Gatilho.MANUAL)


def test_coletar_agendada() -> None:
    assert interpretar(["coletar", "--gatilho", "agendada"]).gatilho is Gatilho.AGENDADA


@pytest.mark.parametrize(
    "argumentos",
    [[], ["apagar-tudo"], ["coletar", "--gatilho", "reserva"], ["coletar", "--gatilho", "x"]],
)
def test_comando_ou_gatilho_invalido_sai_com_codigo_2(argumentos: list[str]) -> None:
    # reserva é comando próprio (US2), não um gatilho de coletar
    with pytest.raises(SystemExit) as saida:
        interpretar(argumentos)

    assert saida.value.code == 2


def test_versao_do_codigo_vem_do_commit_do_deploy() -> None:
    assert versao_do_codigo({"RAILWAY_GIT_COMMIT_SHA": "abc1234"}) == "abc1234"
    assert versao_do_codigo({}) == "desconhecida"


def test_verificar_config_passa_quando_todas_as_conferencias_passam() -> None:
    feitas: list[str] = []

    codigo = verificar({"banco": lambda: feitas.append("banco"), "r2": lambda: feitas.append("r2")})

    assert codigo == 0
    assert feitas == ["banco", "r2"]


def test_verificar_config_roda_todas_e_falha_se_alguma_falhar() -> None:
    feitas: list[str] = []

    def r2_fora() -> None:
        raise ConnectionError("R2 fora do ar")

    codigo = verificar(
        {
            "banco": lambda: feitas.append("banco"),
            "r2": r2_fora,
            "api": lambda: feitas.append("api"),
        }
    )

    assert codigo == 1
    assert feitas == ["banco", "api"]
