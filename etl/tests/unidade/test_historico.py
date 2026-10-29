"""Derivação de períodos de exercício, filiações e UF a partir do histórico (data-model.md).

Base do futuro denominador das estatísticas (DA03): erro aqui vira taxa errada.
Os casos com a fixture real (deputado 204496, 22 eventos, 17 da 57ª) foram
conferidos à mão evento a evento; os sintéticos cobrem as bordas que ela não tem.
"""

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from etl.dominio.entidades import (
    Condicao,
    EventoHistorico,
    Filiacao,
    IdentificadorExterno,
    Partido,
    PeriodoDeExercicio,
    SistemaExterno,
)
from etl.dominio.historico import derivar_filiacoes, derivar_periodos, derivar_uf

FIXTURE = Path(__file__).parents[1] / "fixtures" / "camara" / "historico-204496-2026-10-28.json"
BRASILIA = ZoneInfo("America/Sao_Paulo")
LEGISLATURA = 57

POSSE = "Entrada - Posse de Eleito Titular - Posse na Sessão Preparatória"
REASSUNCAO = "Entrada - Reassunção"
MINISTRO = "Saída - Afastamento sem prazo determinado - Ministro de Estado"


def _momento(texto: str) -> datetime:
    return datetime.fromisoformat(texto).replace(tzinfo=BRASILIA)


def _partido(sigla: str, valor: str) -> Partido:
    return Partido(sigla, IdentificadorExterno(SistemaExterno.CAMARA_V2_PARTIDO, valor))


UNIAO = _partido("UNIÃO", "38009")
PDT = _partido("PDT", "36786")


def _evento_da_fonte(bruto: dict) -> EventoHistorico:
    # A mesma tradução que o adaptador da Câmara fará (T036), só para alimentar
    # o domínio aqui: o domínio não conhece o formato da API (DA02).
    situacao = bruto["situacao"]
    condicao = bruto["condicaoEleitoral"]
    sigla = bruto["siglaPartido"]
    return EventoHistorico(
        data_hora=_momento(bruto["dataHora"]),
        legislatura=bruto["idLegislatura"],
        em_exercicio=None if situacao is None else situacao == "Exercício",
        condicao=None if condicao is None else Condicao(condicao.lower()),
        partido=None
        if sigla == "S.PART."
        else _partido(sigla, bruto["uriPartido"].rsplit("/")[-1]),
        uf=bruto["siglaUf"],
        descricao=bruto["descricaoStatus"],
    )


@pytest.fixture(scope="module")
def eventos_204496() -> list[EventoHistorico]:
    dados = json.loads(FIXTURE.read_text(encoding="utf-8"))["dados"]
    return [_evento_da_fonte(bruto) for bruto in dados]


def _evento(
    momento: str,
    em_exercicio: bool | None = True,
    partido: Partido | None = UNIAO,
    condicao: Condicao | None = Condicao.TITULAR,
    descricao: str = "",
    legislatura: int = LEGISLATURA,
    uf: str = "PA",
) -> EventoHistorico:
    return EventoHistorico(
        data_hora=_momento(momento),
        legislatura=legislatura,
        em_exercicio=em_exercicio,
        condicao=condicao,
        partido=partido,
        uf=uf,
        descricao=descricao,
    )


def _intervalos(itens: list) -> list[tuple[datetime, datetime | None]]:
    return [(item.inicio, item.fim) for item in itens]


# --- fixture real -------------------------------------------------------------


def test_fixture_tem_os_22_eventos_conferidos(eventos_204496: list[EventoHistorico]) -> None:
    assert len(eventos_204496) == 22
    assert sum(evento.legislatura == LEGISLATURA for evento in eventos_204496) == 17


def test_periodos_abrem_no_exercicio_e_fecham_na_licenca(
    eventos_204496: list[EventoHistorico],
) -> None:
    periodos = derivar_periodos(eventos_204496, LEGISLATURA)

    assert _intervalos(periodos) == [
        (_momento("2023-02-01T12:05"), _momento("2023-07-18T00:00")),
        (_momento("2023-11-30T09:17"), _momento("2023-12-06T00:00")),
        (_momento("2024-12-03T12:38"), _momento("2024-12-06T17:00")),
        (_momento("2025-02-01T08:43"), _momento("2025-02-03T13:17")),
        (_momento("2025-10-08T17:58"), _momento("2025-10-09T14:54")),
        (_momento("2025-11-13T09:55"), _momento("2025-11-17T19:36")),
        # as trocas de partido de abril/2026 seguem em exercício: não fecham o período
        (_momento("2025-12-19T14:51"), None),
    ]


def test_periodos_levam_condicao_e_motivos(eventos_204496: list[EventoHistorico]) -> None:
    periodos = derivar_periodos(eventos_204496, LEGISLATURA)

    assert periodos[0] == PeriodoDeExercicio(
        inicio=_momento("2023-02-01T12:05"),
        fim=_momento("2023-07-18T00:00"),
        condicao=Condicao.TITULAR,
        motivo_inicio=POSSE,
        motivo_fim=MINISTRO,
    )
    assert periodos[1].motivo_inicio == REASSUNCAO
    assert periodos[-1].motivo_fim is None
    assert {periodo.condicao for periodo in periodos} == {Condicao.TITULAR}


