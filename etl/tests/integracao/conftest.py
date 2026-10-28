"""Conexões de teste com o Postgres, uma por papel (contracts/ambientes-e-segredos.md).

Cada teste recebe uma conexão dentro de uma transação que é desfeita ao fim,
então nenhum teste deixa dado para o seguinte.

Sem as variáveis de banco, os testes daqui são pulados com mensagem clara. Com
ETL_EXIGIR_INTEGRACAO=1 (o CI define), variável ausente é erro, nunca pulo:
um teste mascarado não pode passar por verde (constituição, princípio III).
"""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import Connection, Engine, create_engine, make_url

_PASTA = Path(__file__).parent


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    # Todo teste desta pasta precisa do banco; o marcador permite filtrar com -m.
    for item in items:
        if _PASTA in item.path.parents:
            item.add_marker(pytest.mark.integration)


def _url_do_ambiente(variavel: str) -> str:
    url = os.environ.get(variavel)
    if not url:
        mensagem = (
            f"{variavel} não definida: teste de integração precisa de Postgres com as "
            "migrations aplicadas (ver etl/.env.example)"
        )
        if os.environ.get("ETL_EXIGIR_INTEGRACAO") == "1":
            pytest.fail(f"{mensagem}. ETL_EXIGIR_INTEGRACAO=1 proíbe pular.", pytrace=False)
        pytest.skip(mensagem)
    return url


def _engine_do_ambiente(variavel: str) -> Iterator[Engine]:
    url = _url_do_ambiente(variavel)
    engine = create_engine(make_url(url).set(drivername="postgresql+psycopg"))
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def url_escrita() -> str:
    """URL do papel etl_escrita, para testar o próprio adaptador de banco."""
    return _url_do_ambiente("DATABASE_URL_ESCRITA_TESTE")


def _conexao_com_rollback(engine: Engine) -> Iterator[Connection]:
    with engine.connect() as conexao:
        transacao = conexao.begin()
        try:
            yield conexao
        finally:
            transacao.rollback()


@pytest.fixture(scope="session")
def engine_dono() -> Iterator[Engine]:
    yield from _engine_do_ambiente("DATABASE_URL_TESTE")


@pytest.fixture(scope="session")
def engine_escrita() -> Iterator[Engine]:
    yield from _engine_do_ambiente("DATABASE_URL_ESCRITA_TESTE")


@pytest.fixture(scope="session")
def engine_leitura() -> Iterator[Engine]:
    yield from _engine_do_ambiente("DATABASE_URL_LEITURA_TESTE")


@pytest.fixture
def conexao_dono(engine_dono: Engine) -> Iterator[Connection]:
    """Papel dono do schema (o mesmo que aplica as migrations)."""
    yield from _conexao_com_rollback(engine_dono)


@pytest.fixture
def conexao_escrita(engine_escrita: Engine) -> Iterator[Connection]:
    """Papel etl_escrita: o que a coleta usa."""
    yield from _conexao_com_rollback(engine_escrita)


@pytest.fixture
def conexao_leitura(engine_leitura: Engine) -> Iterator[Connection]:
    """Papel site_leitura: o que o build do site usa."""
    yield from _conexao_com_rollback(engine_leitura)
