"""Acesso separado: só a coleta escreve, e ninguém além do dono altera a estrutura (T059).

FR-019, SC-005 e princípio V. As permissões vêm da migration 0001_fundacao.
Cada recusa confere o SQLSTATE 42501 (insufficient_privilege) E o objeto que
recusou: o mesmo SQLSTATE aparece para a sequência do id, então um GRANT de
INSERT na tabela passaria despercebido se o teste olhasse só o código. Os
casos aceitos protegem contra um GRANT mais apertado que a regra.
"""

import pytest
from sqlalchemy import Connection, text
from sqlalchemy.exc import DBAPIError

SEM_PRIVILEGIO = "42501"
NA_TABELA = "permission denied for table partido"
NO_SCHEMA = "permission denied for schema public"
SO_O_DONO = "must be owner of table partido"

ESCRITAS = {
    "insert": ("INSERT INTO partido (sigla) VALUES ('PAPEL')", NA_TABELA),
    "update": ("UPDATE partido SET sigla = sigla", NA_TABELA),
    "delete": ("DELETE FROM partido", NA_TABELA),
}

ESTRUTURA = {
    "create_table": ("CREATE TABLE papel_intruso (id int)", NO_SCHEMA),
    "drop_table": ("DROP TABLE partido", SO_O_DONO),
    "alter_table": ("ALTER TABLE partido ADD COLUMN intrusa int", SO_O_DONO),
    "truncate": ("TRUNCATE partido CASCADE", NA_TABELA),
}


def _recusa(conexao: Connection, sql: str, mensagem: str) -> None:
    with pytest.raises(DBAPIError) as erro, conexao.begin_nested():
        conexao.execute(text(sql))
    original = erro.value.orig
    assert original is not None
    assert (original.sqlstate, original.diag.message_primary) == (SEM_PRIVILEGIO, mensagem)


@pytest.mark.parametrize(
    ("sql", "mensagem"), [*ESCRITAS.values(), *ESTRUTURA.values()], ids=[*ESCRITAS, *ESTRUTURA]
)
def test_site_leitura_nao_escreve_nem_altera_a_estrutura(
    conexao_leitura: Connection, sql: str, mensagem: str
) -> None:
    _recusa(conexao_leitura, sql, mensagem)


def test_site_leitura_le(conexao_leitura: Connection) -> None:
    assert conexao_leitura.execute(text("SELECT count(*) FROM parlamentar")).scalar_one() >= 0
    assert conexao_leitura.execute(text("SELECT count(*) FROM execucao_etl")).scalar_one() >= 0


@pytest.mark.parametrize(("sql", "mensagem"), ESTRUTURA.values(), ids=ESTRUTURA)
def test_etl_escrita_nao_altera_a_estrutura(
    conexao_escrita: Connection, sql: str, mensagem: str
) -> None:
    _recusa(conexao_escrita, sql, mensagem)


def test_etl_escrita_insere_atualiza_e_apaga(conexao_escrita: Connection) -> None:
    partido_id = conexao_escrita.execute(
        text("INSERT INTO partido (sigla) VALUES ('PAPEL') RETURNING id")
    ).scalar_one()

    atualizadas = conexao_escrita.execute(
        text("UPDATE partido SET sigla = 'PAPEL2' WHERE id = :id"), {"id": partido_id}
    ).rowcount
    apagadas = conexao_escrita.execute(
        text("DELETE FROM partido WHERE id = :id"), {"id": partido_id}
    ).rowcount

    assert (atualizadas, apagadas) == (1, 1)