def test_filiacao_inicial_vem_do_evento_de_inicio_da_legislatura(
    eventos_204496: list[EventoHistorico],
) -> None:
    filiacoes = derivar_filiacoes(eventos_204496, LEGISLATURA)

    assert filiacoes == [
        # "Partido no início da legislatura", com situação nula, às 00:00 de 01/02/2023
        Filiacao(
            partido=UNIAO, inicio=_momento("2023-02-01T00:00"), fim=_momento("2026-04-17T20:00")
        ),
        # o segundo evento com PDT (23/04) repete a sigla: não abre outra filiação
        Filiacao(partido=PDT, inicio=_momento("2026-04-17T20:00"), fim=None),
    ]


def test_uf_vem_do_primeiro_evento_da_legislatura(eventos_204496: list[EventoHistorico]) -> None:
    assert derivar_uf(eventos_204496, LEGISLATURA) == "PA"


def test_eventos_de_outras_legislaturas_nao_entram(eventos_204496: list[EventoHistorico]) -> None:
    # os 5 eventos da 56ª trazem PSDB, S.PART. e PSL e começam em 2019
    inicio_da_57 = _momento("2023-02-01T00:00")

    periodos = derivar_periodos(eventos_204496, LEGISLATURA)
    filiacoes = derivar_filiacoes(eventos_204496, LEGISLATURA)

    assert all(periodo.inicio >= inicio_da_57 for periodo in periodos)
    assert {filiacao.partido.sigla for filiacao in filiacoes} == {"UNIÃO", "PDT"}


def test_ordem_da_fonte_nao_muda_o_resultado(eventos_204496: list[EventoHistorico]) -> None:
    invertidos = list(reversed(eventos_204496))

    assert derivar_periodos(invertidos, LEGISLATURA) == derivar_periodos(
        eventos_204496, LEGISLATURA
    )
    assert derivar_filiacoes(invertidos, LEGISLATURA) == derivar_filiacoes(
        eventos_204496, LEGISLATURA
    )


# --- bordas sintéticas --------------------------------------------------------


def test_empate_de_data_hora_mantem_a_ordem_da_fonte() -> None:
    # saída e reentrada no mesmo minuto: a ordem da fonte decide (FR-007b)
    eventos = [
        _evento("2023-02-01T12:00"),
        _evento("2023-05-10T10:00", em_exercicio=False, descricao="Saída"),
        _evento("2023-05-10T10:00", descricao="Entrada"),
    ]

    assert _intervalos(derivar_periodos(eventos, LEGISLATURA)) == [
        (_momento("2023-02-01T12:00"), _momento("2023-05-10T10:00")),
        (_momento("2023-05-10T10:00"), None),
    ]


def test_evento_sem_situacao_nao_abre_nem_fecha_periodo() -> None:
    eventos = [
        _evento("2023-02-01T00:00", em_exercicio=None, condicao=None),
        _evento("2023-02-01T12:00"),
        _evento("2023-03-01T00:00", em_exercicio=None, condicao=None),
    ]

    assert _intervalos(derivar_periodos(eventos, LEGISLATURA)) == [
        (_momento("2023-02-01T12:00"), None)
    ]


def test_condicao_vem_do_evento_que_abre_o_periodo() -> None:
    eventos = [_evento("2023-04-01T12:00", condicao=Condicao.SUPLENTE)]

    assert derivar_periodos(eventos, LEGISLATURA)[0].condicao is Condicao.SUPLENTE


def test_sem_partido_fecha_a_filiacao_sem_abrir_outra() -> None:
    eventos = [
        _evento("2023-02-01T00:00", em_exercicio=None, condicao=None),
        _evento("2023-02-01T12:00"),
        _evento("2023-09-09T18:10", partido=None),
        _evento("2023-09-22T14:42", partido=PDT),
    ]

    assert derivar_filiacoes(eventos, LEGISLATURA) == [
        Filiacao(
            partido=UNIAO, inicio=_momento("2023-02-01T00:00"), fim=_momento("2023-09-09T18:10")
        ),
        Filiacao(partido=PDT, inicio=_momento("2023-09-22T14:42"), fim=None),
    ]


def test_sem_partido_no_fim_deixa_nenhuma_filiacao_aberta() -> None:
    eventos = [_evento("2023-02-01T12:00"), _evento("2023-09-09T18:10", partido=None)]

    filiacoes = derivar_filiacoes(eventos, LEGISLATURA)

    assert [filiacao.fim for filiacao in filiacoes] == [_momento("2023-09-09T18:10")]


def test_legislatura_sem_eventos_e_recusada() -> None:
    eventos = [_evento("2019-02-01T12:00", legislatura=56)]

    with pytest.raises(ValueError, match="57"):
        derivar_uf(eventos, LEGISLATURA)
