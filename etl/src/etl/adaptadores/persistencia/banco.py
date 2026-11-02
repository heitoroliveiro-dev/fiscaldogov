"""Acesso ao Postgres com SQLAlchemy 2 Core (ADR-0001, research §5).

O schema pertence ao Prisma (web/prisma/schema.prisma); o ETL não declara
tabelas, só as reflete. Tabela ausente faz a reflection falhar já na conexão,
antes de qualquer coleta.

O statement_timeout da sessão é o próprio tempo limite da execução: o vigia
(signal.alarm) não interrompe uma chamada bloqueada na libpq, o banco sim.
"""

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass

from sqlalchemy import Connection, Engine, MetaData, Table, create_engine, make_url
from sqlalchemy.exc import OperationalError

from etl.portas import CredencialInvalida

CREDENCIAL = "senha do banco (DATABASE_URL_ESCRITA, papel etl_escrita)"
TEMPO_PARA_CONECTAR_S = 30


def traduzir_erro_de_conexao(erro: BaseException) -> BaseException:
    """Senha recusada vira CredencialInvalida, para o alerta nomear o que renovar (FR-020a)."""
    texto = str(erro)
    if isinstance(erro, OperationalError) and (
        "password authentication failed" in texto
        or ("role " in texto and "does not exist" in texto)
        or "is not permitted to log in" in texto
    ):
        return CredencialInvalida(CREDENCIAL, "autenticação recusada pelo Postgres")
    return erro


TABELAS = (
    "casa_legislativa",
    "legislatura",
    "partido",
    "parlamentar",
    "identificador_externo",
    "mandato",
    "periodo_exercicio",
    "filiacao",
    "execucao_etl",
    "coleta_bruta",
)


@dataclass(frozen=True)
class Banco:
    engine: Engine
    tabelas: Mapping[str, Table]

    @classmethod
    def conectar(cls, url: str, tempo_limite_s: int) -> Banco:
        engine = create_engine(
            make_url(url).set(drivername="postgresql+psycopg"),
            connect_args={
                "options": f"-c statement_timeout={tempo_limite_s * 1000}",
                # sem isto, uma rede travada na conexão não tem limite próprio
                "connect_timeout": TEMPO_PARA_CONECTAR_S,
            },
        )
        metadados = MetaData()
        try:
            metadados.reflect(bind=engine, only=TABELAS)
        except Exception:
            engine.dispose()
            raise
        return cls(engine=engine, tabelas=metadados.tables)

    @contextmanager
    def transacao(self) -> Iterator[Connection]:
        """Unidade de trabalho: uma transação; COMMIT no fim, ROLLBACK em qualquer erro."""
        with self.engine.begin() as conexao:
            yield conexao

    def fechar(self) -> None:
        self.engine.dispose()
