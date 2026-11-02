"""Linha de comando: argumentos, códigos de saída e verificar-config (contracts/etl-cli.md, T040).

O caminho completo de coletar contra o banco está em tests/integracao/test_coletar.py.
"""

import pytest
from sqlalchemy.exc import OperationalError

from etl.__main__ import (
    codigo_de_saida,
    interpretar,
    proteger,
    rodar,
    verificar,
    versao_do_codigo,
)
from etl.pipeline.coletar import ColetaEmAndamento, Resultado
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


@pytest.mark.parametrize("comando", ["reserva", "agendado"])
def test_comandos_da_agenda(comando: str) -> None:
    assert interpretar([comando]).comando == comando


def test_coleta_recusada_por_outra_em_andamento_sai_com_codigo_3() -> None:
    def recusar() -> Resultado:
        raise ColetaEmAndamento("já há uma coleta em andamento (execução 5)")

    assert rodar(recusar) == 3


@pytest.mark.parametrize(
    ("status", "codigo"), [(StatusExecucao.DISPENSADA, 0), (StatusExecucao.FALHA, 1)]
)
def test_rodar_traduz_o_status_no_codigo(status: StatusExecucao, codigo: int) -> None:
    assert rodar(lambda: Resultado(1, status)) == codigo


class _Alertador:
    def __init__(self) -> None:
        self.textos: list[str] = []

    def alertar(self, texto: str) -> None:
        self.textos.append(texto)


def _operacional(mensagem: str) -> OperationalError:
    return OperationalError("SELECT 1", {}, Exception(mensagem))


def test_banco_fora_do_ar_antes_de_comecar_alerta_e_sai_com_1(
    caplog: pytest.LogCaptureFixture,
) -> None:
    alertador = _Alertador()

    def falhar() -> int:
        raise _operacional('connection to server at "127.0.0.1", port 1 failed: Connection refused')

    assert proteger(falhar, alertador) == 1
    (texto,) = alertador.textos
    assert "coleta não começou" in texto
    assert "OperationalError" in texto
    assert "Traceback" not in caplog.text


def test_senha_do_banco_recusada_nomeia_a_credencial() -> None:
    alertador = _Alertador()

    def falhar() -> int:
        raise _operacional('FATAL:  password authentication failed for user "etl_escrita"')

    assert proteger(falhar, alertador) == 1
    assert "falha de autenticação: senha do banco (DATABASE_URL_ESCRITA" in alertador.textos[0]


def test_proteger_nao_mexe_no_codigo_de_uma_execucao_normal() -> None:
    alertador = _Alertador()

    assert proteger(lambda: 3, alertador) == 3
    assert alertador.textos == []
