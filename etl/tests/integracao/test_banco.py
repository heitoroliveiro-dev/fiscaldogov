"""Adaptador de banco: reflection, unidade de trabalho e statement_timeout (T017).

Os testes usam o papel etl_escrita, o mesmo da coleta. Os que confirmam o
COMMIT apagam o que gravaram, porque aqui a transação é a do próprio adaptador.
"""

from collections.abc import Iterator

import pytest
from sqlalchemy import delete, select
from sqlalchemy.exc import OperationalError

from etl.adaptadores.persistencia.banco import TABELAS, Banco

CONSULTA_CANCELADA = "57014"


@pytest.fixture
def banco(url_escrita: str) -> Iterator[Banco]:
    banco = Banco.conectar(url_escrita, tempo_limite_s=2)
    yield banco
    banco.fechar()


def _partido_existe(banco: Banco, sigla: str) -> bool:
    partido = banco.tabelas["partido"]
    with banco.transacao() as conexao:
        linha = conexao.execute(select(partido.c.id).where(partido.c.sigla == sigla)).first()
    return linha is not None


def test_reflection_encontra_as_tabelas_da_fundacao(banco: Banco) -> None:
    assert set(banco.tabelas) == set(TABELAS)
    assert len(TABELAS) == 10
    assert {"status", "gatilho", "contagens", "versao_codigo"} <= set(
        banco.tabelas["execucao_etl"].c.keys()
    )


def test_statement_timeout_da_sessao_vem_do_tempo_limite(banco: Banco) -> None:
    with banco.transacao() as conexao:
        assert conexao.exec_driver_sql("SHOW statement_timeout").scalar_one() == "2s"


def test_consulta_que_passa_do_tempo_limite_e_cancelada_pelo_banco(url_escrita: str) -> None:
    # o vigia (signal.alarm) não interrompe uma chamada bloqueada na libpq;
    # o statement_timeout garante que o banco a cancele
    banco = Banco.conectar(url_escrita, tempo_limite_s=1)
    try:
        with pytest.raises(OperationalError) as erro, banco.transacao() as conexao:
            conexao.exec_driver_sql("SELECT pg_sleep(3)")
        assert erro.value.orig is not None
        assert erro.value.orig.sqlstate == CONSULTA_CANCELADA
    finally:
        banco.fechar()


def test_erro_na_unidade_de_trabalho_desfaz_tudo(banco: Banco) -> None:
    partido = banco.tabelas["partido"]
    with pytest.raises(RuntimeError), banco.transacao() as conexao:
        conexao.execute(partido.insert().values(sigla="T017-ROLLBACK"))
        raise RuntimeError("falha no meio da gravação")

    assert not _partido_existe(banco, "T017-ROLLBACK")


def test_unidade_de_trabalho_sem_erro_confirma(banco: Banco) -> None:
    partido = banco.tabelas["partido"]
    try:
        with banco.transacao() as conexao:
            conexao.execute(partido.insert().values(sigla="T017-COMMIT"))
        assert _partido_existe(banco, "T017-COMMIT")
    finally:
        with banco.transacao() as conexao:
            conexao.execute(delete(partido).where(partido.c.sigla == "T017-COMMIT"))
