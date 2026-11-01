"""Apoio dos testes de integração da coleta da US2 (concorrência, tempo limite, falha da fonte).

A coleta grava de verdade (COMMIT), então o banco é limpo no fim: apaga, tabela
a tabela, só as linhas com id maior que o último existente antes do teste.
"""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import func, select, text

from etl.adaptadores.brutos_r2.armazem import ArmazemDeBrutos, GravadorEmDisco
from etl.adaptadores.persistencia.banco import Banco
from etl.adaptadores.persistencia.execucoes import Execucoes
from etl.adaptadores.persistencia.repositorio import Repositorio
from etl.dominio.entidades import (
    Condicao,
    EventoHistorico,
    Historico,
    IdentificadorExterno,
    Origem,
    Parlamentar,
    Partido,
    SistemaExterno,
)
from etl.pipeline.coletar import Coleta
from etl.portas import FonteDaCasa

# ordem de apagar: dependentes antes
TABELAS_DA_COLETA = (
    "coleta_bruta",
    "execucao_etl",
    "periodo_exercicio",
    "filiacao",
    "mandato",
    "identificador_externo",
    "parlamentar",
    "partido",
)
BASE = "https://dadosabertos.camara.leg.br/api/v2"
AGORA = datetime(2026, 11, 2, 6, 0, tzinfo=UTC)
CELSO = Parlamentar(
    "Celso Sabino",
    IdentificadorExterno(SistemaExterno.CAMARA_V2, "204496"),
    Origem(f"{BASE}/deputados?itens=100&pagina=1", AGORA),
)

PDT = Partido("PDT", IdentificadorExterno(SistemaExterno.CAMARA_V2_PARTIDO, "36786"))
HISTORICO = Historico(
    eventos=(
        EventoHistorico(
            data_hora=datetime(2023, 2, 1, 15, 0, tzinfo=UTC),
            legislatura=57,
            em_exercicio=True,
            condicao=Condicao.TITULAR,
            partido=PDT,
            uf="PA",
            descricao="Entrada",
        ),
    ),
    origem=Origem(f"{BASE}/deputados/204496/historico", datetime(2026, 11, 2, 6, tzinfo=UTC)),
)


@contextmanager
def banco_limpo(url_escrita: str, tempo_limite_s: int = 30) -> Iterator[Banco]:
    banco = Banco.conectar(url_escrita, tempo_limite_s)
    with banco.transacao() as conexao:
        ultimos = {
            nome: conexao.execute(
                select(func.coalesce(func.max(banco.tabelas[nome].c.id), 0))
            ).scalar_one()
            for nome in TABELAS_DA_COLETA
        }
    try:
        yield banco
    finally:
        with banco.transacao() as conexao:
            for nome in TABELAS_DA_COLETA:
                tabela = banco.tabelas[nome]
                conexao.execute(tabela.delete().where(tabela.c.id > ultimos[nome]))
        banco.fechar()


class PublicadorFalso:
    def __init__(self) -> None:
        self.disparos: list[int] = []

    def disparar(self, execucao_id: int) -> None:
        self.disparos.append(execucao_id)


class BackupFalso:
    def __init__(self) -> None:
        self.copias = 0

    def copiar(self) -> list[str]:
        self.copias += 1
        return ["diario/teste.dump"]


class AlertadorFalso:
    def __init__(self, falhar: bool = False) -> None:
        self.textos: list[str] = []
        self._falhar = falhar

    def alertar(self, texto: str) -> None:
        self.textos.append(texto)
        if self._falhar:
            raise ConnectionError("Telegram fora do ar")


def montar_coleta(
    banco: Banco,
    pasta: Path,
    criar_fonte: Callable[[Callable[[str, Any], None], Callable[[dict], None]], FonteDaCasa],
    *,
    alertador: Any = None,
    publicador: Any = None,
    tempo_limite_s: int = 3600,
) -> Coleta:
    return Coleta(
        criar_fonte=criar_fonte,
        repositorio=Repositorio(banco),
        brutos=ArmazemDeBrutos(banco, GravadorEmDisco(pasta)),
        execucoes=Execucoes(banco),
        backup=BackupFalso(),
        publicador=publicador or PublicadorFalso(),
        alertador=alertador or AlertadorFalso(),
        versao_codigo="teste",
        tempo_limite_s=tempo_limite_s,
    )


def contar(banco: Banco, tabela: str) -> int:
    with banco.transacao() as conexao:
        return conexao.execute(select(func.count()).select_from(banco.tabelas[tabela])).scalar_one()


def linhas(banco: Banco, sql: str, **parametros: object) -> list:
    with banco.transacao() as conexao:
        return list(conexao.execute(text(sql), parametros))
