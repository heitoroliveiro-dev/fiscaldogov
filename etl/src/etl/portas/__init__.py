"""Portas: o que o pipeline espera de cada adaptador (ADR-0003, typing.Protocol).

O pipeline depende destas interfaces, não das implementações; os erros das
fontes também moram aqui, para que o pipeline os trate sem conhecer a Câmara.
"""

from typing import Protocol

from etl.dominio.entidades import Historico, IdentificadorExterno, Parlamentar


class FonteIncompleta(Exception):
    """A fonte respondeu, mas com menos do que o mínimo plausível: nada é gravado (FR-007b)."""


class RespostaInvalida(Exception):
    """JSON inválido, ou campo usado ausente ou de tipo inesperado: falha fechada."""


class FonteDaCasa(Protocol):
    def listar_em_exercicio(self) -> list[Parlamentar]: ...

    def historico(self, parlamentar: IdentificadorExterno) -> Historico: ...
