"""Registro de cada execução em execucao_etl (FR-010, data-model.md).

Cada operação abre a própria transação, separada da que grava a coleta: o
início e o desfecho de uma execução com falha continuam registrados depois do
ROLLBACK dos dados (FR-012).
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import exists, func, select

from etl.adaptadores.persistencia.banco import Banco
from etl.portas import Abertura, ColetaEmAndamento, Gatilho, StatusExecucao

__all__ = ["ExecucaoNaoEmAndamento", "Execucao", "Execucoes", "Gatilho", "StatusExecucao"]


BEM_SUCEDIDAS = (StatusExecucao.SUCESSO, StatusExecucao.COM_PENDENCIAS)
# em_andamento mais antiga que isto é de um processo que morreu sem registrar o fim (FR-013a)
VIDA_MAXIMA = timedelta(minutes=60)
# chave do pg_advisory_xact_lock que serializa o início das coletas; não exige privilégio
TRAVA_DO_INICIO = 4_701_001
INTERROMPIDA = [{"etapa": "vigia", "tipo": "interrompida"}]


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

    def abrir(self, gatilho: Gatilho, versao_codigo: str) -> Abertura:
        t = self._tabela
        with self._banco.engine.begin() as conexao:
            conexao.execute(select(func.pg_advisory_xact_lock(TRAVA_DO_INICIO)))
            interrompidas = conexao.execute(
                t.update()
                .where(
                    t.c.status == StatusExecucao.EM_ANDAMENTO.value,
                    t.c.iniciada_em < func.now() - VIDA_MAXIMA,
                )
                .values(
                    status=StatusExecucao.FALHA.value, terminada_em=func.now(), erros=INTERROMPIDA
                )
                .returning(t.c.id)
            ).scalars()
            interrompidas = tuple(sorted(interrompidas))
            viva = conexao.execute(
                select(t.c.id).where(t.c.status == StatusExecucao.EM_ANDAMENTO.value).limit(1)
            ).scalar_one_or_none()
            execucao_id = None
            if viva is None:
                execucao_id = conexao.execute(
                    t.insert()
                    .values(gatilho=gatilho.value, versao_codigo=versao_codigo)
                    .returning(t.c.id)
                ).scalar_one()
        # levanta só depois do COMMIT: as travadas ficam fechadas mesmo quando esta é recusada
        if execucao_id is None:
            raise ColetaEmAndamento(f"já há uma coleta em andamento (execução {viva})")
        return Abertura(execucao_id, interrompidas)

    def houve_bem_sucedida_desde(self, momento: datetime) -> bool:
        t = self._tabela
        consulta = select(
            exists().where(
                t.c.status.in_([status.value for status in BEM_SUCEDIDAS]),
                t.c.iniciada_em >= momento,
            )
        )
        with self._banco.engine.connect() as conexao:
            return conexao.execute(consulta).scalar_one()

    def registrar_dispensada(self, versao_codigo: str) -> int:
        with self._banco.engine.begin() as conexao:
            return conexao.execute(
                self._tabela.insert()
                .values(
                    gatilho=Gatilho.RESERVA.value,
                    status=StatusExecucao.DISPENSADA.value,
                    terminada_em=func.now(),
                    versao_codigo=versao_codigo,
                )
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
