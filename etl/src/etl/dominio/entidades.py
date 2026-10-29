"""Entidades do domínio (ADR-0003 §2–3, data-model.md).

Imutáveis e sem I/O. Os adaptadores traduzem o formato de cada fonte para
estes tipos; o domínio nunca vê um JSON da Câmara (DA02).
"""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from etl.dominio.selecao import normalizar_nome


class SistemaExterno(StrEnum):
    CAMARA_V2 = "camara_v2"
    CAMARA_V2_PARTIDO = "camara_v2_partido"


class Condicao(StrEnum):
    TITULAR = "titular"
    SUPLENTE = "suplente"


@dataclass(frozen=True)
class IdentificadorExterno:
    """Identificador de um registro numa fonte; a chave própria é do banco."""

    sistema: SistemaExterno
    valor: str
    legislatura: int | None = None


@dataclass(frozen=True)
class Partido:
    sigla: str
    identificador: IdentificadorExterno


@dataclass(frozen=True)
class Origem:
    """De onde e quando veio um dado: todo registro exibido é rastreável (princípio I)."""

    url: str
    coletado_em: datetime


@dataclass(frozen=True)
class Parlamentar:
    nome_parlamentar: str
    identificador: IdentificadorExterno
    origem: Origem
    url_foto: str | None = None

    @property
    def nome_ordenacao(self) -> str:
        return normalizar_nome(self.nome_parlamentar)


@dataclass(frozen=True)
class Mandato:
    """Parlamentar × casa × legislatura × UF."""

    casa: str
    legislatura: int
    uf: str


@dataclass(frozen=True)
class PeriodoDeExercicio:
    """Intervalo em exercício; fim nulo = em exercício agora. Base do denominador (DA03)."""

    inicio: datetime
    fim: datetime | None
    condicao: Condicao
    motivo_inicio: str
    motivo_fim: str | None


@dataclass(frozen=True)
class Filiacao:
    """Partido num intervalo; a filiação sem fim é o partido atual (RN01)."""

    partido: Partido
    inicio: datetime
    fim: datetime | None


@dataclass(frozen=True)
class EventoHistorico:
    """Um evento do histórico do parlamentar, já traduzido pelo adaptador.

    em_exercicio é None num evento que só registra nome ou partido (como o de
    início da legislatura): ele não abre nem fecha período. partido é None quando
    o parlamentar está sem partido.
    """

    data_hora: datetime
    legislatura: int
    em_exercicio: bool | None
    condicao: Condicao | None
    partido: Partido | None
    uf: str
    descricao: str


@dataclass(frozen=True)
class Historico:
    """Todos os eventos do histórico de um parlamentar, na ordem da fonte."""

    eventos: tuple[EventoHistorico, ...]
    origem: Origem
