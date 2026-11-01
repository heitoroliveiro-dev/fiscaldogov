"""Contrato schema ↔ ETL (T055, ADR-0001).

O schema pertence ao Prisma; o ETL só reflete as tabelas. Uma coluna renomeada
ou removida numa migration quebraria a coleta em produção, longe do PR que a
causou. Este teste roda depois de `prisma migrate deploy` e falha no próprio PR.

A lista abaixo é explícita de propósito: é o que o código do ETL lê ou grava
(adaptadores de persistência e de brutos). Coluna nova que o ETL passe a usar
entra aqui no mesmo commit.
"""

from collections.abc import Iterator

import pytest

from etl.adaptadores.persistencia.banco import TABELAS, Banco

COLUNAS_USADAS: dict[str, set[str]] = {
    "casa_legislativa": {"id", "sigla"},
    # refletida por ser alvo de chave estrangeira; o ETL não lê nem grava colunas dela
    "legislatura": set(),
    "partido": {"id", "sigla"},
    "parlamentar": {
        "id",
        "nome_parlamentar",
        "nome_ordenacao",
        "url_foto",
        "fonte_url",
        "coletado_em",
    },
    "identificador_externo": {
        "sistema",
        "valor",
        "legislatura_numero",
        "parlamentar_id",
        "partido_id",
    },
    "mandato": {"id", "parlamentar_id", "casa_id", "legislatura_numero", "uf"},
    "periodo_exercicio": {
        "mandato_id",
        "inicio",
        "fim",
        "condicao",
        "motivo_inicio",
        "motivo_fim",
        "fonte_url",
        "coletado_em",
    },
    "filiacao": {"parlamentar_id", "partido_id", "inicio", "fim", "fonte_url", "coletado_em"},
    "execucao_etl": {
        "id",
        "iniciada_em",
        "terminada_em",
        "status",
        "gatilho",
        "versao_codigo",
        "contagens",
        "tentativas",
        "erros",
        "pendencias",
    },
    "coleta_bruta": {
        "id",
        "execucao_id",
        "fonte",
        "url",
        "chave_r2",
        "sha256",
        "bytes",
        "coletada_em",
    },
}


@pytest.fixture(scope="module")
def banco(url_escrita: str) -> Iterator[Banco]:
    # o mesmo caminho da coleta: papel etl_escrita + reflection do adaptador
    banco = Banco.conectar(url_escrita, tempo_limite_s=10)
    yield banco
    banco.fechar()


def test_a_lista_do_contrato_cobre_todas_as_tabelas_refletidas() -> None:
    assert set(COLUNAS_USADAS) == set(TABELAS)


def test_toda_coluna_usada_pelo_etl_existe_no_schema(banco: Banco) -> None:
    faltando = {
        tabela: sorted(colunas - set(banco.tabelas[tabela].c.keys()))
        for tabela, colunas in COLUNAS_USADAS.items()
    }
    assert {tabela: cols for tabela, cols in faltando.items() if cols} == {}
