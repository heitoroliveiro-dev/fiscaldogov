"""Invariantes garantidas pelo banco (specs/001-fundacao-tecnica/data-model.md).

Cada recusa confere o SQLSTATE da violação esperada, para que um erro de
preparação (NOT NULL, chave estrangeira) não passe por invariante cumprida.
Os casos aceitos protegem contra uma restrição mais apertada que a regra.
As permissões dos papéis são testadas em test_papeis.py (US4).
"""

from datetime import UTC, date, datetime

import pytest
from sqlalchemy import Connection, text
from sqlalchemy.exc import IntegrityError

VIOLA_CHECK = "23514"
VIOLA_EXCLUSAO = "23P01"
VIOLA_UNICO = "23505"

FONTE = "https://dadosabertos.camara.leg.br/api/v2/deputados/204496/historico"
COLETADO_EM = datetime(2026, 10, 20, 6, 0, tzinfo=UTC)


def _momento(ano: int, mes: int, dia: int) -> datetime:
    return datetime(ano, mes, dia, tzinfo=UTC)


def _inserir(conexao: Connection, sql: str, **parametros: object) -> int:
    return conexao.execute(text(sql), parametros).scalar_one()


def _recusa(conexao: Connection, sqlstate: str, sql: str, **parametros: object) -> None:
    with pytest.raises(IntegrityError) as erro, conexao.begin_nested():
        conexao.execute(text(sql), parametros)
    assert erro.value.orig is not None
    assert erro.value.orig.sqlstate == sqlstate, erro.value.orig


def _parlamentar(conexao: Connection, nome: str = "Fulano de Tal") -> int:
    return _inserir(
        conexao,
        "INSERT INTO parlamentar (nome_parlamentar, nome_ordenacao, fonte_url, coletado_em) "
        "VALUES (:nome, lower(:nome), :fonte, :coletado_em) RETURNING id",
        nome=nome,
        fonte=FONTE,
        coletado_em=COLETADO_EM,
    )


def _partido(conexao: Connection, sigla: str) -> int:
    return _inserir(
        conexao, "INSERT INTO partido (sigla) VALUES (:sigla) RETURNING id", sigla=sigla
    )


def _mandato(conexao: Connection, parlamentar_id: int) -> int:
    return _inserir(
        conexao,
        "INSERT INTO mandato (parlamentar_id, casa_id, legislatura_numero, uf) "
        "SELECT :parlamentar_id, id, 57, 'SP' FROM casa_legislativa WHERE sigla = 'CD' "
        "RETURNING id",
        parlamentar_id=parlamentar_id,
    )


INSERE_PERIODO = (
    "INSERT INTO periodo_exercicio "
    "(mandato_id, inicio, fim, condicao, motivo_inicio, fonte_url, coletado_em) "
    "VALUES (:mandato_id, :inicio, :fim, 'titular', 'Posse', :fonte, :coletado_em) "
    "RETURNING id"
)

INSERE_FILIACAO = (
    "INSERT INTO filiacao (parlamentar_id, partido_id, inicio, fim, fonte_url, coletado_em) "
    "VALUES (:parlamentar_id, :partido_id, :inicio, :fim, :fonte, :coletado_em) "
    "RETURNING id"
)

INSERE_IDENTIFICADOR = (
    "INSERT INTO identificador_externo (parlamentar_id, partido_id, sistema, valor) "
    "VALUES (:parlamentar_id, :partido_id, :sistema, :valor) "
    "RETURNING id"
)


def _periodo(conexao: Connection, mandato_id: int, inicio: datetime, fim: datetime | None) -> dict:
    return dict(mandato_id=mandato_id, inicio=inicio, fim=fim, fonte=FONTE, coletado_em=COLETADO_EM)


def _filiacao(parlamentar_id: int, partido_id: int, inicio: datetime, fim: datetime | None) -> dict:
    return dict(
        parlamentar_id=parlamentar_id,
        partido_id=partido_id,
        inicio=inicio,
        fim=fim,
        fonte=FONTE,
        coletado_em=COLETADO_EM,
    )


