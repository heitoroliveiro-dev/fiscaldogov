"""Agenda do cron e reserva das 05:00 (T062, FR-013, contracts/etl-cli.md).

O cron do Railway roda `agendado` às 06h e 08h UTC (03:00 e 05:00 em Brasília).
A reserva só coleta se ainda não houve sucesso no dia de Brasília.
"""

from datetime import UTC, datetime

import pytest

from etl.pipeline.coletar import Resultado
from etl.pipeline.reserva import Reserva, comando_agendado, inicio_do_dia_em_brasilia
from etl.portas import Gatilho, StatusExecucao


@pytest.mark.parametrize(
    ("hora", "minuto", "comando"),
    [(6, 0, "coletar"), (6, 14, "coletar"), (8, 0, "reserva"), (8, 9, "reserva")],
)
def test_agendado_decide_pelo_horario_utc(hora: int, minuto: int, comando: str) -> None:
    assert comando_agendado(datetime(2026, 11, 2, hora, minuto, tzinfo=UTC)) == comando


def test_agendado_fora_das_duas_janelas_cai_na_reserva() -> None:
    # um "Run now" manual no painel do Railway nunca coleta duas vezes no mesmo dia
    assert comando_agendado(datetime(2026, 11, 2, 15, 0, tzinfo=UTC)) == "reserva"


@pytest.mark.parametrize(
    ("agora", "meia_noite"),
    [
        (datetime(2026, 11, 2, 8, 0, tzinfo=UTC), datetime(2026, 11, 2, 3, 0, tzinfo=UTC)),
        # 01:30 UTC ainda é dia 1 em Brasília
        (datetime(2026, 11, 2, 1, 30, tzinfo=UTC), datetime(2026, 11, 1, 3, 0, tzinfo=UTC)),
    ],
)
def test_inicio_do_dia_e_meia_noite_de_brasilia(agora: datetime, meia_noite: datetime) -> None:
    assert inicio_do_dia_em_brasilia(agora) == meia_noite


class _Execucoes:
    def __init__(self, bem_sucedida: bool) -> None:
        self._bem_sucedida = bem_sucedida
        self.consultado_desde: datetime | None = None
        self.dispensadas: list[str] = []

    def houve_bem_sucedida_desde(self, momento: datetime) -> bool:
        self.consultado_desde = momento
        return self._bem_sucedida

    def registrar_dispensada(self, versao_codigo: str) -> int:
        self.dispensadas.append(versao_codigo)
        return 77


class _Coleta:
    def __init__(self) -> None:
        self.gatilhos: list[Gatilho] = []

    def executar(self, gatilho: Gatilho) -> Resultado:
        self.gatilhos.append(gatilho)
        return Resultado(9, StatusExecucao.SUCESSO)


AS_05_EM_BRASILIA = datetime(2026, 11, 2, 8, 0, tzinfo=UTC)


def _reserva(execucoes: _Execucoes, coleta: _Coleta) -> Reserva:
    return Reserva(
        execucoes=execucoes, coleta=coleta, versao_codigo="abc", relogio=lambda: AS_05_EM_BRASILIA
    )


def test_reserva_com_sucesso_no_dia_e_dispensada_sem_coletar() -> None:
    execucoes, coleta = _Execucoes(bem_sucedida=True), _Coleta()

    resultado = _reserva(execucoes, coleta).executar()

    assert resultado == Resultado(77, StatusExecucao.DISPENSADA)
    assert execucoes.dispensadas == ["abc"]
    assert coleta.gatilhos == []
    assert execucoes.consultado_desde == datetime(2026, 11, 2, 3, 0, tzinfo=UTC)


def test_reserva_sem_sucesso_no_dia_coleta_com_gatilho_reserva() -> None:
    execucoes, coleta = _Execucoes(bem_sucedida=False), _Coleta()

    resultado = _reserva(execucoes, coleta).executar()

    assert resultado == Resultado(9, StatusExecucao.SUCESSO)
    assert coleta.gatilhos == [Gatilho.RESERVA]
    assert execucoes.dispensadas == []
