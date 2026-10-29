"""Derivação de períodos de exercício, filiações e UF a partir do histórico (data-model.md).

Funções puras. Só os eventos da legislatura pedida entram (decisão de
2026-10-28: o M1 cobre a 57ª). Os eventos são ordenados por data e hora antes da
derivação; no empate, vale a ordem da fonte (FR-007b).
"""

from collections.abc import Iterable

from etl.dominio.entidades import (
    Condicao,
    EventoHistorico,
    Filiacao,
    Partido,
    PeriodoDeExercicio,
)


def _da_legislatura(eventos: Iterable[EventoHistorico], legislatura: int) -> list[EventoHistorico]:
    # sorted é estável: eventos com a mesma data e hora mantêm a ordem da fonte
    return sorted(
        (evento for evento in eventos if evento.legislatura == legislatura),
        key=lambda evento: evento.data_hora,
    )


def derivar_periodos(
    eventos: Iterable[EventoHistorico], legislatura: int
) -> list[PeriodoDeExercicio]:
    """Abre num evento em exercício e fecha no próximo evento fora de exercício."""
    periodos: list[PeriodoDeExercicio] = []
    entrada: tuple[EventoHistorico, Condicao] | None = None
    for evento in _da_legislatura(eventos, legislatura):
        if evento.em_exercicio is True and entrada is None:
            if evento.condicao is None:
                raise ValueError(f"evento em exercício sem condição em {evento.data_hora}")
            entrada = (evento, evento.condicao)
        elif evento.em_exercicio is False and entrada is not None:
            periodos.append(_periodo(*entrada, saida=evento))
            entrada = None
    if entrada is not None:
        periodos.append(_periodo(*entrada, saida=None))
    return periodos


def _periodo(
    entrada: EventoHistorico, condicao: Condicao, saida: EventoHistorico | None
) -> PeriodoDeExercicio:
    return PeriodoDeExercicio(
        inicio=entrada.data_hora,
        fim=saida.data_hora if saida else None,
        condicao=condicao,
        motivo_inicio=entrada.descricao,
        motivo_fim=saida.descricao if saida else None,
    )


def derivar_filiacoes(eventos: Iterable[EventoHistorico], legislatura: int) -> list[Filiacao]:
    """Abre quando o partido muda; evento sem partido fecha a filiação sem abrir outra."""
    filiacoes: list[Filiacao] = []
    atual: tuple[Partido, EventoHistorico] | None = None
    for evento in _da_legislatura(eventos, legislatura):
        if evento.partido == (atual[0] if atual else None):
            continue
        if atual is not None:
            partido, inicio = atual
            filiacoes.append(Filiacao(partido, inicio.data_hora, fim=evento.data_hora))
        atual = (evento.partido, evento) if evento.partido is not None else None
    if atual is not None:
        partido, inicio = atual
        filiacoes.append(Filiacao(partido, inicio.data_hora, fim=None))
    return filiacoes


def derivar_uf(eventos: Iterable[EventoHistorico], legislatura: int) -> str:
    da_legislatura = _da_legislatura(eventos, legislatura)
    if not da_legislatura:
        raise ValueError(f"nenhum evento da {legislatura}ª legislatura no histórico")
    return da_legislatura[0].uf