def test_invariante_1_periodo_termina_depois_de_comecar(conexao_dono: Connection) -> None:
    mandato = _mandato(conexao_dono, _parlamentar(conexao_dono))
    posse = _momento(2023, 2, 1)

    _recusa(conexao_dono, VIOLA_CHECK, INSERE_PERIODO, **_periodo(mandato, posse, posse))
    _recusa(
        conexao_dono,
        VIOLA_CHECK,
        INSERE_PERIODO,
        **_periodo(mandato, posse, _momento(2023, 1, 31)),
    )

    # fim nulo = ainda em exercício
    _inserir(conexao_dono, INSERE_PERIODO, **_periodo(mandato, posse, None))


def test_invariante_2_periodos_do_mesmo_mandato_nao_se_sobrepoem(
    conexao_dono: Connection,
) -> None:
    mandato = _mandato(conexao_dono, _parlamentar(conexao_dono))
    licenca = _momento(2023, 6, 1)
    _inserir(conexao_dono, INSERE_PERIODO, **_periodo(mandato, _momento(2023, 2, 1), licenca))

    _recusa(
        conexao_dono,
        VIOLA_EXCLUSAO,
        INSERE_PERIODO,
        **_periodo(mandato, _momento(2023, 5, 1), _momento(2023, 8, 1)),
    )
    # período aberto antes da licença cobre todo o futuro
    _recusa(
        conexao_dono,
        VIOLA_EXCLUSAO,
        INSERE_PERIODO,
        **_periodo(mandato, _momento(2023, 1, 1), None),
    )

    # reassunção no instante exato em que o período anterior terminou
    _inserir(conexao_dono, INSERE_PERIODO, **_periodo(mandato, licenca, None))

    # outro mandato no mesmo intervalo não conflita
    outro = _mandato(conexao_dono, _parlamentar(conexao_dono, "Beltrana"))
    _inserir(conexao_dono, INSERE_PERIODO, **_periodo(outro, _momento(2023, 2, 1), None))


def test_invariante_3_no_maximo_uma_filiacao_aberta(conexao_dono: Connection) -> None:
    parlamentar = _parlamentar(conexao_dono)
    partido_a = _partido(conexao_dono, "AAA")
    partido_b = _partido(conexao_dono, "BBB")
    troca = _momento(2024, 3, 1)

    _inserir(
        conexao_dono,
        INSERE_FILIACAO,
        **_filiacao(parlamentar, partido_a, _momento(2023, 2, 1), troca),
    )
    _inserir(conexao_dono, INSERE_FILIACAO, **_filiacao(parlamentar, partido_b, troca, None))

    _recusa(
        conexao_dono,
        VIOLA_UNICO,
        INSERE_FILIACAO,
        **_filiacao(parlamentar, partido_a, _momento(2025, 1, 1), None),
    )

    # a regra é por parlamentar: outro parlamentar pode ter a sua aberta
    outro = _parlamentar(conexao_dono, "Beltrana")
    _inserir(conexao_dono, INSERE_FILIACAO, **_filiacao(outro, partido_b, troca, None))


def test_invariante_4_identificador_aponta_para_exatamente_uma_entidade(
    conexao_dono: Connection,
) -> None:
    parlamentar = _parlamentar(conexao_dono)
    partido = _partido(conexao_dono, "AAA")

    _recusa(
        conexao_dono,
        VIOLA_CHECK,
        INSERE_IDENTIFICADOR,
        parlamentar_id=None,
        partido_id=None,
        sistema="camara_v2",
        valor="1",
    )
    _recusa(
        conexao_dono,
        VIOLA_CHECK,
        INSERE_IDENTIFICADOR,
        parlamentar_id=parlamentar,
        partido_id=partido,
        sistema="camara_v2",
        valor="2",
    )

    _inserir(
        conexao_dono,
        INSERE_IDENTIFICADOR,
        parlamentar_id=parlamentar,
        partido_id=None,
        sistema="camara_v2",
        valor="204496",
    )
    _inserir(
        conexao_dono,
        INSERE_IDENTIFICADOR,
        parlamentar_id=None,
        partido_id=partido,
        sistema="camara_v2_partido",
        valor="36844",
    )


def test_invariante_5_cargas_fixas_da_migration(conexao_dono: Connection) -> None:
    camara = conexao_dono.execute(
        text("SELECT nome FROM casa_legislativa WHERE sigla = 'CD'")
    ).scalar_one()
    assert camara == "Câmara dos Deputados"

    legislatura = conexao_dono.execute(
        text("SELECT inicio, fim FROM legislatura WHERE numero = 57")
    ).one()
    assert tuple(legislatura) == (date(2023, 2, 1), date(2027, 1, 31))
