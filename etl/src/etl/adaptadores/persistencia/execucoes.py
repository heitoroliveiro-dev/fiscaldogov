"""Registro de cada execução em execucao_etl (FR-010, data-model.md).

Cada operação abre a própria transação, separada da que grava a coleta: o
início e o desfecho de uma execução com falha continuam registrados depois do
ROLLBACK dos dados (FR-012).
"""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import func, select

from etl.adaptadores.persistencia.banco import Banco


class StatusExecucao(StrEnum):
    EM_ANDAMENTO = "em_andamento"
    SUCESSO = "sucesso"
    COM_PENDENCIAS = "com_pendencias"
    FALHA = "falha"
    DISPENSADA = "dispensada"


class Gatilho(StrEnum):
    AGENDADA = "agendada"
    RESERVA = "reserva"
    MANUAL = "manual"


BEM_SUCEDIDAS = (StatusExecucao.SUCESSO, StatusExecucao.COM_PENDENCIAS)


class ExecucaoNaoEmAndamento(Exception):
    """A execução não existe ou já foi finalizada: só em_andamento muda de status."""


@dataclass(frozen=True)
class Execucao:
    id: int
    iniciada_em: datetime
    terminada_em: datetime | None
    status: StatusExecucao
    gatilho: Gatilho


class Execucoes:
    def __init__(self, banco: Banco) -> None:
        self._banco = banco
        self._tabela = banco.tabelas["execucao_etl"]

    def iniciar(self, gatilho: Gatilho, versao_codigo: str) -> int:
        with self._banco.engine.begin() as conexao:
            return conexao.execute(
                self._tabela.insert()
                .values(gatilho=gatilho.value, versao_codigo=versao_codigo)
                .returning(self._tabela.c.id)
            ).scalar_one()

    def finalizar(
        self,
        execucao_id: int,
        status: StatusExecucao,
        *,
        contagens: dict[str, Any] | None = None,
        tentativas: list[Any] | None = None,
        erros: list[Any] | None = None,
        pendencias: list[Any] | None = None,
    ) -> None:
        if status is StatusExecucao.EM_ANDAMENTO:
            raise ValueError("finalizar exige um status final, não em_andamento")

        detalhes = {
            nome: valor
            for nome, valor in (
                ("contagens", contagens),
                ("tentativas", tentativas),
                ("erros", erros),
                ("pendencias", pendencias),
            )
            if valor is not None
        }
        with self._banco.engine.begin() as conexao:
            alteradas = conexao.execute(
                self._tabela.update()
                .where(
                    self._tabela.c.id == execucao_id,
                    self._tabela.c.status == StatusExecucao.EM_ANDAMENTO.value,
                )
                .values(status=status.value, terminada_em=func.now(), **detalhes)
            ).rowcount
        if alteradas != 1:
            raise ExecucaoNaoEmAndamento(f"execução {execucao_id} não está em andamento")

    def ultima_bem_sucedida(self) -> Execucao | None:
        """A mais recente com sucesso ou com_pendencias: é a que o site publica."""
        t = self._tabela
        consulta = (
            select(t.c.id, t.c.iniciada_em, t.c.terminada_em, t.c.status, t.c.gatilho)
            .where(t.c.status.in_([status.value for status in BEM_SUCEDIDAS]))
            .order_by(t.c.iniciada_em.desc(), t.c.id.desc())
            .limit(1)
        )
        with self._banco.engine.connect() as conexao:
            linha = conexao.execute(consulta).first()
        if linha is None:
            return None
        return Execucao(
            id=linha.id,
            iniciada_em=linha.iniciada_em,
            terminada_em=linha.terminada_em,
            status=StatusExecucao(linha.status),
            gatilho=Gatilho(linha.gatilho),
        )
