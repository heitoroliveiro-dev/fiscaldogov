"""Agenda do cron e execução de reserva das 05:00 (T071, FR-013, contracts/etl-cli.md).

Um único serviço no Railway, com cron `0 6,8 * * *` (UTC), roda `agendado`:
às 06h UTC (03:00 em Brasília) coleta; em qualquer outro horário, cai na
reserva, que só coleta se ainda não houve `sucesso` ou `com_pendencias` no dia
de Brasília. Assim um "Run now" manual no painel nunca coleta duas vezes.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, time
from typing import Literal, Protocol
from zoneinfo import ZoneInfo

from etl.pipeline.coletar import Resultado
from etl.portas import Gatilho, StatusExecucao

BRASILIA = ZoneInfo("America/Sao_Paulo")
HORA_DA_COLETA_UTC = 6


def comando_agendado(agora: datetime) -> Literal["coletar", "reserva"]:
    return "coletar" if agora.astimezone(UTC).hour == HORA_DA_COLETA_UTC else "reserva"


def inicio_do_dia_em_brasilia(agora: datetime) -> datetime:
    dia = agora.astimezone(BRASILIA).date()
    return datetime.combine(dia, time(0), tzinfo=BRASILIA).astimezone(UTC)


class _Execucoes(Protocol):
    def houve_bem_sucedida_desde(self, momento: datetime) -> bool: ...

    def registrar_dispensada(self, versao_codigo: str) -> int: ...


class _Coleta(Protocol):
    def executar(self, gatilho: Gatilho) -> Resultado: ...


@dataclass(frozen=True)
class Reserva:
    execucoes: _Execucoes
    coleta: _Coleta
    versao_codigo: str
    relogio: Callable[[], datetime] = lambda: datetime.now(UTC)

    def executar(self) -> Resultado:
        if self.execucoes.houve_bem_sucedida_desde(inicio_do_dia_em_brasilia(self.relogio())):
            execucao_id = self.execucoes.registrar_dispensada(self.versao_codigo)
            return Resultado(execucao_id, StatusExecucao.DISPENSADA)
        # a coleta fecha as travadas há mais de 60 min antes de começar
        return self.coleta.executar(Gatilho.RESERVA)
