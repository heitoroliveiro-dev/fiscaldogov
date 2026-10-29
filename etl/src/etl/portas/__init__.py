"""Portas: o que o pipeline espera de cada adaptador (ADR-0003, typing.Protocol).

O pipeline depende destas interfaces, não das implementações; os erros das
fontes e os estados de uma execução também moram aqui, para que o pipeline os
trate sem conhecer a Câmara nem o banco.
"""

from collections.abc import Sequence
from enum import StrEnum
from typing import Any, Protocol

from etl.dominio.entidades import DadosDoParlamentar, Historico, IdentificadorExterno, Parlamentar


class FonteIncompleta(Exception):
    """A fonte respondeu, mas com menos do que o mínimo plausível: nada é gravado (FR-007b)."""


class RespostaInvalida(Exception):
    """JSON inválido, ou campo usado ausente ou de tipo inesperado: falha fechada."""


class StatusExecucao(StrEnum):
    EM_ANDAMENTO = "em_andamento"
    SUCESSO = "sucesso"
    COM_PENDENCIAS = "com_pendencias"
    FALHA = "falha"
    DISPENSADA = "dispensada"


class Gatilho(StrEnum):
    AGENDADA = "agendada"
    RESERVA = "reserva"
    MANUAL = "manual"


class FonteDaCasa(Protocol):
    def listar_em_exercicio(self) -> list[Parlamentar]: ...

    def historico(self, parlamentar: IdentificadorExterno) -> Historico: ...


class RepositorioDeDados(Protocol):
    def parlamentares_armazenados(self) -> list[IdentificadorExterno]: ...

    def gravar(self, todos: Sequence[DadosDoParlamentar]) -> dict[str, int]:
        """Grava tudo numa única transação e devolve as contagens (FR-012)."""
        ...


class ArmazemDeBrutos(Protocol):
    def guardar(self, execucao_id: int, url: str, conteudo: Any) -> bool: ...


class RegistroDeExecucoes(Protocol):
    def iniciar(self, gatilho: Gatilho, versao_codigo: str) -> int: ...

    def finalizar(
        self,
        execucao_id: int,
        status: StatusExecucao,
        *,
        contagens: dict[str, Any] | None = None,
        tentativas: list[Any] | None = None,
        erros: list[Any] | None = None,
        pendencias: list[Any] | None = None,
    ) -> None: ...


class Publicador(Protocol):
    def disparar(self, execucao_id: int) -> None: ...
